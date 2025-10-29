from fastapi import APIRouter, HTTPException, Header, Request
from aio_pika import Message, DeliveryMode
from typing import Optional
import json
import hmac
import hashlib
import logging
import uuid
from .redis_client import RedisClient
from .config import Config
from .models import PullRequestData
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()
    
redis_client = RedisClient(Config.REDIS_URL)


@router.post("/webhook/github")
async def handle_github_webhook(
    request:Request,
    x_hub_signature_256: Optional[str]=Header(None),
    x_github_event:str = Header(...)
):
    if x_github_event != "pull_request":
        return {"message": f"Event{x_github_event} ignored"}
    
    payload_body = await request.body()

    if Config.GITHUB_WEBHOOK_SECRET:
        if not verify_signature(payload_body, x_hub_signature_256, Config.GITHUB_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid signature")
        

    webhook_data = await request.json()

    if webhook_data.get("action") not in ["opened", "synchronize"]:
        return {"message": f"PR action '{webhook_data.get('action')}' ignored"}

    repo_name = webhook_data["repository"]["full_name"]
    pr_number = webhook_data["number"]
    diff_content = await fetch_pr_diff(repo_name, pr_number)

    if not diff_content:
        logger.warning(f"Proceed without diff for PR #{webhook_data['number']}")
        diff_content = "Diff file unable to retrieve"
        return {"status": "error", "message": "Failed to fetch diff"}
    
    diff_id =  str(uuid.uuid4())

    success = await redis_client.store_diff(diff_id, diff_content)
    if not success:
        logger.error(f"Failed to store diff in Redis for {repo_name}#{pr_number}")
        return {"status": "error", "message": "Failed to store diff"}

    pr_data = PullRequestData(
        action=webhook_data["action"],
        pr_number=webhook_data["number"],
        pr_title=webhook_data["pull_request"]["title"],
        pr_body=webhook_data["pull_request"].get("body"),
        pr_url=webhook_data["pull_request"]["html_url"],
        pr_diff_url=webhook_data["pull_request"]["diff_url"],
        pr_author=webhook_data["pull_request"]["user"]["login"],
        repo_name=webhook_data["repository"]["full_name"],
        repo_url=webhook_data["repository"]["html_url"],
        created_at=webhook_data["pull_request"]["created_at"],
        diff_id = diff_id
    )
    channel = await request.app.state.rabbitmq_connection.channel()

    try:
        ai_exchange = await channel.get_exchange("ai_service")
        msg = Message(
            body=json.dumps(pr_data.model_dump()).encode("utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT,
            headers={
                "repo": pr_data.repo_name,
                "pr_number": str(pr_data.pr_number)
            }
        )
        await ai_exchange.publish(msg, routing_key="pr")
        logger.info(f"Published PR#{pr_data.pr_number} to AI Service")
    except Exception as e:
        logger.error(f"Failed to publish to RabbitMQ: {e}")
        raise HTTPException(status_code=503, detail="Queue Unavailable")
    finally:
        await redis_client.close()
        await channel.close()

    return {
        "status": "accepted",
        "pr_number": pr_data.pr_number,
        "action": "queued_for_processing"
    }

async def fetch_pr_diff(repo: str, pr_number: int, timeout: int = 30) -> str | None:
    """fetch actual diff content"""
    api_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    token = await Config.github_app_auth.get_installation_token()
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"token {token}",
        "User-Agent": "PR-Owl-Bot"
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(api_url, headers=headers) as response:
                response.raise_for_status()
                diff = await response.text()

                # MVP: 500kb limit
                if len(diff) > 500_000:
                    logger.warning(f"Diff too large ({len(diff)} bytes), truncating")
                    return diff[:500_000] + "\n... [truncated]"
                return diff

    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP error fetching diff: {e.status} - {e.message}")
        return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching diff after {timeout}s")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching diff: {e}")
        return None
    
# helper funtions
def verify_signature(payload_body: bytes, signature: str | None, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature or not secret:
        return False
    
    hash_object = hmac.new(
        secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature)
