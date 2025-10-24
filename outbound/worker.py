import asyncio
import json
import logging
import os
import signal
import time
from datetime import datetime, timedelta

from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
import aiohttp
import jwt
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("outbound-worker")

RABBITMQ_URL = os.getenv('RABBITMQ_URL')
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH", "./github-app-private-key.pem")
GITHUB_INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")


# ----------------------
# GitHub App Authentication
# ----------------------

class GitHubAppAuth:
    def __init__(self, app_id: str, private_key_path: str, installation_id: str):
        self.app_id = app_id
        self.installation_id = installation_id
        
        # Read private key
        with open(private_key_path, 'r') as f:
            self.private_key = f.read()
        
        self._token = None
        self._token_expires_at = None
    
    def _generate_jwt(self) -> str:
        """Generate JWT to authenticate as the GitHub App"""
        payload = {
            'iat': int(time.time()),
            'exp': int(time.time()) + 600,  # JWT expires in 10 minutes
            'iss': self.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
    async def get_installation_token(self) -> str:
        """Get installation access token (cached)"""
        # Return cached token if still valid
        if self._token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._token
        
        # Generate new token
        jwt_token = self._generate_jwt()
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PR-Owl-Bot'
        }
        
        url = f'https://api.github.com/app/installations/{self.installation_id}/access_tokens'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                
                self._token = data['token']
                # Tokens expire in 1 hour, refresh 5 min early
                self._token_expires_at = datetime.now() + timedelta(minutes=55)
                
                log.info("GitHub App installation token refreshed")
                return self._token
if not GITHUB_APP_ID or not GITHUB_INSTALLATION_ID:
    raise ValueError("GITHUB_APP_ID and GITHUB_INSTALLATION_ID must be set")

# Initialize GitHub App Auth
github_auth = GitHubAppAuth(
    app_id=GITHUB_APP_ID,
    private_key_path=GITHUB_PRIVATE_KEY_PATH,
    installation_id=GITHUB_INSTALLATION_ID
)


# ----------------------
# Message Handlers
# ----------------------

async def handle_github(msg: AbstractIncomingMessage):
    """Handle PR review result and post to GitHub as a comment."""
    async with msg.process(ignore_processed=True):  # auto-ack on success
        try:
            data = json.loads(msg.body.decode("utf-8"))
            repo = data["repo_name"]
            pr = data["pr_number"]

            # Prefer review_text, fallback to summary
            review_body = data.get("review_text") or data.get("summary") or "[no review text]"

            log.info(f"Posting review to GitHub PR#{pr} in {repo}:\n{review_body[:200]}...")

            # Get fresh installation token
            token = await github_auth.get_installation_token()

            url = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "PR-Owl-Bot"
            }

            async with aiohttp.ClientSession() as session:
                resp = await session.post(url, headers=headers, json={"body": review_body})
                if resp.status != 201:
                    text = await resp.text()
                    log.error(f"GitHub API error {resp.status}: {text}")

        except Exception as e:
            log.error("Failed to handle GitHub message: %s", e, exc_info=True)
            await msg.nack(requeue=False)  # DLQ should capture


# async def handle_slack(msg: AbstractIncomingMessage):
#     """Handle PR review result and post to Slack channel."""
#     async with msg.process(ignore_processed=True):
#         try:
#             data = json.loads(msg.body.decode("utf-8"))
#             repo = data["repo_name"]
#             pr = data["pr_number"]
#             review_summary = data.get("summary", "[no summary]")

#             log.info(f"Sending Slack notification for PR#{pr} in {repo}: {review_summary}")

#             url = "https://slack.com/api/chat.postMessage"
#             headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
#             payload = {"channel": "#code-reviews", "text": review_summary}

#             async with aiohttp.ClientSession() as session:
#                 resp = await session.post(url, headers=headers, json=payload)
#                 if resp.status != 200:
#                     text = await resp.text()
#                     log.error(f"Slack API error {resp.status}: {text}")

#         except Exception as e:
#             log.error("Failed to handle Slack message: %s", e, exc_info=True)
#             await msg.nack(requeue=False)


# ----------------------
# Worker Main Loop
# ----------------------

async def main():
    conn = await connect_robust(RABBITMQ_URL)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=5)

    github_q = await ch.declare_queue("github_comments", durable=True)
    slack_q = await ch.declare_queue("slack_msgs", durable=True)

    await github_q.consume(handle_github)
    # await slack_q.consume(handle_slack)

    log.info("Outbound worker consuming from github_comments and slack_msgs queues...")

    stop_event = asyncio.Event()

    def _stop(*_):
        log.info("Shutdown signal received.")
        stop_event.set()

    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(s, _stop)
        except NotImplementedError:
            pass

    await stop_event.wait()
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
