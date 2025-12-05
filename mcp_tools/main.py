from fastapi import FastAPI
from fastmcp import FastMCP

from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from pathlib import Path
import os

from .tool_generator import (
    register_templates_from_directory,
    register_templates_from_source,
)
from .template_loader import is_url, is_github_repo_format

TITLE = os.getenv("MCP_TITLE", "Python MCP Template")
DESCRIPTION = os.getenv(
    "MCP_DESCRIPTION", "A template for creating MCP-compliant FastAPI"
)

# Templates source - can be configured via environment variable
# Supports:
#   - Local directory: /path/to/templates/ or .github/ISSUE_TEMPLATE
#   - Local file: /path/to/template.md
#   - URL: https://example.com/template.md
#   - GitHub repo: owner/repo (loads from .github/ISSUE_TEMPLATE/)
#   - GitHub repo with path: owner/repo:.github/ISSUE_TEMPLATE/bug.md
TEMPLATES_SOURCE = os.getenv("MCP_TEMPLATES_SOURCE", ".github/ISSUE_TEMPLATE")

app = FastAPI(
    title=TITLE,
    description=DESCRIPTION,
)


# Register templates from the configured source
# This must happen BEFORE creating the MCP server
def load_templates_from_source(source: str):
    """Load templates based on source type."""
    # Check if it's a URL or GitHub format
    if is_url(source) or is_github_repo_format(source) or ":" in source:
        register_templates_from_source(app, source)
    else:
        # Local path
        path = Path(source)
        if path.exists():
            if path.is_dir():
                register_templates_from_directory(app, path)
            else:
                register_templates_from_source(app, source)
        else:
            print(f"Templates source not found: {source}")


# Support multiple sources separated by comma
sources = [s.strip() for s in TEMPLATES_SOURCE.split(",") if s.strip()]
for source in sources:
    print(f"Loading templates from: {source}")
    try:
        load_templates_from_source(source)
    except Exception as e:
        print(f"Failed to load from {source}: {e}")

# Create MCP server from FastAPI app (includes all registered endpoints as tools)
mcp = FastMCP.from_fastapi(app=app, stateless_http=True, json_response=True)

starlette_app = mcp.http_app(
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
)

starlette_app.mount("/api", app=app)  # (Optional) Keep the original FastAPI app at /api
