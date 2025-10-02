import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE = os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
    MODEL = os.getenv("MODEL", "deepseek/deepseek-chat-v3.1:free")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))
    MAX_FILES = int(os.getenv("MAX_FILES_FOR_SNIPPETS", "3"))
    MAX_LINES = int(os.getenv("MAX_LINES_PER_FILE", "120"))
