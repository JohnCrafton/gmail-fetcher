"""Configuration management for Gmail Fetcher."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""

    # Gmail API credentials
    credentials_path: Path
    token_path: Path

    # Output settings
    output_dir: Path
    archive_enabled: bool
    archive_password: Optional[str]

    # Download settings
    max_results: Optional[int]
    include_attachments: bool
    delete_after_download: bool

    # Query settings
    query: str

    # Rate limiting settings
    requests_per_second: float
    max_retries: int

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Detect if running in container or locally
        # In container: use /data (mounted volume)
        # Locally: use ./data (current directory)
        default_data_dir = "/data" if os.path.exists("/.dockerenv") else "./data"
        base_dir = Path(os.getenv("DATA_DIR", default_data_dir))

        # Create base_dir if it doesn't exist (for local runs)
        base_dir.mkdir(parents=True, exist_ok=True)

        # Credentials can be mounted as Docker secrets
        creds_path = Path(os.getenv("CREDENTIALS_PATH", "/run/secrets/gmail_credentials"))
        if not creds_path.exists():
            # Fallback to .env location
            creds_path = Path(os.getenv("CREDENTIALS_PATH", "./credentials.json"))

        token_path = base_dir / "token.json"
        output_dir = base_dir / "emails"

        # Archive password - support both direct env var and file (Docker secrets)
        archive_password = os.getenv("ARCHIVE_PASSWORD")
        archive_password_file = os.getenv("ARCHIVE_PASSWORD_FILE")

        if not archive_password and archive_password_file:
            # Try to read from file (Docker secret)
            password_path = Path(archive_password_file)
            if password_path.exists():
                archive_password = password_path.read_text().strip()

        return cls(
            credentials_path=creds_path,
            token_path=token_path,
            output_dir=output_dir,
            archive_enabled=os.getenv("ARCHIVE_ENABLED", "false").lower() == "true",
            archive_password=archive_password,
            max_results=int(os.getenv("MAX_RESULTS", "0")) or None,
            include_attachments=os.getenv("INCLUDE_ATTACHMENTS", "true").lower() == "true",
            delete_after_download=os.getenv("DELETE_AFTER_DOWNLOAD", "false").lower() == "true",
            query=os.getenv("GMAIL_QUERY", "in:anywhere"),
            requests_per_second=float(os.getenv("REQUESTS_PER_SECOND", "10.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "5")),
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.credentials_path.exists():
            errors.append(f"Credentials file not found: {self.credentials_path}")

        if self.archive_enabled and not self.archive_password:
            errors.append("Archive password required when archiving is enabled")

        if self.delete_after_download:
            errors.append(
                "WARNING: DELETE_AFTER_DOWNLOAD is enabled. "
                "Emails will be permanently deleted from Gmail after download!"
            )

        # Validate rate limiting settings
        if self.requests_per_second < 0:
            errors.append("REQUESTS_PER_SECOND must be >= 0 (0 disables rate limiting)")

        if self.requests_per_second > 250:
            errors.append(
                f"WARNING: REQUESTS_PER_SECOND={self.requests_per_second} is very high. "
                "Gmail API limit is 250 req/sec per user. Recommended: 10-50."
            )

        if self.max_retries < 0:
            errors.append("MAX_RETRIES must be >= 0")

        return errors
