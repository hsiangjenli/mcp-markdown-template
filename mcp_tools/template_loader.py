"""
Load markdown templates from various sources:
- Local directory
- Local file path
- URL (including GitHub raw URLs)
- GitHub Issue Template (owner/repo format)
"""

import re
import httpx
from pathlib import Path
from typing import Iterator
from pydantic import BaseModel
from urllib.parse import urlparse


class TemplateSource(BaseModel):
    """Represents a loaded template source."""

    name: str  # Identifier for the template
    content: str  # Raw markdown content
    source_type: str  # "local_dir", "local_file", "url", "github"
    source_path: str  # Original path/URL


def is_url(path: str) -> bool:
    """Check if the path is a URL."""
    try:
        result = urlparse(path)
        return result.scheme in ("http", "https")
    except Exception:
        return False


def is_github_repo_format(path: str) -> bool:
    """Check if the path is in owner/repo format."""
    return bool(re.match(r"^[\w\-\.]+/[\w\-\.]+$", path))


def fetch_url_content(url: str) -> str:
    """Fetch content from a URL."""
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def get_github_raw_url(owner: str, repo: str, path: str, branch: str = "main") -> str:
    """Convert GitHub repo info to raw content URL."""
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def list_github_issue_templates(
    owner: str, repo: str, branch: str = "main"
) -> list[str]:
    """
    List all issue templates in a GitHub repository.
    Returns list of file paths.
    """
    api_url = (
        f"https://api.github.com/repos/{owner}/{repo}/contents/.github/ISSUE_TEMPLATE"
    )

    with httpx.Client(timeout=30) as client:
        response = client.get(api_url, params={"ref": branch})

        if response.status_code == 404:
            # Try without .github prefix (some repos use different structure)
            return []

        response.raise_for_status()
        files = response.json()

        # Filter for markdown files
        return [
            f["path"]
            for f in files
            if f["type"] == "file" and f["name"].endswith((".md", ".yaml", ".yml"))
        ]


def load_from_local_directory(
    dir_path: Path, pattern: str = "*.md"
) -> Iterator[TemplateSource]:
    """Load all templates from a local directory."""
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            yield TemplateSource(
                name=file_path.stem,
                content=file_path.read_text(encoding="utf-8"),
                source_type="local_dir",
                source_path=str(file_path),
            )


def load_from_local_file(file_path: Path) -> TemplateSource:
    """Load a single template from a local file."""
    return TemplateSource(
        name=file_path.stem,
        content=file_path.read_text(encoding="utf-8"),
        source_type="local_file",
        source_path=str(file_path),
    )


def load_from_url(url: str) -> TemplateSource:
    """Load a template from a URL."""
    content = fetch_url_content(url)

    # Extract name from URL
    parsed = urlparse(url)
    name = Path(parsed.path).stem or "template"

    return TemplateSource(
        name=name,
        content=content,
        source_type="url",
        source_path=url,
    )


def load_from_github_repo(
    owner: str,
    repo: str,
    branch: str = "main",
    template_path: str | None = None,
) -> Iterator[TemplateSource]:
    """
    Load templates from a GitHub repository.

    If template_path is provided, load only that file.
    Otherwise, load all templates from .github/ISSUE_TEMPLATE/
    """
    if template_path:
        # Load specific file
        url = get_github_raw_url(owner, repo, template_path, branch)
        content = fetch_url_content(url)
        name = Path(template_path).stem

        yield TemplateSource(
            name=name,
            content=content,
            source_type="github",
            source_path=f"{owner}/{repo}/{template_path}",
        )
    else:
        # List and load all templates
        template_paths = list_github_issue_templates(owner, repo, branch)

        for path in template_paths:
            if path.endswith(".md"):  # Only load markdown files
                url = get_github_raw_url(owner, repo, path, branch)
                try:
                    content = fetch_url_content(url)
                    name = Path(path).stem

                    yield TemplateSource(
                        name=name,
                        content=content,
                        source_type="github",
                        source_path=f"{owner}/{repo}/{path}",
                    )
                except Exception as e:
                    print(f"Failed to load {path}: {e}")


def load_templates(source: str, pattern: str = "*.md") -> Iterator[TemplateSource]:
    """
    Load templates from various sources.

    Supported formats:
    - Local directory: /path/to/templates/
    - Local file: /path/to/template.md
    - URL: https://example.com/template.md
    - GitHub raw URL: https://raw.githubusercontent.com/owner/repo/branch/path/template.md
    - GitHub repo: owner/repo (loads all templates from .github/ISSUE_TEMPLATE/)
    - GitHub repo with path: owner/repo:.github/ISSUE_TEMPLATE/bug.md

    Parameters
    ----------
    source : str
        The source path, URL, or GitHub repo identifier
    pattern : str
        Glob pattern for local directory (default: "*.md")

    Yields
    ------
    TemplateSource
        Loaded template sources
    """
    # Check if it's a URL
    if is_url(source):
        yield load_from_url(source)
        return

    # Check if it's a GitHub repo format (owner/repo or owner/repo:path)
    if ":" in source and is_github_repo_format(source.split(":")[0]):
        # owner/repo:path format
        repo_part, path = source.split(":", 1)
        owner, repo = repo_part.split("/")
        yield from load_from_github_repo(owner, repo, template_path=path)
        return

    if is_github_repo_format(source):
        # owner/repo format - load all templates
        owner, repo = source.split("/")
        yield from load_from_github_repo(owner, repo)
        return

    # Local path
    path = Path(source)

    if path.is_dir():
        yield from load_from_local_directory(path, pattern)
    elif path.is_file():
        yield load_from_local_file(path)
    else:
        raise ValueError(
            f"Invalid source: {source} (not a valid path, URL, or GitHub repo)"
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m mcp_tools.template_loader <source>")
        print("\nExamples:")
        print("  python -m mcp_tools.template_loader .github/ISSUE_TEMPLATE/")
        print("  python -m mcp_tools.template_loader /path/to/template.md")
        print("  python -m mcp_tools.template_loader https://example.com/template.md")
        print("  python -m mcp_tools.template_loader owner/repo")
        print(
            "  python -m mcp_tools.template_loader owner/repo:.github/ISSUE_TEMPLATE/bug.md"
        )
        sys.exit(1)

    source = sys.argv[1]
    print(f"Loading templates from: {source}\n")

    for template in load_templates(source):
        print(f"=== {template.name} ===")
        print(f"Source: {template.source_type} ({template.source_path})")
        print(f"Content preview: {template.content[:200]}...")
        print()
