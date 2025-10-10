import asyncio
from aio_pika.abc import AbstractIncomingMessage
import aio_pika
from aio_pika import Message, DeliveryMode
import os, json, argparse
from pathlib import Path
import orjson
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging
import signal
import boto3
import base64
from ai_service.models import PullRequestData, ReviewResult, Finding
from ai_service.config import Config



logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'     
  )
logger = logging.getLogger(__name__)

async def handle_message(message: AbstractIncomingMessage, channel):
    # async with message.process(requeue=False): # manual ack
    #     try:
    #         event_dict = json.loads(message.body.decode("utf-8"))

    #         result = process_event(
    #             event_dict,
    #             prompt_path=Path(__file__).parent / "prompt.md",
    #             model_id=Config.MODEL_ID,
    #             aws_access_key=Config.AWS_ACCESS_KEY,
    #             aws_secret_key=Config.AWS_SECRET_KEY,
    #             aws_region=Config.AWS_DEFAULT_REGION,
    #             llm_timeout=Config.LLM_TIMEOUT,
    #             max_files=Config.MAX_FILES,
    #             max_lines=Config.MAX_LINES,
    #         )
    #         out_exchange = await channel.get_exchange("out_exchange")
    #         msg=Message(
    #             body=orjson.dumps(result.model_dump()),
    #             delivery_mode=DeliveryMode.PERSISTENT,
    #             content_type="application/json", 
    #             headers={"repo": result.repo_name, "pr_number": result.pr_number},
    #         )
    #         await out_exchange.publish(msg, routing_key="")
    #         logger.info("Published review result for %s PR#%s", result.repo_name, result.pr_number)
    #     except Exception as e:
    #         logger.error("Error processing message: %s", e, exc_info=True)
    #         # MVP: nack it (later customizable)
    #         await message.nack(requeue=False)
    
    async with message.process(requeue=False): # manual ack
        event_dict = json.loads(message.body.decode("utf-8"))

        result = process_event(
            event_dict,
            prompt_path=Path(__file__).parent / "prompt.md",
            model_id=Config.MODEL_ID,
            aws_access_key=Config.AWS_ACCESS_KEY,
            aws_secret_key=Config.AWS_SECRET_KEY,
            aws_region=Config.AWS_DEFAULT_REGION,
            llm_timeout=Config.LLM_TIMEOUT,
            max_files=Config.MAX_FILES,
            max_lines=Config.MAX_LINES,
        )
        out_exchange = await channel.get_exchange("out_exchange")
        msg=Message(
            body=orjson.dumps(result.model_dump()),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json", 
            headers={"repo": result.repo_name, "pr_number": result.pr_number},
        )
        await out_exchange.publish(msg, routing_key="")
        logger.info("Published review result for %s PR#%s", result.repo_name, result.pr_number)



            
def process_event(
    event_dict: dict,
    *,
    prompt_path: Path,
    model_id: str,
    aws_access_key: str,
    aws_secret_key: str,
    aws_region: str,
    llm_timeout: int,
    max_files: int,
    max_lines: int,
) -> ReviewResult:
    event = PullRequestData.model_validate(event_dict)
    if not event.pr_diff_content:
        logger.error(f"Receiving PR #{event.pr_number}has no diff content available")
        raise Exception(f"Invalid PR to review: #{event.pr_number}")
    files, snippets = parse_diff(
        event.pr_diff_content, max_files=max_files, max_lines_per_file=max_lines
    )

    prompt_template = load_prompt_template(prompt_path)
    prompt = render_prompt(prompt_template, event, files, snippets)
    llm_response = call_bedrock(
        prompt,
        model_id=model_id,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        aws_region=aws_region,
        timeout_s=llm_timeout,
    )

    findings = [
        Finding.model_validate(finding)
        for finding in (llm_response.get("findings") or [])
    ]

    return ReviewResult(
        repo_name=event.repo_name,
        pr_number=event.pr_number,
        pr_url=event.pr_url,
        summary=(llm_response.get("summary") or "").strip(),
        findings=findings,
        guideline_references=[
            "Avoid secrets in code",
            "Add/adjust tests when behavior changes",
        ],
        llm_meta={"provider": "aws_bedrock", "model": model_id},
    )

