# Advanced MCP Server Features

## Overview

The advanced MCP server (`mcp_advanced_asgi.py`) implements the full Model Context Protocol specification with enhanced features for production use.

## New Features

### 1. **Caching System**
- 5-minute cache for API responses
- Reduces Power BI API calls
- Automatic cache expiration
- Manual cache clearing tool

### 2. **Usage Statistics**
- Track tool usage counts
- Monitor execution times
- Performance metrics per tool
- Server health monitoring

### 3. **Resources**
Resources provide static reference content:
- **DAX Function Reference** - Complete DAX documentation
- **Sample DAX Queries** - Common query patterns

Access via:
```json
{
  "method": "resources/list",
  "params": {}
}
```

### 4. **Prompts**
Pre-defined prompt templates for common tasks:
- **analyze_dataset** - Analyze a dataset and suggest insights
- **optimize_dax** - Optimize DAX queries for performance

Use with:
```json
{
  "method": "prompts/get",
  "params": {"name": "analyze_dataset"}
}
```

### 5. **Enhanced Tools**

#### powerbi_health
- API connectivity test
- Cache status
- Usage statistics
- Environment detection

#### powerbi_workspaces
- Capacity information
- Dedicated capacity status
- Enhanced metadata

#### powerbi_datasets
- Storage mode details
- Security requirements
- Creation dates
- Content provider types

#### powerbi_query
- Execution time tracking
- Enhanced error messages
- Performance metrics

#### clear_cache
- Manual cache management
- Returns items cleared

#### get_usage_stats
- Detailed usage metrics
- Average execution times
- Cache information

### 6. **Logging Control**
Dynamic logging level adjustment:
```json
{
  "method": "logging/setLevel",
  "params": {"level": "debug"}
}
```

## Performance Optimizations

1. **Token Caching** - Power BI tokens cached for 50 minutes
2. **Response Caching** - API responses cached for 5 minutes
3. **Async Operations** - All tools use async/await
4. **Error Recovery** - Graceful fallback to demo data

## Demo Data Enhancements

- More realistic sample data
- Multiple months of financial data
- Regional sales breakdowns
- Department efficiency metrics

## Deployment

To use the advanced server:

1. Update Procfile:
```
web: gunicorn --bind=0.0.0.0:$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 600 --access-logfile - --error-logfile - --log-level info mcp_advanced_asgi:application
```

2. Deploy to Azure
3. Test enhanced features

## Testing Advanced Features

### Test Caching:
```bash
# First call - hits API
curl -X POST https://your-app.azurewebsites.net/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"powerbi_workspaces"},"id":1}'

# Second call within 5 minutes - returns cached data
curl -X POST https://your-app.azurewebsites.net/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"powerbi_workspaces"},"id":2}'
```

### Test Resources:
```bash
curl -X POST https://your-app.azurewebsites.net/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"resources/list","id":1}'
```

### Test Statistics:
```bash
curl -X POST https://your-app.azurewebsites.net/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_usage_stats"},"id":1}'
```

## Benefits

1. **Better Performance** - Caching reduces API calls
2. **Production Ready** - Monitoring and statistics
3. **Enhanced UX** - Resources and prompts for guidance
4. **Debugging** - Dynamic logging control
5. **Reliability** - Error handling and recovery