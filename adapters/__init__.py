"""Adapters for external services."""
from .github_adapter import GitHubAdapter
from .notion_adapter import NotionAdapter

__all__ = ["GitHubAdapter", "NotionAdapter"]
