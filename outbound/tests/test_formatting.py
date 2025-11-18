import os
from pathlib import Path
import importlib


def import_outbound_worker():
    """
    Helper to safely import outbound worker.

    It sets required env vars and a dummy private key file so that
    the module-level initialization doesn't crash, but we never
    actually call GitHub APIs in these tests.
    """
    os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    os.environ.setdefault("GITHUB_APP_ID", "12345")
    os.environ.setdefault("GITHUB_INSTALLATION_ID", "67890")

    key_path = Path("github-app-private-key.pem")
    if not key_path.exists():
        key_path.write_text("dummy-key", encoding="utf-8")

    # Import **after** env + file are set
    return importlib.import_module("outbound.worker")


def test_format_finding_markdown_basic():
    worker = import_outbound_worker()
    finding = {
        "severity": "high",
        "title": "SQL injection risk",
        "details": "User input is concatenated directly into SQL.",
        "file": "app/db.py",
        "line": 42,
    }

    md = worker.format_finding_markdown(finding)

    assert "🟠 HIGH" in md  # emoji + uppercase severity
    assert "SQL injection risk" in md
    assert "User input is concatenated directly into SQL." in md
    assert "**Location:** `app/db.py` (Line 42)" in md


def test_format_finding_markdown_missing_optional_fields():
    worker = import_outbound_worker()
    finding = {
        "severity": "info",
        "title": "Minor style suggestion",
        "details": "Consider renaming variable for clarity.",
        # no file / line
    }

    md = worker.format_finding_markdown(finding)

    assert "ℹ️ INFO" in md
    assert "Minor style suggestion" in md
    # no Location section if file is missing
    assert "Location" not in md


def test_format_github_comment_with_findings():
    worker = import_outbound_worker()

    data = {
        "review_id": "rev-123",
        "summary": "Overall, the PR looks good but has a few security issues.",
        "findings": [
            {
                "severity": "critical",
                "title": "Hardcoded secret",
                "details": "Found an AWS secret key in config.py.",
                "file": "config.py",
                "line": 12,
            },
            {
                "severity": "low",
                "title": "Minor naming issue",
                "details": "Variable `x` could be renamed for clarity.",
                "file": "utils/helpers.py",
                "line": 88,
            },
        ],
        "guideline_references": [
            "Avoid hardcoded secrets",
            "Use descriptive variable names",
        ],
        "llm_meta": {
            "provider": "bedrock",
            "model": "meta.llama3",
            "region": "us-east-1",
        },
    }

    comment = worker.format_github_comment(data)

    # Header & summary
    assert "# 🦉 PROwl Code Review" in comment
    assert "Review ID:` rev-123`" not in comment  # just sanity check spacing
    assert "`rev-123`" in comment
    assert "## 📋 Summary" in comment
    assert "Overall, the PR looks good but has a few security issues." in comment

    # Findings
    assert "## 🔍 Findings" in comment
    assert "🔴 CRITICAL" in comment
    assert "Hardcoded secret" in comment
    assert "config.py" in comment
    assert "Line 12" in comment
    assert "🔵 LOW" in comment or "low".upper() in comment

    # Guidelines
    assert "## 📚 Guideline References" in comment
    assert "- Avoid hardcoded secrets" in comment

    # Metadata footer
    assert "🤖 Review Metadata" in comment
    assert '"provider": "bedrock"' in comment
    assert "Automated review powered by PROwl" in comment


def test_format_github_comment_no_findings():
    worker = import_outbound_worker()

    data = {
        "review_id": "rev-999",
        "summary": "No issues found.",
        "findings": [],
        "guideline_references": [],
    }

    comment = worker.format_github_comment(data)

    assert "## ✅ No Issues Found" in comment
    assert "No significant issues were detected in this PR." in comment
    assert "🔍 Findings" not in comment or "## 🔍 Findings" not in comment
