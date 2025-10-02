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

from fastapi import FastAPI
from contextlib import asynccontextmanager
from aio_pika import connect_robust, ExchangeType
import logging
from intake.config import Config
from intake.webhooks import router as webhook_router


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

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connection to RabbitMQ")
    app.state.rabbitmq_connection = await connect_robust(Config.RABBITMQ_URL)

    setup_channel = await app.state.rabbitmq_connection.channel()

    try:
        # AI service Exchanges
        ai_exchange = await setup_channel.declare_exchange(
            "ai_service", ExchangeType.DIRECT, durable=True
        )
        ai_queue = await setup_channel.declare_queue("pr_review", durable=True)
        await ai_queue.bind(ai_exchange, routing_key="pr")

        # Oursource exchanges
        out_exchange = await setup_channel.declare_exchange(
            "out_exchange", ExchangeType.FANOUT, durable=True
        )

        # maintain this slack queue seperately so we can pause notification during off office time
        slack_queue = await setup_channel.declare_queue("slack_msgs", durable=True)
        await slack_queue.bind(out_exchange)

        github_queue = await setup_channel.declare_queue("github_comments", durable=True)
        await github_queue.bind(out_exchange)
    finally: 
        await setup_channel.close()

    yield

    logger.info("Closing RabbitMQ connection")
    await app.state.rabbitmq_connection.close()
    

app = FastAPI(lifespan=lifespan)

@app.get("/")
def ping():
    return {"message": "hello world"}

@app.get("/health")
def health():
    return {"status": "healthy"}

app.include_router(webhook_router)
