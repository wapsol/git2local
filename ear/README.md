# EAR Tool - Engineering Activity Report System

Refactored and unified engineering activity reporting system for GitHub and Odoo.

## Architecture

```
ear_tool/
├── models/          # Pydantic models for type safety
│   ├── config.py    # Unified configuration (Pydantic Settings)
│   ├── activity.py  # GitHub activity models
│   └── ticket.py    # Odoo ticket models
├── services/        # Business logic layer
│   ├── odoo_service.py      # Unified Odoo operations
│   ├── github_service.py    # GitHub API wrapper
│   ├── report_service.py    # HTML report generation
│   └── web_service.py       # HTTPS server
├── api/             # FastAPI application
│   ├── app.py       # Main FastAPI app
│   └── routers/     # API route modules
├── utils/           # Helper utilities
│   ├── odoo_api.py          # Odoo XML-RPC client
│   ├── query_parser.py      # Natural language parser
│   ├── text_processing.py   # Text utilities
│   └── date_helpers.py      # Date/time utilities
├── templates/       # Jinja2 templates
│   └── partials/    # Reusable template components
└── main.py          # Unified CLI entry point
```

## Configuration

Configuration uses a cascading priority system:
1. Command-line arguments (highest priority)
2. Environment variables
3. `.env` file
4. Default values (lowest priority)

### Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# Odoo Configuration
ODOO_URL=https://erp.wapsol.de
ODOO_DB=wapsol
ODOO_USER=your_email@example.com
ODOO_PASSWORD=your_password

# GitHub Configuration
GITHUB_ORGS=euroblaze,wapsol
GITHUB_DEFAULT_PERIOD=lastweek

# Server Configuration
SERVER_PORT=443
SERVER_AUTO_GENERATE_CERTS=true

# API Configuration
API_PORT=8000
```

## Services

### OdooService
Consolidates all Odoo operations:
- Connection management with caching
- Ticket fetching and enrichment
- Natural language query parsing
- User activity aggregation

### GitHubService
Handles GitHub API interactions:
- GraphQL query execution via `gh` CLI
- Issue and PR fetching
- Developer activity aggregation

### ReportService (To be implemented)
Generates HTML reports:
- Jinja2 template rendering
- Data formatting and presentation
- Report persistence

### WebService (To be implemented)
HTTPS server with production features:
- SSL certificate auto-generation
- Pre-flight validation checks
- Port availability checking
- Hosts file validation

## Models

### Pydantic Models
All data structures use Pydantic for:
- Runtime type checking
- Data validation
- Automatic serialization/deserialization
- IDE autocomplete support

## Backward Compatibility

Legacy scripts are supported via wrapper scripts that delegate to the new unified CLI.

## Development

### Installation

```bash
# Install in development mode
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=ear_tool --cov-report=html
```

### Code Quality

```bash
# Format code
black ear_tool/

# Lint
ruff ear_tool/

# Type check
mypy ear_tool/
```

## Migration from Legacy

See `MIGRATION.md` for detailed migration guide from the old scripts to the new unified system.
