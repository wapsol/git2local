"""
Main entry point for EAR tool unified CLI.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
import sys
from pathlib import Path

app = typer.Typer(
    name="ear-tool",
    help="Engineering Activity Report (EAR) Tool - Unified GitHub and Odoo reporting",
    add_completion=False
)
console = Console()


@app.command()
def generate(
    orgs: str = typer.Option(
        None,
        "--orgs",
        help="Comma-separated GitHub organizations (or use GITHUB_ORGS env var)"
    ),
    period: str = typer.Option(
        "lastweek",
        "--period",
        help="Time period: lastweek, week, 7d, 14d, month, lastmonth, quarter, year"
    ),
    devs: Optional[str] = typer.Option(
        None,
        "--devs",
        help="Comma-separated developer usernames to filter"
    ),
    include_odoo: bool = typer.Option(
        False,
        "--include-odoo",
        help="Include Odoo helpdesk tickets in the report"
    ),
    odoo_only: bool = typer.Option(
        False,
        "--odoo-only",
        help="Generate report with only Odoo data (skip GitHub)"
    ),
    refresh_rate: Optional[str] = typer.Option(
        None,
        "--refreshrate",
        help="Auto-refresh rate for live updates (e.g., '10s', '5m')"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: reports/EAR_YYYY-MM-DD.html)"
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Run without interactive prompts"
    )
):
    """Generate an Engineering Activity Report."""
    from .models.config import get_config
    from .services.github_service import GitHubService
    from .services.odoo_service import OdooService
    from .utils.date_helpers import calculate_date_range, parse_refresh_rate
    from datetime import datetime
    import os

    try:
        console.print(Panel(
            "EAR Report Generator",
            style="bold blue"
        ))

        config = get_config()

        # Determine organizations
        if orgs:
            orgs_list = [org.strip() for org in orgs.split(',') if org.strip()]
        else:
            orgs_list = config.github.get_orgs_list()

        console.print(f"Organizations: {', '.join(orgs_list)}")

        # Calculate date range
        since_date, end_date, period_label = calculate_date_range(period)
        console.print(f"Period: {period_label} ({since_date} to {end_date})")

        # Parse developer filter
        filter_devs = None
        if devs:
            filter_devs = set(dev.strip() for dev in devs.split(','))
            console.print(f"Filtering for developers: {', '.join(filter_devs)}")

        # Parse refresh rate
        refresh_rate_ms = parse_refresh_rate(refresh_rate) if refresh_rate else None
        if refresh_rate_ms:
            console.print(f"Auto-refresh: every {refresh_rate}")

        report_date = datetime.now().strftime('%Y-%m-%d')

        # Fetch GitHub data (unless --odoo-only)
        developer_activity = {}
        if not odoo_only:
            console.print("\n[bold]Fetching GitHub data...[/bold]")
            github_service = GitHubService()
            data = github_service.fetch_recent_activity(orgs_list, since_date)

            console.print("Aggregating data by developer...")
            developer_activity = github_service.aggregate_by_developer(data, filter_devs)

            if not developer_activity and not include_odoo:
                console.print("[yellow]No GitHub activity found.[/yellow]")
                raise typer.Exit(0)

            console.print(f"[green]✓[/green] Found activity for {len(developer_activity)} developer(s)")

        # Fetch Odoo data if requested
        odoo_user_activity = None
        if include_odoo or odoo_only:
            console.print("\n[bold]Fetching Odoo data...[/bold]")

            if not config.odoo.password:
                console.print("[red]Error: Odoo password not configured.[/red]")
                console.print("Set ODOO_PASSWORD environment variable or add to .env file")
                raise typer.Exit(1)

            try:
                odoo_service = OdooService(config.odoo)
                tickets = odoo_service.fetch_tickets(since_date, end_date)

                if tickets:
                    console.print(f"Aggregating Odoo tickets...")
                    odoo_user_activity = odoo_service.aggregate_by_user(tickets, filter_devs)
                    console.print(f"[green]✓[/green] Found activity for {len(odoo_user_activity)} user(s)")
                else:
                    console.print("[yellow]No Odoo tickets found.[/yellow]")

            except Exception as e:
                console.print(f"[red]Error fetching Odoo data: {e}[/red]")
                raise typer.Exit(1)

        # Check if we have any data
        if not developer_activity and not odoo_user_activity:
            console.print("[yellow]No activity found.[/yellow]")
            raise typer.Exit(0)

        # Generate report
        # NOTE: This requires the full git2local generate_html_report function
        # For now, we'll import from the legacy file until ReportService is implemented
        console.print("\n[bold]Generating HTML report...[/bold]")

        # Import legacy function temporarily
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from git2local import generate_html_report

        html = generate_html_report(
            developer_activity,
            report_date,
            since_date,
            end_date,
            period_label,
            orgs_list,
            refresh_rate_ms,
            odoo_user_activity
        )

        # Save report
        if output:
            output_path = output
        else:
            os.makedirs('reports', exist_ok=True)
            output_path = f'reports/EAR_{report_date}.html'

        with open(output_path, 'w') as f:
            f.write(html)

        console.print(Panel(
            f"[green]✓[/green] Report generated successfully!\n\n"
            f"File: {output_path}\n"
            f"URL: file://{os.path.abspath(output_path)}",
            title="Success",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def serve(
    port: int = typer.Option(
        443,
        "--port",
        "-p",
        help="Server port (default: 443, requires sudo)"
    ),
    auto_cert: bool = typer.Option(
        True,
        "--auto-cert/--no-auto-cert",
        help="Auto-generate SSL certificates if missing"
    )
):
    """Start HTTPS server to serve reports."""
    # TODO: Implement WebService
    # For now, delegate to legacy script
    import subprocess
    import os

    console.print(Panel(
        f"Starting HTTPS server on port {port}...",
        style="bold blue"
    ))

    script_path = Path(__file__).parent.parent / "start_ear_server.sh"
    if script_path.exists():
        try:
            subprocess.run([str(script_path), str(port)], check=True)
        except KeyboardInterrupt:
            console.print("\n[green]Server stopped.[/green]")
    else:
        console.print("[red]Legacy server script not found. WebService not yet implemented.[/red]")
        raise typer.Exit(1)


@app.command()
def api(
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="API server port"
    ),
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        help="API server host"
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development"
    )
):
    """Start Odoo Query API server."""
    import uvicorn

    console.print(Panel(
        f"Starting API server on {host}:{port}...\n"
        f"Docs: http://localhost:{port}/docs",
        style="bold blue"
    ))

    # Import and run the API app
    # TODO: Refactor odoo_query_server.py to use ear_tool.api.app
    # For now, use legacy
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from odoo_query_server import app as api_app

    uvicorn.run(api_app, host=host, port=port, reload=reload, log_level="info")


@app.command()
def query(
    query_text: str = typer.Argument(..., help="Natural language query for Odoo tickets")
):
    """Execute an Odoo query from command line."""
    from .models.config import get_config
    from .services.odoo_service import OdooService
    from rich.table import Table

    try:
        config = get_config()

        if not config.odoo.password:
            console.print("[red]Error: Odoo password not configured.[/red]")
            raise typer.Exit(1)

        odoo_service = OdooService(config.odoo)

        console.print(f"[bold]Query:[/bold] {query_text}")
        console.print(f"[bold]Summary:[/bold] {odoo_service.get_query_summary(query_text)}\n")

        tickets = odoo_service.query_natural_language(query_text)

        if not tickets:
            console.print("[yellow]No tickets found.[/yellow]")
            return

        # Display results in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim")
        table.add_column("Title")
        table.add_column("Customer")
        table.add_column("User")
        table.add_column("Status")

        for ticket in tickets[:10]:  # Limit to 10 results
            status = "✓ Closed" if ticket.is_closed else "○ Open"
            table.add_row(
                str(ticket.id),
                ticket.name[:50],
                ticket.customer[:30],
                ticket.user[:20],
                status
            )

        console.print(table)
        console.print(f"\n[dim]Showing {min(len(tickets), 10)} of {len(tickets)} results[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration"
    )
):
    """Manage configuration."""
    from .models.config import get_config
    from rich.table import Table

    cfg = get_config()

    if show:
        table = Table(show_header=True, header_style="bold magenta", title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Odoo URL", cfg.odoo.url)
        table.add_row("Odoo DB", cfg.odoo.db)
        table.add_row("Odoo User", cfg.odoo.user)
        table.add_row("Odoo Password", "***" if cfg.odoo.password else "[red]Not set[/red]")
        table.add_row("GitHub Orgs", ", ".join(cfg.github.get_orgs_list()))
        table.add_row("Default Period", cfg.github.default_period)
        table.add_row("Server Port", str(cfg.server.port))
        table.add_row("API Port", str(cfg.api.port))

        console.print(table)
    else:
        console.print("Use --show to display current configuration")


if __name__ == "__main__":
    app()
