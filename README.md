<div align="center">

  <h1> MCP Markdown Template </h1>

</div>


## 🚀 Core Idea

Transform markdown templates (like GitHub Issue templates) into MCP tools automatically. Write a template once, get both a FastAPI endpoint and an MCP tool.

## 🏗️ Architecture

```
mcp_tools/
├── models.py      # Data models (Template, TemplateVariable)
├── loader.py      # Load templates from files, directories, URLs
├── parser.py      # Extract variables & render with Jinja2
├── generator.py   # Create FastAPI endpoints dynamically
└── server.py      # FastMCP server with CORS
```

**How it works:** 
 
1. **Load** - Fetch templates from local files, directories, or URLs  
2. **Parse** - Extract `<variables>` and metadata from YAML frontmatter  
3. **Generate** - Create typed FastAPI endpoints with Pydantic models  
4. **Serve** - Expose as both REST API (`/api/docs`) and MCP tools (`/mcp`)  

## 🌟 Features

- **Auto-generate MCP tools** from markdown templates
- **Multiple sources** - Load from local files, directories, or URLs
- **Swagger UI** - Test endpoints at `/api/docs`
- **Docker ready** - Production-ready container setup
- **CI/CD** - GitHub Actions for automated workflows

## 🛠️ Getting Started

### Local Development

Install dependencies:

```bash
uv sync
```

Run the MCP server:

```bash
uv run uvicorn mcp_tools.main:starlette_app --host 127.0.0.1 --port 8000
```

### Docker

Build the Docker image:

```bash
docker build -t docker.io/username/mcp-markdown-template:latest .
```

Run the container with various template sources:

```bash
# Mount local templates directory
docker run -i --rm -p 8000:8000 \
  -v /path/to/your/templates:/app/templates \
  -e MCP_TEMPLATES_SOURCE=/app/templates \
  docker.io/hsiangjenli/mcp-markdown-template:latest
```

```bash
# Load from URL (GitHub raw URL)
docker run -i --rm -p 8000:8000 \
  -e MCP_TEMPLATES_SOURCE=https://raw.githubusercontent.com/hsiangjenli/mcp-markdown-template/refs/heads/main/.github/ISSUE_TEMPLATE/demo.md \
  docker.io/hsiangjenli/mcp-markdown-template:latest
```

```bash
# Multiple sources (comma-separated)
docker run -i --rm -p 8000:8000 \
  -e MCP_TEMPLATES_SOURCE="/app/templates,https://raw.githubusercontent.com/owner/repo/main/template.md" \
  -v /path/to/local/templates:/app/templates \
  docker.io/hsiangjenli/mcp-markdown-template:latest
```

MCP Server configuration (for Claude Desktop, etc.):

```json
{
	"servers": {
		"markdown-template": {
			"url": "http://localhost:8000/mcp",
			"type": "http"
		}
	},
	"inputs": []
}
```

### Template Sources

| Format | Example |
|--------|---------|
| Local directory | `/path/to/templates/` |
| Local file | `/path/to/template.md` |
| URL | `https://raw.githubusercontent.com/.../template.md` |
| Multiple | `source1,source2` (comma-separated) |

### Environment Variables

| Variable | Default |
|----------|---------|
| `MCP_TITLE` | `Python MCP Template` |
| `MCP_DESCRIPTION` | `A template for creating MCP-compliant FastAPI` |
| `MCP_TEMPLATES_SOURCE` | `.github/ISSUE_TEMPLATE` |

## 📚 Documentation

Build docs locally:

```bash
scripts/build_docs.sh && uv run mkdocs build
```