# Helper:
def parse_diff(diff_text: str, max_files: int, max_lines_per_file: int):
    files, snippets = [], []
    current_file, additions, deletions = None, 0, 0
    added_lines: list[str] = []
    removed_lines: list[str] = []

    NOISY_ENDSWITH = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", ".min.js")

    def flush():
        nonlocal current_file, additions, deletions, added_lines, removed_lines
        if current_file is not None:
            files.append(
                {
                    "filename": current_file,
                    "additions": additions,
                    "deletions": deletions,
                }
            )

            if not current_file.endswith(NOISY_ENDSWITH):
                snippet = {
                    "filename": current_file,
                    "added_text": (
                        "\n".join(added_lines[:max_lines_per_file])
                        if added_lines
                        else ""
                    ),
                    "removed_text": (
                        "\n".join(removed_lines[:max_lines_per_file])
                        if removed_lines
                        else ""
                    ),
                }
                if snippet["added_text"] or snippet["removed_text"]:
                    snippets.append(snippet)

        current_file, additions, deletions = None, 0, 0
        added_lines, removed_lines = [], []

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current_file is not None:
                flush()
            current_file = None

        elif line.startswith("+++ b/"):
            current_file = line[len("+++ b/") :].strip()

        elif line.startswith("--- a/"):
            pass

        else:
            if current_file is None:
                continue

            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
                added_lines.append(line[1:])

            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
                removed_lines.append(line[1:])

    if current_file is not None:
        flush()

    files.sort(key=lambda file_info: file_info["additions"], reverse=True)
    top_files = files[:max_files]
    top_paths = {file_info["filename"] for file_info in top_files}
    top_snippets = [
        snippet for snippet in snippets if snippet["filename"] in top_paths
    ][:max_files]
    return top_files, top_snippets

def load_prompt_template(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Prompt file not found: {path.resolve()}")

def render_prompt(
    prompt_template: str,
    event: PullRequestData,
    files: list[dict],
    snippets: list[dict],
) -> str:
    return (
        prompt_template.replace("{{repo_name}}", event.repo_name)
        .replace("{{pr_number}}", str(event.pr_number))
        .replace("{{pr_title}}", event.pr_title)
        .replace("{{pr_author}}", event.pr_author)
        .replace("{{pr_body}}", (event.pr_body or "")[:1000])
        .replace("{{files_table}}", build_files_table(files))
        .replace("{{snippets}}", build_snippets_block(snippets))
    )

def call_bedrock(
    prompt_text: str, model_id: str, aws_access_key: str, aws_secret_key: str, aws_region: str, timeout_s: int
) -> dict:
    # Create Bedrock client with explicit credentials
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name=aws_region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )

    # For Llama models, use the converse API format
    conversation = [
        {
            "role": "user",
            "content": [{"text": f"You are a precise code review assistant. Return ONLY JSON.\n\n{prompt_text}"}]
        }
    ]

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={
                "maxTokens": 4000,
                "temperature": 0.2,
                "topP": 0.9
            }
        )
        
        # Extract response text
        response_text = response["output"]["message"]["content"][0]["text"]
        
        # Try to parse as JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, wrap in a basic structure
            logger.warning(f"Non-JSON response from Bedrock: {response_text}")
            return {
                "summary": response_text,
                "findings": []
            }
        
    except Exception as e:
        logger.error(f"Error calling Bedrock: {e}")
        raise

def build_files_table(files: list[dict]) -> str:
    return (
        "\n".join(
            f'{file_info["filename"]} +{file_info["additions"]}/-{file_info["deletions"]}'
            for file_info in files
        )
        or "(no files parsed)"
    )

def build_snippets_block(snippets: list[dict]) -> str:
    if not snippets:
        return "(no change snippets)"

    blocks = []
    for snippet in snippets:
        parts = [f"--- file: {snippet['filename']}"]

        added_text = snippet.get("added_text") or ""
        removed_text = snippet.get("removed_text") or ""

        if added_text:
            parts.append("\n".join("+" + line for line in added_text.splitlines()))
        if removed_text:
            parts.append("\n".join("-" + line for line in removed_text.splitlines()))

        blocks.append("\n".join(parts))

    return "\n".join(blocks)

async def main():
    conn = await aio_pika.connect_robust(Config.RABBITMQ_URL)
    channel = await conn.channel()

    await channel.set_qos(prefetch_count=1)

    pr_queue = await channel.declare_queue("pr_review", durable=True)

    stop_event = asyncio.Event()

    async def consumer(msg: AbstractIncomingMessage):
        await handle_message(msg, channel)

    await pr_queue.consume(consumer)
    logger.info("AI service consuming from pr_review queue")

    def _stop(*_):
        logger.info("Shut down")
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
