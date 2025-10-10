"""Pydantic models for GitHub activity."""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class GitHubComment(BaseModel):
    """GitHub comment data."""
    author: Optional[Dict[str, str]] = None
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    url: str
    body: Optional[str] = None

    class Config:
        populate_by_name = True


class GitHubIssue(BaseModel):
    """GitHub issue data."""
    number: int
    title: str
    url: str
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    state: str
    body: Optional[str] = None
    repository: Dict[str, str]
    author: Optional[Dict[str, str]] = None
    comments: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class GitHubPullRequest(BaseModel):
    """GitHub pull request data."""
    number: int
    title: str
    url: str
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    merged_at: Optional[str] = Field(None, alias="mergedAt")
    closed_at: Optional[str] = Field(None, alias="closedAt")
    state: str
    body: Optional[str] = None
    repository: Dict[str, str]
    author: Optional[Dict[str, str]] = None
    comments: Dict[str, Any] = Field(default_factory=dict)
    reviews: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class DeveloperActivity(BaseModel):
    """Aggregated GitHub activity for a developer."""
    username: str
    issues_created: List[GitHubIssue] = Field(default_factory=list)
    issues_commented: List[Dict] = Field(default_factory=list)
    prs_created: List[GitHubPullRequest] = Field(default_factory=list)
    prs_reviewed: List[Dict] = Field(default_factory=list)
    prs_commented: List[Dict] = Field(default_factory=list)
    repos: List[str] = Field(default_factory=list)
    by_repo: Dict[str, Dict] = Field(default_factory=dict)
    total_comments: int = 0
    total_issues: int = 0
    total_prs: int = 0
    total_reviews: int = 0


class ReportMetadata(BaseModel):
    """Metadata for EAR report."""
    report_date: str
    since_date: str
    end_date: str
    period_label: str
    organizations: List[str]
    refresh_rate_ms: Optional[int] = None
    include_github: bool = True
    include_odoo: bool = False
