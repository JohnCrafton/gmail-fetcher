"""Main entry point for Gmail Fetcher."""

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .gmail_client import GmailClient
from .downloader import EmailDownloader
from .archiver import Archiver
from .dashboard import Dashboard
from .status_writer import StatusWriter


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main() -> int:
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Gmail Fetcher - Secure local Gmail archiving',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Run with dashboard interface
  gmail-fetcher --dash

  # Run in batch mode (no dashboard)
  gmail-fetcher

  # Download with custom query
  GMAIL_QUERY="from:someone@example.com" gmail-fetcher

  # Enable archiving
  ARCHIVE_ENABLED=true ARCHIVE_PASSWORD=secret gmail-fetcher --dash

Security Notes:
  - Credentials should be provided via Docker secrets or .env file
  - Never commit credentials.json or token.json to version control
  - Archives are encrypted with AES-256 when password is provided
  - Container runs as non-root user for additional security
        '''
    )

    parser.add_argument(
        '--dash',
        action='store_true',
        help='Enable terminal dashboard interface'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Headless mode: no dashboard, write status to file'
    )

    parser.add_argument(
        '--status-file',
        type=str,
        default='/tmp/gmail-fetcher-status.json',
        help='Path to status file for headless mode (default: /tmp/gmail-fetcher-status.json)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--no-auth-browser',
        action='store_true',
        help='Disable automatic browser opening for OAuth (use console link)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        config = Config.from_env()

        # Validate configuration
        errors = config.validate()
        if errors:
            for error in errors:
                if error.startswith("WARNING"):
                    logger.warning(error)
                else:
                    logger.error(error)

            # Check for fatal errors (non-warnings)
            fatal_errors = [e for e in errors if not e.startswith("WARNING")]
            if fatal_errors:
                logger.error("Configuration validation failed. Exiting.")
                return 1

        logger.info("Configuration loaded successfully")

        # Initialize Gmail client
        gmail_client = GmailClient(config)

        logger.info("Authenticating with Gmail API...")
        # Use manual flow if --no-auth-browser flag is set
        use_local_server = not args.no_auth_browser
        gmail_client.authenticate(use_local_server=use_local_server)

        # Initialize downloader
        downloader = EmailDownloader(config, gmail_client)

        # Initialize status writer for headless mode
        status_writer = None
        if args.headless:
            status_writer = StatusWriter(args.status_file)
            logger.info(f"Headless mode: status file at {args.status_file}")

            # Write initial status
            status_writer.write_status(
                'starting',
                gmail_client.get_stats(),
                {'query': config.query, 'output_dir': str(config.output_dir)}
            )

        # Progress callback for status updates
        def progress_callback(stats):
            if status_writer:
                status_writer.write_status('running', stats)

        # Run with dashboard, headless, or batch mode
        if args.dash and not args.headless:
            logger.info("Starting download with dashboard interface")
            dashboard = Dashboard(config)
            stats = dashboard.run_live(downloader.download_all)
        else:
            mode = "headless mode" if args.headless else "batch mode"
            logger.info(f"Starting download in {mode}")

            # Run download with progress callback if headless
            if args.headless:
                stats = downloader.download_all(progress_callback=progress_callback)
            else:
                stats = downloader.download_all()

            # Print summary
            logger.info("=" * 60)
            logger.info("DOWNLOAD COMPLETE")
            logger.info(f"Total emails scanned: {stats['total_emails']}")
            logger.info(f"Emails downloaded: {stats['downloaded_emails']}")
            logger.info(f"Attachments saved: {stats['total_attachments']}")
            logger.info(f"Total size: {stats['total_size_bytes'] / (1024*1024):.2f} MB")
            logger.info(f"Errors: {stats['errors']}")
            logger.info(f"Output directory: {config.output_dir}")
            logger.info("=" * 60)

        # Write final status for headless mode
        if status_writer:
            status_writer.write_status('complete', stats)

        # Create archive if enabled
        if config.archive_enabled:
            logger.info("Creating archive...")
            archiver = Archiver(config.output_dir.parent)

            archive_path = archiver.create_archive(
                config.output_dir,
                password=config.archive_password,
                archive_format='zip'
            )

            logger.info(f"Archive created: {archive_path}")

        logger.info("All operations completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
