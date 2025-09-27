from fastapi import FastAPI, HTTPException, Header, Request
from contextlib import asynccontextmanager
from aio_pika import connect_robust, Message, DeliveryMode, ExchangeType
from pydantic import BaseModel
from typing import Optional
import json
import hmac
import hashlib
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class PullRequestModel(BaseModel):
    action: str
    number: int
    pull_request: dict
    repository: dict

logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'     
  )
logger = logging.getLogger(__name__)

# Connections Pool
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     app.state.rabbitmq_connection = await connect_robust(
#         os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
#     )

#     app.state.channel = await app.state.rabbitmq_connection.channel()

#     await app.state.channel.declare_queue("github_pr_events", durable=True)

#     yield

#     await app.state.channel.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rabbitmq_connection = await connect_robust(
        os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    )

    app.state.channel = await app.state.rabbitmq_connection.channel()

    # Declare exchange and queue, then bind
    app.state.exchange = await app.state.channel.declare_exchange(
        "github_events", ExchangeType.DIRECT, durable=True
    )
    queue = await app.state.channel.declare_queue("github_pr_events", durable=True)
    await queue.bind(app.state.exchange, routing_key="github_prs")

    yield

    await app.state.channel.close()


app = FastAPI(lifespan=lifespan)

@app.get("/")
def ping():
    return {"message": "hello world"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/intake/ci")
@app.post("/intake/webhook")
async def handle_intake_webhook(    
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: str = Header(...),
    #Note: might need x_github_delivery id for dedupe
):
    if x_github_event != "pull_request":
        return {"message": "Not a pull request. Ignoring"}

    payload_body = await request.body();

    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if webhook_secret:
            if not verify_signature(payload_body, x_hub_signature_256, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid Signature")
    
    webhook_data = await request.json()

    if webhook_data.get("action") != "opened":
        return {"message": f"PR action '{webhook_data.get('action')}' ignored"}
        
        # Extract relevant data
    pr_data = {
        "action": webhook_data["action"],
        "pr_number": webhook_data["number"],
        "pr_title": webhook_data["pull_request"]["title"],
        "pr_body": webhook_data["pull_request"]["body"],
        "pr_url": webhook_data["pull_request"]["html_url"],
        "pr_diff_url": webhook_data["pull_request"]["diff_url"],
        "pr_author": webhook_data["pull_request"]["user"]["login"],
        "repo_name": webhook_data["repository"]["full_name"],
        "repo_url": webhook_data["repository"]["html_url"],
        "created_at": webhook_data["pull_request"]["created_at"],
    }

    try:
        msg = Message(
            body=json.dumps(pr_data).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            headers={
                "repo": webhook_data["repository"]["full_name"],
                "pr_number": str(webhook_data["number"])
            }
        )
        await app.state.exchange.publish(msg, routing_key="github_prs")
    except Exception as e:
        logger.error("Failed to publish to RabbitMQ", exc_info=e)
        raise HTTPException(status_code=503, detail="Queue Unavailable, please retry")
    
    return {
        "status": "accepted",
        "pr_number": webhook_data["number"],
        "action": "queued_for_processing"
    }


# consumer 


# webhook support functions below
def verify_signature(payload_body: bytes, signature: str | None, secret: str) -> bool:
    """Verify the payload was sent from Github"""
    if not signature:
        return False
    
    hash_object = hmac.new(
        secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )

    expected_signature= "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature)


