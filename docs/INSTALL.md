# Quick Installation Guide

## Prerequisites

- Python 3.9 or higher
- `gh` CLI (GitHub CLI) for GitHub data
- Odoo credentials (for Odoo features)

## Installation Steps

### 1. Install the Package

```bash
# From the git2local directory
pip install -e .
```

This installs `ear-tool` and all dependencies defined in `pyproject.toml`.

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

Minimum required configuration in `.env`:
```bash
# Odoo (required for Odoo features)
ODOO_PASSWORD=your_odoo_password_here

# Optional overrides (defaults shown)
ODOO_URL=https://erp.wapsol.de
ODOO_DB=wapsol
ODOO_USER=ashant@simplify-erp.de

# GitHub (optional, can override on command line)
GITHUB_ORGS=euroblaze,wapsol
GITHUB_DEFAULT_PERIOD=lastweek
```

### 3. Verify Installation

```bash
# Check if ear-tool is installed
python -m ear_tool.main --help

# Or if installed globally:
ear-tool --help
```

You should see:
```
Usage: ear-tool [OPTIONS] COMMAND [ARGS]...

  Engineering Activity Report (EAR) Tool - Unified GitHub and Odoo reporting

Commands:
  api       Start Odoo Query API server.
  config    Manage configuration.
  generate  Generate an Engineering Activity Report.
  query     Execute an Odoo query from command line.
  serve     Start HTTPS server to serve reports.
```

### 4. Test with a Simple Report

```bash
# Generate a report for last week (GitHub only, no Odoo password needed)
python -m ear_tool.main generate --period=lastweek

# If configured with Odoo password:
python -m ear_tool.main generate --period=week --include-odoo
```

### 5. Try CLI Queries (if Odoo configured)

```bash
python -m ear_tool.main query "show me open tickets"
```

## Common Issues

### "Module 'ear_tool' has no attribute 'main'"

Make sure you're in the git2local directory and run:
```bash
pip install -e .
```

### "Odoo password not configured"

Either:
1. Set in `.env`: `ODOO_PASSWORD=your_password`
2. Or use environment variable: `export ODOO_PASSWORD=your_password`

### "Command 'gh' not found"

Install GitHub CLI:
- macOS: `brew install gh`
- Linux: See https://github.com/cli/cli#installation
- Windows: See https://github.com/cli/cli#installation

Then authenticate:
```bash
gh auth login
```

### Import errors

Make sure you're running from the git2local directory, or the package is properly installed:
```bash
cd /path/to/git2local
pip install -e .
```

## Usage Examples

```bash
# Generate reports
python -m ear_tool.main generate --period=week
python -m ear_tool.main generate --period=month --devs=VTV24710
python -m ear_tool.main generate --period=lastweek --include-odoo --refreshrate=5m

# Query Odoo
python -m ear_tool.main query "my high priority tickets"
python -m ear_tool.main query "closed tickets from last month"

# Start servers
python -m ear_tool.main api --port=8000
sudo python -m ear_tool.main serve --port=443

# View configuration
python -m ear_tool.main config --show
```

## Alternative: Using Legacy Scripts

The old scripts still work if you prefer:

```bash
# Legacy report generation
./git2local --orgs=euroblaze --period=week

# Legacy API server
python3 odoo_query_server.py

# Legacy HTTPS server
sudo ./start_ear_server.sh
```

## Next Steps

1. Read `REFACTORING_GUIDE.md` for detailed usage
2. See `REFACTORING_SUMMARY.md` for what's been improved
3. Check `ear_tool/README.md` for architecture details

## Uninstallation

```bash
pip uninstall ear-tool
```

The legacy scripts will continue to work independently.
