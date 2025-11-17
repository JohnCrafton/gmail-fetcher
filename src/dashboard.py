"""Terminal dashboard interface for Gmail Fetcher."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text
from rich import box

logger = logging.getLogger(__name__)


class Dashboard:
    """Terminal dashboard for monitoring Gmail download progress."""

    def __init__(self, config):
        """Initialize dashboard with configuration."""
        self.config = config
        self.console = Console()
        self.stats = {
            'total_emails': 0,
            'downloaded_emails': 0,
            'total_attachments': 0,
            'total_size_bytes': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
            'status': 'Initializing'
        }

    def create_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=7)
        )

        layout["main"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="config", ratio=1)
        )

        return layout

    def render_header(self) -> Panel:
        """Render the header panel."""
        title = Text()
        title.append("Gmail Fetcher", style="bold cyan")
        title.append(" - Secure Local Email Archive", style="dim")

        return Panel(
            title,
            box=box.ROUNDED,
            style="bold white on blue"
        )

    def render_stats(self) -> Panel:
        """Render the statistics panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green", justify="right")

        # Status
        status_style = "green" if self.stats['status'] == 'Complete' else "yellow"
        table.add_row("Status", Text(self.stats['status'], style=status_style))
        table.add_row("", "")  # Spacer

        # Download stats
        table.add_row("Total Emails", str(self.stats['total_emails']))
        table.add_row("Downloaded", str(self.stats['downloaded_emails']))
        table.add_row("Attachments", str(self.stats['total_attachments']))

        # Size
        size_mb = self.stats['total_size_bytes'] / (1024 * 1024)
        table.add_row("Total Size", f"{size_mb:.2f} MB")

        # Errors and retries
        error_style = "red" if self.stats['errors'] > 0 else "green"
        table.add_row("Errors", Text(str(self.stats['errors']), style=error_style))

        # Rate limit info
        if self.stats.get('rate_limit_hits', 0) > 0:
            table.add_row("Rate Limits Hit", str(self.stats['rate_limit_hits']))
        if self.stats.get('retries', 0) > 0:
            table.add_row("API Retries", str(self.stats['retries']))

        table.add_row("", "")  # Spacer

        # Timing
        if self.stats['start_time']:
            elapsed = (self.stats['end_time'] or datetime.now()) - self.stats['start_time']
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            table.add_row("Elapsed Time", elapsed_str)

            if self.stats['downloaded_emails'] > 0:
                emails_per_sec = self.stats['downloaded_emails'] / elapsed.total_seconds()
                table.add_row("Speed", f"{emails_per_sec:.2f} emails/sec")

        return Panel(
            table,
            title="[bold]Statistics[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )

    def render_config(self) -> Panel:
        """Render the configuration panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Setting", style="cyan", width=20)
        table.add_column("Value", style="yellow")

        # Query
        query_display = self.config.query
        if len(query_display) > 30:
            query_display = query_display[:27] + "..."
        table.add_row("Query", query_display)

        # Output
        output_display = str(self.config.output_dir)
        if len(output_display) > 30:
            output_display = "..." + output_display[-27:]
        table.add_row("Output Dir", output_display)

        # Settings
        table.add_row("Attachments", "Yes" if self.config.include_attachments else "No")
        table.add_row("Archive", "Yes" if self.config.archive_enabled else "No")

        max_results_display = str(self.config.max_results) if self.config.max_results else "All"
        table.add_row("Max Results", max_results_display)

        # Warning for delete
        if self.config.delete_after_download:
            table.add_row("", "")  # Spacer
            table.add_row("⚠ DELETE MODE", Text("ENABLED", style="bold red"))

        return Panel(
            table,
            title="[bold]Configuration[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )

    def render_footer(self) -> Panel:
        """Render the footer panel with help text."""
        help_text = Text()
        help_text.append("Controls: ", style="bold cyan")
        help_text.append("Ctrl+C", style="bold yellow")
        help_text.append(" to stop gracefully\n")

        help_text.append("\nSecurity: ", style="bold cyan")
        help_text.append("Running in non-root container", style="green")
        help_text.append(" | ")
        help_text.append("Local storage only", style="green")
        help_text.append(" | ")

        creds_status = "Using Docker secrets" if str(self.config.credentials_path).startswith("/run/secrets") else "Using .env file"
        help_text.append(creds_status, style="yellow")

        return Panel(
            help_text,
            border_style="dim",
            box=box.ROUNDED
        )

    def update_stats(self, stats: dict) -> None:
        """Update dashboard statistics."""
        self.stats.update(stats)

    def render(self, layout: Layout) -> None:
        """Render all dashboard components."""
        layout["header"].update(self.render_header())
        layout["stats"].update(self.render_stats())
        layout["config"].update(self.render_config())
        layout["footer"].update(self.render_footer())

    def run_live(self, download_func):
        """
        Run dashboard in live mode while downloading.

        Args:
            download_func: Function to call for downloading (should accept progress_callback)
        """
        layout = self.create_layout()
        self.stats['start_time'] = datetime.now()
        self.stats['status'] = 'Downloading'

        def progress_callback(stats):
            """Update dashboard with download progress."""
            self.update_stats(stats)

        try:
            # Disable refresh in non-TTY environments
            import sys
            is_tty = sys.stdout.isatty()

            with Live(
                layout,
                refresh_per_second=4 if is_tty else 1,
                console=self.console,
                transient=False
            ):
                # Initial render
                self.render(layout)
                time.sleep(0.5)

                # Run download with progress updates
                result = download_func(progress_callback=progress_callback)

                # Update final stats
                self.stats['end_time'] = datetime.now()
                self.stats['status'] = 'Complete'
                self.update_stats(result)
                self.render(layout)

                # Keep dashboard visible for a moment
                time.sleep(2)

        except KeyboardInterrupt:
            self.stats['status'] = 'Cancelled'
            self.stats['end_time'] = datetime.now()
            self.render(layout)
            self.console.print("\n[yellow]Download cancelled by user[/yellow]")

        return self.stats

    def show_summary(self, stats: dict) -> None:
        """Show final summary after download completes."""
        self.console.print("\n[bold green]Download Complete![/bold green]\n")

        summary_table = Table(title="Summary", box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green", justify="right")

        summary_table.add_row("Total Emails", str(stats['downloaded_emails']))
        summary_table.add_row("Attachments", str(stats['total_attachments']))

        size_mb = stats['total_size_bytes'] / (1024 * 1024)
        summary_table.add_row("Total Size", f"{size_mb:.2f} MB")

        if stats.get('errors', 0) > 0:
            summary_table.add_row("Errors", str(stats['errors']))

        self.console.print(summary_table)
        self.console.print(f"\n[dim]Output: {self.config.output_dir}[/dim]\n")
