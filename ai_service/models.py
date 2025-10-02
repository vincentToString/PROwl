from pydantic import BaseModel, Field
import os
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