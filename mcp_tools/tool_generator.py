"""
Dynamically generate MCP tools from markdown templates.
"""

import re
from pathlib import Path
from pydantic import Field, create_model
from fastapi import FastAPI

from .template_parser import parse_template, render_template
from .template_loader import TemplateSource, load_templates


def create_tool_from_template(
    app: FastAPI,
    template_path: Path | str,
    tool_name: str | None = None,
    remove_comments: bool = True,
):
    """
    Create a FastAPI endpoint from a markdown template file.

    Parameters
    ----------
    app : FastAPI
        The FastAPI app to register the endpoint with
    template_path : Path | str
        Path to the markdown template
    tool_name : str | None
        Custom tool name (defaults to template name)
    remove_comments : bool
        Whether to remove HTML comments from rendered output

    Returns
    -------
    The registered endpoint function
    """
    template_path = Path(template_path)
    parsed = parse_template(template_path)

    return _create_tool_internal(
        app=app,
        parsed=parsed,
        template_content=parsed.raw_content,
        source_identifier=str(template_path),
        tool_name=tool_name,
        remove_comments=remove_comments,
    )


def create_tool_from_source(
    app: FastAPI,
    source: TemplateSource,
    tool_name: str | None = None,
    remove_comments: bool = True,
):
    """
    Create a FastAPI endpoint from a TemplateSource.

    Parameters
    ----------
    app : FastAPI
        The FastAPI app to register the endpoint with
    source : TemplateSource
        The loaded template source
    tool_name : str | None
        Custom tool name (defaults to template name)
    remove_comments : bool
        Whether to remove HTML comments from rendered output

    Returns
    -------
    The registered endpoint function
    """
    parsed = parse_template(source.name, content=source.content)

    return _create_tool_internal(
        app=app,
        parsed=parsed,
        template_content=source.content,
        source_identifier=source.source_path,
        tool_name=tool_name,
        remove_comments=remove_comments,
    )


def _create_tool_internal(
    app: FastAPI,
    parsed,
    template_content: str,
    source_identifier: str,
    tool_name: str | None = None,
    remove_comments: bool = True,
):
    """Internal function to create a tool from parsed template."""

    # Generate tool name from template name if not provided
    if tool_name is None:
        name = parsed.name or "template"
        name = re.sub(r"[^\w\s]", "", name).strip().lower().replace(" ", "_")
        tool_name = f"create_{name}" if name else "create_template"

    # Build parameter info for the dynamic function
    param_info = []
    for var in parsed.variables:
        description = var.description
        if var.example:
            description += f"\n\nExample:\n{var.example}"
        param_info.append((var.name, description))

    # Create a Pydantic model for the input
    field_definitions = {}
    for name, desc in param_info:
        field_definitions[name] = (str, Field(description=desc))

    InputModel = create_model(
        f"{tool_name.title().replace('_', '')}Input", **field_definitions
    )

    # Store in closure
    _template_content = template_content
    _remove_comments = remove_comments
    _description = parsed.about or f"Create content from {parsed.name} template"

    # Create the endpoint function
    async def endpoint_func(input_data: InputModel) -> str:
        """Render the template with provided values."""
        return render_template(
            template_source=source_identifier,
            variables=input_data.model_dump(),
            remove_comments=_remove_comments,
            content=_template_content,
        )

    # Update function metadata
    endpoint_func.__name__ = tool_name
    endpoint_func.__doc__ = _description

    # Register with FastAPI as POST endpoint
    app.post(
        f"/{tool_name}",
        name=tool_name,
        description=_description,
        summary=parsed.name or tool_name,
        tags=["Template Tools"],
    )(endpoint_func)

    return endpoint_func


def register_templates_from_directory(
    app: FastAPI,
    templates_dir: Path | str,
    pattern: str = "*.md",
    remove_comments: bool = True,
):
    """
    Register all templates from a local directory as FastAPI endpoints.

    Parameters
    ----------
    app : FastAPI
        The FastAPI app
    templates_dir : Path | str
        Directory containing templates
    pattern : str
        Glob pattern for template files
    remove_comments : bool
        Whether to remove HTML comments

    Returns
    -------
    list
        List of registered endpoint functions
    """
    templates_dir = Path(templates_dir)
    tools = []

    for template_path in templates_dir.glob(pattern):
        try:
            tool = create_tool_from_template(
                app, template_path, remove_comments=remove_comments
            )
            tools.append(tool)
            print(f"Registered endpoint from: {template_path}")
        except Exception as e:
            print(f"Failed to register {template_path}: {e}")

    return tools


def register_templates_from_source(
    app: FastAPI,
    source: str,
    pattern: str = "*.md",
    remove_comments: bool = True,
):
    """
    Register templates from various sources as FastAPI endpoints.

    Supported formats:
    - Local directory: /path/to/templates/
    - Local file: /path/to/template.md
    - URL: https://example.com/template.md
    - GitHub raw URL: https://raw.githubusercontent.com/owner/repo/branch/path/template.md
    - GitHub repo: owner/repo (loads all templates from .github/ISSUE_TEMPLATE/)
    - GitHub repo with path: owner/repo:.github/ISSUE_TEMPLATE/bug.md

    Parameters
    ----------
    app : FastAPI
        The FastAPI app
    source : str
        The source path, URL, or GitHub repo identifier
    pattern : str
        Glob pattern for local directory (default: "*.md")
    remove_comments : bool
        Whether to remove HTML comments

    Returns
    -------
    list
        List of registered endpoint functions
    """
    tools = []

    for template_source in load_templates(source, pattern):
        try:
            tool = create_tool_from_source(
                app, template_source, remove_comments=remove_comments
            )
            tools.append(tool)
            print(
                f"Registered endpoint from: {template_source.source_type} - {template_source.source_path}"
            )
        except Exception as e:
            print(f"Failed to register {template_source.name}: {e}")

    return tools
