import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE = os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
    MODEL = os.getenv("MODEL", "deepseek/deepseek-chat-v3.1:free")
    AWS_BEARER_TOKEN_BEDROCK = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
    KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    MODEL_ID = os.getenv("MODEL_ID", "meta.llama4-scout-17b-instruct-v1:0")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20") or "20")
    MAX_FILES = int(os.getenv("MAX_FILES_FOR_SNIPPETS", "3") or "3")
    MAX_LINES = int(os.getenv("MAX_LINES_PER_FILE", "120") or "120")
