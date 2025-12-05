"""
Parse markdown template and extract variables with their examples.
"""

import re
from pathlib import Path
from pydantic import BaseModel, Field
from jinja2 import Environment, StrictUndefined


class TemplateVariable(BaseModel):
    """Represents a variable in the template."""

    name: str
    description: str = ""
    example: str = ""


class ParsedTemplate(BaseModel):
    """Parsed template with metadata and variables."""

    name: str = ""
    about: str = ""
    variables: list[TemplateVariable] = Field(default_factory=list)
    raw_content: str = ""

    def get_variable_names(self) -> list[str]:
        return [v.name for v in self.variables]


def parse_template(
    template_source: Path | str, content: str | None = None
) -> ParsedTemplate:
    """
    Parse a markdown template and extract:
    - YAML frontmatter (name, about, etc.)
    - Variables in <variable_name> format
    - Example comments for each section

    Parameters
    ----------
    template_source : Path | str
        Path to the markdown template file, or a name identifier if content is provided
    content : str | None
        Raw markdown content. If None, will read from template_source path.

    Returns
    -------
    ParsedTemplate
        Parsed template with variables and metadata
    """
    if content is None:
        template_path = Path(template_source)
        raw = template_path.read_text(encoding="utf-8")
    else:
        raw = content

    result = ParsedTemplate(raw_content=raw)

    # Parse YAML frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", raw, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        # Extract name
        name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
        if name_match:
            result.name = name_match.group(1).strip()
        # Extract about
        about_match = re.search(r"^about:\s*(.+)$", frontmatter, re.MULTILINE)
        if about_match:
            result.about = about_match.group(1).strip()

    # Find all variables in <variable_name> format
    # Exclude HTML-like tags and frontmatter variables
    variable_pattern = r"<([a-z][a-z0-9_]*)>"
    variables_found = re.findall(variable_pattern, raw)
    unique_vars = list(
        dict.fromkeys(variables_found)
    )  # Preserve order, remove duplicates

    # Extract descriptions and examples for each variable
    # Split content into sections by ###
    sections = re.split(r"(###\s*[^:\n]+:)", raw)

    # Build a map of section name -> content
    section_map = {}
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            section_header = sections[i].strip()
            section_content = sections[i + 1]
            # Extract section name from "### Section Name:"
            section_name = re.sub(r"^###\s*|\s*:$", "", section_header)
            section_map[section_name] = section_content

    for var_name in unique_vars:
        var = TemplateVariable(name=var_name)

        # Find which section contains this variable
        for section_name, section_content in section_map.items():
            if f"<{var_name}>" in section_content:
                var.description = section_name

                # Extract comment before the variable
                comment_match = re.search(
                    rf"<!--([\s\S]*?)-->\s*<{var_name}>", section_content
                )
                if comment_match:
                    comment_content = comment_match.group(1).strip()

                    # Check if it contains "Example:"
                    example_match = re.search(
                        r"Example:?\s*([\s\S]*)", comment_content, re.IGNORECASE
                    )
                    if example_match:
                        var.example = example_match.group(1).strip()
                    else:
                        # Use the comment as additional description
                        var.description = f"{section_name}: {comment_content}"
                break

        # Handle frontmatter variables (like title)
        if not var.description and frontmatter_match:
            # Check if variable is in frontmatter
            title_pattern = rf"title:\s*'[^']*<{var_name}>[^']*'"
            if re.search(title_pattern, raw):
                var.description = "Issue title"

        result.variables.append(var)

    return result


def render_template(
    template_source: Path | str,
    variables: dict[str, str],
    remove_comments: bool = True,
    content: str | None = None,
) -> str:
    """
    Render a template with the given variables.

    Parameters
    ----------
    template_source : Path | str
        Path to the markdown template file, or a name identifier if content is provided
    variables : dict[str, str]
        Variables to render
    remove_comments : bool
        Whether to remove HTML comments from output
    content : str | None
        Raw markdown content. If None, will read from template_source path.

    Returns
    -------
    str
        Rendered template
    """
    if content is None:
        template_path = Path(template_source)
        raw = template_path.read_text(encoding="utf-8")
    else:
        raw = content

    # Escape HTML comments to prevent Jinja2 from parsing them
    comments = []

    def save_comment(match):
        comments.append(match.group(0))
        return f"__COMMENT_{len(comments) - 1}__"

    escaped = re.sub(r"<!--[\s\S]*?-->", save_comment, raw)

    # Create Jinja2 environment with custom delimiters
    env = Environment(
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
        variable_start_string="<",
        variable_end_string=">",
    )
    template = env.from_string(escaped)

    # Render
    rendered = template.render(**variables)

    # Restore or remove comments
    if remove_comments:
        rendered = re.sub(r"__COMMENT_\d+__\s*\n?", "", rendered)
    else:

        def restore_comment(match):
            idx = int(match.group(1))
            return comments[idx]

        rendered = re.sub(r"__COMMENT_(\d+)__", restore_comment, rendered)

    return rendered


if __name__ == "__main__":
    # Test parsing
    parsed = parse_template(".github/ISSUE_TEMPLATE/demo.md")
    print(f"Template: {parsed.name}")
    print(f"About: {parsed.about}")
    print(f"\nVariables:")
    for var in parsed.variables:
        print(f"  - {var.name}")
        print(f"    Description: {var.description}")
        if var.example:
            print(f"    Example: {var.example[:50]}...")
