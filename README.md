<div align="center">

  <h1> Python MCP Template </h1>

</div>

> A DevOps-friendly template with CI/CD, Docker, and Documentation-as-Code (DaC) for building MCP server

## 🚀 Core Idea

This template leverages **fastmcp** and **FastAPI** to seamlessly integrate MCP functionality while inheriting the original OpenAPI specifications.

## 🌟 Features

- **CI/CD Integration**: Automate your workflows with GitHub Actions.
- **Dockerized Environment**: Consistent and portable development and production environments.
- **Documentation-as-Code**: Automatically generate and deploy documentation using MkDocs. This process also utilizes the `openapi.json` file to ensure API documentation is up-to-date.
- **FastAPI Integration**: Build robust APIs with OpenAPI support.

## 🛠️ Getting Started

### Local Development

1. Install dependencies:
  ```bash
  uv sync
  ```

2. Run the MCP server:
  ```bash
  # HTTP (recommended)
  uv run uvicorn mcp_tools.main:starlette_app --host 127.0.0.1 --port 8000
  ```

  ```bash
  # stdio
  uv run --with fastmcp fastmcp run mcp_tools/main.py
  ```

### Docker

1. Build the Docker image:
   ```bash
   docker build -t python-mcp-template:latest .
   ```

2. Run the container with various template sources:

   ```bash
   # Mount local templates directory
   docker run -i --rm -p 8000:8000 \
     -v /path/to/your/templates:/app/templates \
     -e MCP_TEMPLATES_SOURCE=/app/templates \
     python-mcp-template:latest
   ```

   ```bash
   # Load from URL (GitHub raw URL)
   docker run -i --rm -p 8000:8000 \
     -e MCP_TEMPLATES_SOURCE=https://raw.githubusercontent.com/hsiangjenli/mcp-yaml-to-markdown/refs/heads/main/.github/ISSUE_TEMPLATE/demo.md \
     python-mcp-template:latest
   ```

   ```bash
   # Multiple sources (comma-separated)
   docker run -i --rm -p 8000:8000 \
     -e MCP_TEMPLATES_SOURCE="/app/templates,https://raw.githubusercontent.com/owner/repo/main/template.md" \
     -v /path/to/local/templates:/app/templates \
     python-mcp-template:latest
   ```

3. MCP Server configuration:
  ```json
  {
    "mcpServers": {
      "python-mcp-template": {
        "command": "docker",
        "args": [
          "run",
          "--rm",
          "-i",
          "-p",
          "8000:8000",
          "-e",
          "MCP_TEMPLATES_SOURCE=owner/repo",
          "python-mcp-template:latest"
        ]
      }
    }
  }
  ```

### Template Sources

The `MCP_TEMPLATES_SOURCE` environment variable supports multiple formats:

| Format | Example | Description |
|--------|---------|-------------|
| Local directory | `/path/to/templates/` | Load all `.md` files from directory |
| Local file | `/path/to/template.md` | Load a single template file |
| URL | `https://raw.githubusercontent.com/.../template.md` | Load template from any URL |
| Multiple sources | `source1,source2` | Comma-separated, load from multiple sources |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TITLE` | `Python MCP Template` | Title of the MCP server |
| `MCP_DESCRIPTION` | `A template for creating MCP-compliant FastAPI` | Description of the MCP server |
| `MCP_TEMPLATES_SOURCE` | `.github/ISSUE_TEMPLATE` | Template source(s) - supports multiple formats |

## 📚 Documentation

- Documentation is built using MkDocs and deployed to GitHub Pages.
- To build the documentation locally:
  
  ```bash
  chmod +x scripts/build_docs.sh
  scripts/build_docs.sh
  mkdocs build
  ```
