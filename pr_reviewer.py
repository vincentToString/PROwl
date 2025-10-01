import os, json, argparse
from pathlib import Path
import orjson
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Pydantic models
class PullRequestEvent(BaseModel):
    action: str
    pr_number: int
    pr_title: str
    pr_body: str
    pr_url: str
    pr_diff_url: str
    pr_author: str
    repo_name: str
    repo_url: str
    created_at: str


class Finding(BaseModel):
    severity: str
    title: str
    details: str
    file: str | None = None
    line: int | None = None


class ReviewResult(BaseModel):
    review_id: str = Field(default_factory=lambda: os.urandom(8).hex())
    repo_name: str
    pr_number: int
    pr_url: str
    summary: str
    findings: list[Finding]
    guideline_references: list[str] = Field(
        default_factory=lambda: [
            "Avoid secrets in code",
            "Add/adjust tests when behavior changes",
        ]
    )
    llm_meta: dict = Field(default_factory=dict)


# Helper functions
def load_prompt_template(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Prompt file not found: {path.resolve()}")


def fetch_diff(url: str, timeout_s: int, gh_token: str | None = None) -> str:
    headers = {"Accept": "text/plain"}

    # needed if the repo is private
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


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


def render_prompt(
    prompt_template: str,
    event: PullRequestEvent,
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


def call_openrouter(
    prompt_text: str, model: str, base_url: str, api_key: str, timeout_s: int
) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://pr-demo.local",
        "X-Title": "AI PR Reviewer Demo",
    }

    body = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are a precise code review assistant. Return ONLY JSON.",
            },
            {"role": "user", "content": prompt_text},
        ],
    }

    with httpx.Client(timeout=timeout_s, base_url=base_url) as client:
        response = client.post("/chat/completions", headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


# Core function, use this function to integrate with RabbitMQ
def process_event(
    event_dict: dict,
    *,
    prompt_path: Path,
    model: str,
    base_url: str,
    api_key: str,
    http_diff_timeout: int,
    llm_timeout: int,
    max_files: int,
    max_lines: int,
    gh_token: str | None = None,
) -> ReviewResult:
    event = PullRequestEvent.model_validate(event_dict)
    diff_text = fetch_diff(event.pr_diff_url, http_diff_timeout, gh_token=gh_token)
    files, snippets = parse_diff(
        diff_text, max_files=max_files, max_lines_per_file=max_lines
    )
    prompt_template = load_prompt_template(prompt_path)
    prompt = render_prompt(prompt_template, event, files, snippets)
    llm_response = call_openrouter(
        prompt,
        model=model,
        base_url=base_url,
        api_key=api_key,
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
        llm_meta={"provider": "openrouter", "model": model},
    )


# CLI entry, for testing purpose
def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "pr_json", help="Path to sample PR JSON (e.g., sample_data/sample_pr.json)"
    )
    ap.add_argument("--out", default="review_result.json", help="Output file path")
    args = ap.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    base_url = os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
    model = os.getenv("MODEL", "deepseek/deepseek-chat-v3.1:free")
    http_diff_timeout = int(os.getenv("HTTP_DIFF_TIMEOUT", "10"))
    llm_timeout = int(os.getenv("LLM_TIMEOUT", "20"))
    max_files = int(os.getenv("MAX_FILES_FOR_SNIPPETS", "3"))
    max_lines = int(os.getenv("MAX_LINES_PER_FILE", "120"))
    gh_token = os.getenv("GITHUB_TOKEN")  # optional for private repos only

    if not api_key:
        raise SystemExit("Missing OPENROUTER_API_KEY in environment/.env")

    event_dict = orjson.loads(Path(args.pr_json).read_bytes())
    result = process_event(
        event_dict,
        prompt_path=Path("prompt.md"),
        model=model,
        base_url=base_url,
        api_key=api_key,
        http_diff_timeout=http_diff_timeout,
        llm_timeout=llm_timeout,
        max_files=max_files,
        max_lines=max_lines,
        gh_token=gh_token,
    )

    Path(args.out).write_bytes(
        orjson.dumps(result.model_dump(), option=orjson.OPT_INDENT_2)
    )
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
