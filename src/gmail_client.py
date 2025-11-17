"""Gmail API client for fetching emails."""

import base64
import email
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import Config

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_second: float = 10.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second (default: 10)
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.last_request_time = 0.0

    def wait_if_needed(self) -> None:
        """Wait if necessary to maintain rate limit."""
        if self.min_interval <= 0:
            return  # Rate limiting disabled

        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self, config: Config):
        """Initialize Gmail client with configuration."""
        self.config = config
        self.service = None
        self.rate_limiter = RateLimiter(config.requests_per_second)
        self._stats = {
            'total_emails': 0,
            'downloaded_emails': 0,
            'total_attachments': 0,
            'total_size_bytes': 0,
            'errors': 0,
            'rate_limit_hits': 0,
            'retries': 0
        }

    def authenticate(self, use_local_server: bool = True) -> None:
        """
        Authenticate with Gmail API using OAuth2.

        Args:
            use_local_server: If True, use local server for OAuth (default).
                             If False, use console-based manual flow.
        """
        creds = None

        # Token file stores the user's access and refresh tokens
        if self.config.token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.config.token_path), SCOPES
            )

        # If there are no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Starting OAuth2 flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.config.credentials_path), SCOPES
                )

                if use_local_server:
                    # Run local server for OAuth flow (default)
                    creds = flow.run_local_server(port=0)
                else:
                    # Manual console flow - use localhost with instructions
                    print("\n" + "="*70)
                    print("📧 GMAIL FETCHER - OAUTH SETUP (Manual Mode)")
                    print("="*70)
                    print("\nThis is a ONE-TIME setup to authorize Gmail access.")
                    print("Your credentials stay LOCAL - nothing is sent to third parties.\n")

                    print("⚠️  IMPORTANT: For manual mode to work over SSH:")
                    print("-" * 70)
                    print("\nOption 1: Run locally instead (recommended)")
                    print("  1. Exit this SSH session")
                    print("  2. Run locally on a machine with a browser")
                    print("  3. Copy data/token.json to your server\n")

                    print("Option 2: SSH Port Forward (if remote)")
                    print("  1. Exit this script (Ctrl+C)")
                    print("  2. Reconnect with: ssh -L 8080:localhost:8080 user@host")
                    print("  3. Run: python gmail-fetcher.py (no --no-auth-browser flag)")
                    print("  4. Browser will open on your LOCAL machine\n")

                    print("Option 3: Continue with URL copy/paste (may not work)")
                    print("-" * 70 + "\n")

                    choice = input("Continue anyway? [y/N] ").strip().lower()
                    if choice != 'y':
                        print("\nExiting. Please use Option 1 or 2 above.\n")
                        raise SystemExit(0)

                    # Try localhost redirect (works for Desktop apps)
                    print("\n" + "="*70)
                    print("Attempting OAuth with localhost redirect...")
                    print("="*70 + "\n")

                    # Use run_local_server but with clear messaging
                    try:
                        print("A URL will be displayed. Copy it and paste in your browser.")
                        print("After authorizing, you'll be redirected to localhost.")
                        print("Copy the 'code=' parameter from the URL and paste it below.\n")

                        # Get the auth URL
                        flow.redirect_uri = 'http://localhost:8080/'
                        auth_url, state = flow.authorization_url(
                            access_type='offline',
                            prompt='consent'
                        )

                        print("Authorization URL:")
                        print("-" * 70)
                        print(f"\n{auth_url}\n")
                        print("-" * 70)
                        print("\nAfter authorizing, you'll see a URL like:")
                        print("  http://localhost:8080/?code=4/0AbC...&scope=...")
                        print("\nCopy ONLY the code value (after 'code='):\n")

                        code = input("Paste the code here: ").strip()

                        # Extract code if they pasted the whole URL
                        if 'code=' in code:
                            import urllib.parse
                            parsed = urllib.parse.urlparse(code)
                            params = urllib.parse.parse_qs(parsed.query)
                            code = params.get('code', [code])[0]

                        print("\nAuthenticating...")
                        flow.fetch_token(code=code)
                        creds = flow.credentials

                        print("\n" + "="*70)
                        print("✓ Authentication successful!")
                        print("="*70)
                        print(f"\nToken saved to: {self.config.token_path}")
                        print("You won't need to do this again unless you revoke access.\n")

                    except Exception as e:
                        print("\n" + "="*70)
                        print("✗ Authentication failed!")
                        print("="*70)
                        print(f"\nError: {e}\n")
                        print("This manual method is tricky. Please use Option 1 or 2 instead:")
                        print("  1. Run locally and copy token.json")
                        print("  2. Use SSH port forwarding\n")
                        raise

            # Save credentials for next run
            self.config.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.token_path, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"Credentials saved to {self.config.token_path}")

        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully authenticated with Gmail API")

    def _execute_with_backoff(self, request, operation_name: str = "API call"):
        """
        Execute API request with exponential backoff on rate limit errors.

        Args:
            request: Google API request object
            operation_name: Description of operation for logging

        Returns:
            API response

        Raises:
            HttpError: If max retries exceeded or non-retryable error
        """
        max_retries = self.config.max_retries
        base_delay = 1.0  # Start with 1 second

        for attempt in range(max_retries + 1):
            try:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()

                # Execute request
                return request.execute()

            except HttpError as error:
                # Check if it's a rate limit error (429) or server error (500, 503)
                if error.resp.status in [429, 500, 503]:
                    if attempt < max_retries:
                        # Calculate exponential backoff delay
                        delay = base_delay * (2 ** attempt)

                        # Add jitter to prevent thundering herd
                        import random
                        delay = delay * (0.5 + random.random())

                        if error.resp.status == 429:
                            self._stats['rate_limit_hits'] += 1
                            logger.warning(
                                f"Rate limit hit on {operation_name}. "
                                f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                            )
                        else:
                            logger.warning(
                                f"Server error {error.resp.status} on {operation_name}. "
                                f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                            )

                        self._stats['retries'] += 1
                        time.sleep(delay)
                        continue

                # Non-retryable error or max retries exceeded
                raise

    def get_messages(self) -> Iterator[dict]:
        """
        Fetch messages from Gmail using the configured query.

        Yields:
            Message metadata dictionaries
        """
        try:
            page_token = None
            count = 0

            while True:
                # List messages with backoff
                request = self.service.users().messages().list(
                    userId='me',
                    q=self.config.query,
                    maxResults=500,  # Max per page
                    pageToken=page_token
                )

                results = self._execute_with_backoff(request, "list messages")
                messages = results.get('messages', [])

                if not messages:
                    break

                for msg in messages:
                    if self.config.max_results and count >= self.config.max_results:
                        logger.info(f"Reached max_results limit of {self.config.max_results}")
                        return

                    yield msg
                    count += 1

                self._stats['total_emails'] = count
                page_token = results.get('nextPageToken')

                if not page_token:
                    break

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            self._stats['errors'] += 1
            raise

    def get_message_detail(self, msg_id: str) -> dict:
        """
        Fetch full message details including body and attachments.

        Args:
            msg_id: Gmail message ID

        Returns:
            Full message object
        """
        try:
            request = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            )
            message = self._execute_with_backoff(request, f"get message {msg_id[:8]}")
            return message
        except HttpError as error:
            logger.error(f"Error fetching message {msg_id}: {error}")
            self._stats['errors'] += 1
            raise

    def delete_message(self, msg_id: str) -> None:
        """
        Permanently delete a message from Gmail.

        Args:
            msg_id: Gmail message ID
        """
        try:
            request = self.service.users().messages().delete(
                userId='me',
                id=msg_id
            )
            self._execute_with_backoff(request, f"delete message {msg_id[:8]}")
            logger.debug(f"Deleted message {msg_id}")
        except HttpError as error:
            logger.error(f"Error deleting message {msg_id}: {error}")
            self._stats['errors'] += 1
            raise

    def get_stats(self) -> dict:
        """Get download statistics."""
        return self._stats.copy()

    def update_stat(self, key: str, value: int) -> None:
        """Update a statistic value."""
        self._stats[key] = value

    def increment_stat(self, key: str, amount: int = 1) -> None:
        """Increment a statistic counter."""
        self._stats[key] = self._stats.get(key, 0) + amount


def parse_email_date(date_str: str) -> datetime:
    """
    Parse email date header into datetime object.

    Args:
        date_str: Date string from email header

    Returns:
        Parsed datetime object
    """
    try:
        # Parse the date using email utils
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception as e:
        logger.warning(f"Could not parse date '{date_str}': {e}")
        # Fallback to current time
        return datetime.now()


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize filename to be safe for filesystem.

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*\x00'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')

    # Trim to max length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        name = name[:max_length - len(ext) - 3] + '...'
        filename = name + ext

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    return filename or 'unnamed'
