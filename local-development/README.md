# 💻 Local Development Scripts

This directory contains scripts and configuration files for local development and testing.

## 📁 Files

### Scripts
- `setup_local_mcp.bat` - Windows batch script to set up local MCP server for development

### Configuration Files  
- `claude_desktop_config.json` - Configuration for Claude Desktop (local development)

## 🚀 Usage

### Setting Up Local MCP Server
```bash
# Windows
setup_local_mcp.bat

# This script will:
# - Set up local MCP server environment
# - Configure necessary dependencies
# - Prepare for local testing with Claude Desktop
```

### Claude Desktop Configuration
The `claude_desktop_config.json` file should be copied to your Claude Desktop configuration directory:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

## 🎯 Purpose

These files are for:
- ✅ Local development and testing
- ✅ Claude Desktop integration (non-enterprise)
- ✅ Development environment setup
- ❌ NOT for production deployment (use api-management/ for that)

## 🔗 Related Directories

- `../api-management/` - Production API Management deployment
- `../azure-deployment/` - Azure Web App deployment files
- `../documentation/` - Complete setup guides