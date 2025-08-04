# Power BI MCP Server

Minimal FastMCP server for Power BI integration with Claude AI, following Azure deployment best practices.

## Features

- 4 Power BI tools: health, workspaces, datasets, query
- Works with real Power BI data (if configured) or demo data
- No authentication required
- Built with FastMCP for native Claude compatibility
- Azure App Service ready with ASGI deployment

## Environment Variables

Optional - for real Power BI data:
- `AZURE_CLIENT_ID` - Power BI app registration client ID
- `AZURE_CLIENT_SECRET` - Power BI app registration secret  
- `AZURE_TENANT_ID` - Azure tenant ID

## Local Development

```bash
pip install -r requirements.txt
python main.py
```

## Azure Deployment

Uses Gunicorn with Uvicorn worker for ASGI compatibility:
```
web: gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT main:app
```

## Claude Configuration

- URL: `https://your-deployment-url/`
- Authentication: None

## Tools

1. **powerbi_health** - Check server health
2. **powerbi_workspaces** - List workspaces  
3. **powerbi_datasets** - Get datasets
4. **powerbi_query** - Execute DAX queries