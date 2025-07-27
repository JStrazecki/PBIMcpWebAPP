# Branch Management Strategy

This repository uses a dual-branch strategy to support both simplified and full deployment modes.

## 🌿 Branch Overview

### `simplified` Branch (Recommended for Azure)
- **Purpose**: Production Azure Web App deployment
- **Dependencies**: Minimal (no database packages)
- **Main File**: `main_simple.py`
- **Requirements**: Standard `requirements.txt` with minimal dependencies
- **Target**: Azure Web App, cloud environments
- **Auto-Deploy**: ✅ Pushes to this branch trigger Azure deployment

### `main` Branch (Full Featured)
- **Purpose**: Local development and advanced features
- **Dependencies**: Complete (includes database, monitoring, etc.)
- **Main File**: `pbi_mcp_finance/main.py`
- **Requirements**: Standard `requirements.txt` with full dependencies
- **Target**: Local development, advanced deployments
- **Auto-Deploy**: ❌ Manual deployment only

## 🚀 Quick Start

### Deploy to Azure (Recommended)
```bash
# Switch to simplified branch
git checkout simplified

# Make your changes to environment variables or configuration
# DO NOT modify requirements.txt in this branch

# Commit and push - auto-deploys to Azure
git add .
git commit -m "Update configuration"
git push origin simplified
```

### Local Development
```bash
# Switch to main branch
git checkout main

# Install full dependencies
pip install -r requirements.txt

# Run locally with all features
python pbi_mcp_finance/main.py
```

## 📋 Branch Comparison

| Feature | `simplified` Branch | `main` Branch |
|---------|-------------------|---------------|
| **Deployment Target** | Azure Web App | Local/Advanced |
| **Dependencies** | Minimal (9 packages) | Full (40+ packages) |
| **Database** | ❌ None | ✅ SQLite |
| **Conversation Tracking** | ❌ Disabled | ✅ Enabled |
| **Performance Monitoring** | ❌ Basic | ✅ Advanced |
| **Startup Time** | 🚀 Fast (~30s) | 🐌 Slower (~60s) |
| **Memory Usage** | 💚 Low (~100MB) | 🟡 Higher (~300MB) |
| **Complexity** | 💚 Simple | 🔴 Complex |
| **Auto-Deploy** | ✅ GitHub Actions | ❌ Manual |

## 🔄 Working with Both Branches

### Making Changes

#### Configuration Changes (Environment Variables)
```bash
# Make the same change in both branches
git checkout simplified
# Edit configuration files
git add . && git commit -m "Update config"
git push origin simplified

git checkout main  
# Apply the same changes
git add . && git commit -m "Update config"
git push origin main
```

#### Code Changes
```bash
# For simplified mode changes
git checkout simplified
# Edit main_simple.py or other simplified files
git commit -m "Update simplified mode"
git push origin simplified

# For full mode changes  
git checkout main
# Edit pbi_mcp_finance/ files
git commit -m "Update full mode"
git push origin main
```

### Syncing Common Files
Some files should be kept in sync between branches:
- Documentation (*.md files)
- Configuration templates (.env.template)
- Azure configuration (web.config, startup.sh logic)

```bash
# Sync documentation from main to simplified
git checkout main
git checkout simplified
git checkout main -- README.md DEPLOYMENT_CHECKLIST.md
git commit -m "Sync documentation from main"
git push origin simplified
```

## 🚨 Important Rules

### ✅ Do's
- **Use `simplified` branch for Azure deployment**
- **Use `main` branch for local development**
- **Keep critical environment variables the same in both branches**
- **Test changes in both branches if they affect common functionality**
- **Sync documentation between branches regularly**

### ❌ Don'ts
- **Don't modify `requirements.txt` in `simplified` branch** (keep minimal)
- **Don't add database dependencies to `simplified` branch**
- **Don't deploy `main` branch to Azure** (too heavy, database issues)
- **Don't merge branches automatically** (they serve different purposes)

## 🛠️ Branch-Specific Files

### Files that differ between branches:

| File | `simplified` Branch | `main` Branch |
|------|-------------------|---------------|
| `requirements.txt` | Minimal dependencies | Full dependencies |
| Workflow trigger | `simplified` branch | No auto-deploy |
| Primary entry point | `main_simple.py` | `pbi_mcp_finance/main.py` |

### Files that should be the same:
- Documentation (*.md)
- Configuration templates (.env.template)
- Azure settings (web.config)
- Startup logic (startup.sh)

## 🔧 Troubleshooting

### "Wrong dependencies installed"
- Check you're on the right branch: `git branch --show-current`
- Simplified branch should have ~9 dependencies
- Main branch should have 40+ dependencies

### "Database errors in Azure"
- Make sure you're deploying from `simplified` branch
- Check Azure deployment logs show "SIMPLIFIED MODE"

### "Missing features locally"
- Switch to `main` branch: `git checkout main`
- Install full dependencies: `pip install -r requirements.txt`

### "Changes not deploying to Azure"
- Ensure you're pushing to `simplified` branch
- Check GitHub Actions tab for deployment status

## 📊 Deployment Status

### Current Active Deployments
- **Azure Web App**: `simplified` branch (auto-deploy)
- **Local Development**: `main` branch (manual)

### Monitoring Deployments
```bash
# Check what's deployed to Azure
curl https://your-app.azurewebsites.net/health

# Should show: "simplified mode" or similar
```

## 🎯 Recommended Workflow

1. **Daily Development**: Work in `main` branch
2. **Azure Deployment**: Switch to `simplified`, merge critical changes, push
3. **Testing**: Test both branches for compatibility
4. **Documentation**: Keep both branches' docs synchronized

This strategy ensures:
- ✅ Fast, reliable Azure deployments
- ✅ Full development environment available locally  
- ✅ Clear separation of concerns
- ✅ No database deployment issues
- ✅ Minimal Azure resource usage