from pydantic import BaseModel
from typing import Dict, Any

class PullRequestData(BaseModel):
    action: str
    pr_number: int
    pr_title: str
    pr_body: str | None
    pr_url: str
    pr_diff_url: str
    pr_author: str
    repo_name: str
    repo_url: str
    created_at: str
    pr_diff_content: str | None = None