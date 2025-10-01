# PROwl – (AI PR Reviewer · Demo)

AI pull request reviews demo

## Features

- Loads a sample Pull Request payload
- Fetches the PR .diff from GitHub
- Condenses the changes into a prompt
- Sends it to an LLM
- Returns a normalized/structured review

## Prerequisites

- Python 3.10+
- An OpenRouter API key (free models available)

## Setup

1. **Setup virtual environment and dependencies:**

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

2. **Create a `.env` file:**

```bash
OPENROUTER_API_KEY=<"your-openrouter-api-key">
OPENROUTER_BASE=https://openrouter.ai/api/v1
MODEL=deepseek/deepseek-chat-v3.1:free
HTTP_DIFF_TIMEOUT=10
LLM_TIMEOUT=20
MAX_FILES_FOR_SNIPPETS=3
MAX_LINES_PER_FILE=120
```
