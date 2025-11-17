"""Status file writer for headless mode and external monitoring."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class StatusWriter:
    """Writes download status to JSON file for external monitoring."""

    def __init__(self, status_file: str):
        """
        Initialize status writer.

        Args:
            status_file: Path to status file
        """
        self.status_file = Path(status_file)
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

    def write_status(
        self,
        status: str,
        stats: dict,
        config: Optional[dict] = None
    ) -> None:
        """
        Write current status to file.

        Args:
            status: Current status string (e.g., 'running', 'complete', 'error')
            stats: Statistics dictionary
            config: Optional configuration info
        """
        try:
            status_data = {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'stats': stats,
                'config': config or {}
            }

            # Write atomically
            temp_file = self.status_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(status_data, f, indent=2)

            temp_file.replace(self.status_file)

        except Exception as e:
            logger.warning(f"Failed to write status file: {e}")

    def format_for_powerline(self, stats: dict) -> str:
        """
        Format stats for powerline/status bar display.

        Args:
            stats: Statistics dictionary

        Returns:
            Formatted string for status bar
        """
        downloaded = stats.get('downloaded_emails', 0)
        total = stats.get('total_emails', 0)
        errors = stats.get('errors', 0)

        if total > 0:
            percent = (downloaded / total) * 100
            status = f"📧 {downloaded}/{total} ({percent:.0f}%)"
        else:
            status = f"📧 {downloaded}"

        if errors > 0:
            status += f" ⚠️{errors}"

        return status
