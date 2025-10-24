import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")