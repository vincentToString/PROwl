import os
from dotenv import load_dotenv
from .auth import GitHubAppAuth

load_dotenv()

class Config:
    RABBITMQ_URL = os.getenv('RABBITMQ_URL')

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    DIFF_TTL = int(os.getenv("DIFF_TTL", "3600"))

    GITHUB_APP_ID = os.getenv('GITHUB_APP_ID')
    GITHUB_PRIVATE_KEY_PATH = os.getenv('GITHUB_PRIVATE_KEY_PATH', './github-app-private-key.pem')
    GITHUB_INSTALLATION_ID = os.getenv('GITHUB_INSTALLATION_ID')
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

    # Initialize GitHub App Auth
    if not GITHUB_APP_ID or not GITHUB_INSTALLATION_ID:
        raise ValueError("GITHUB_APP_ID and GITHUB_INSTALLATION_ID must be set")

    github_app_auth = GitHubAppAuth(
        app_id=GITHUB_APP_ID,
        private_key_path=GITHUB_PRIVATE_KEY_PATH or './github-app-private-key.pem',
        installation_id=GITHUB_INSTALLATION_ID
    )