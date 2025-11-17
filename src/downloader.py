"""Email downloader for saving Gmail messages to disk."""

import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import email
from email.message import Message

from .config import Config
from .gmail_client import GmailClient, parse_email_date, sanitize_filename

logger = logging.getLogger(__name__)


class EmailDownloader:
    """Downloads and saves Gmail messages to local filesystem."""

    def __init__(self, config: Config, gmail_client: GmailClient):
        """Initialize downloader with config and Gmail client."""
        self.config = config
        self.client = gmail_client
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def download_all(
        self,
        progress_callback: Optional[Callable[[dict], None]] = None
    ) -> dict:
        """
        Download all emails matching the query.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Download statistics
        """
        logger.info(f"Starting download with query: {self.config.query}")
        logger.info(f"Output directory: {self.config.output_dir}")

        for msg_metadata in self.client.get_messages():
            try:
                # Fetch full message
                message = self.client.get_message_detail(msg_metadata['id'])

                # Save the message
                self._save_message(message)

                self.client.increment_stat('downloaded_emails')

                # Optional progress callback
                if progress_callback:
                    progress_callback(self.client.get_stats())

                # Optional deletion
                if self.config.delete_after_download:
                    self.client.delete_message(msg_metadata['id'])

            except Exception as e:
                logger.error(f"Error processing message {msg_metadata['id']}: {e}")
                self.client.increment_stat('errors')

        stats = self.client.get_stats()
        logger.info(f"Download complete: {stats}")
        return stats

    def _save_message(self, message: dict) -> None:
        """
        Save a single message to disk.

        Args:
            message: Full Gmail message object
        """
        msg_id = message['id']
        headers = {h['name']: h['value'] for h in message['payload']['headers']}

        # Extract metadata
        subject = headers.get('Subject', 'No Subject')
        date_str = headers.get('Date', '')
        from_addr = headers.get('From', 'Unknown')

        # Parse date and create directory structure
        date = parse_email_date(date_str)
        date_path = self.config.output_dir / str(date.year) / f"{date.month:02d}" / f"{date.day:02d}"

        # Create safe directory name (limit to 50 to account for multi-byte UTF-8 chars)
        safe_subject = sanitize_filename(subject, max_length=50)
        msg_dir = date_path / f"{date.strftime('%H%M%S')}_{safe_subject}_{msg_id[:8]}"
        msg_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata = {
            'id': msg_id,
            'threadId': message.get('threadId'),
            'subject': subject,
            'from': from_addr,
            'to': headers.get('To', ''),
            'cc': headers.get('Cc', ''),
            'date': date_str,
            'labels': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
        }

        with open(msg_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Process message parts (body, attachments)
        payload = message['payload']
        self._process_parts(payload, msg_dir, msg_id)

        logger.debug(f"Saved message: {subject[:50]} ({msg_id})")

    def _process_parts(self, payload: dict, msg_dir: Path, msg_id: str) -> None:
        """
        Recursively process message parts (body, attachments).

        Args:
            payload: Message payload
            msg_dir: Directory to save parts
            msg_id: Message ID for API calls
        """
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                self._process_parts(part, msg_dir, msg_id)
        else:
            # Single part
            self._save_part(payload, msg_dir, msg_id)

    def _save_part(self, part: dict, msg_dir: Path, msg_id: str) -> None:
        """
        Save a single message part.

        Args:
            part: Message part
            msg_dir: Directory to save to
            msg_id: Message ID
        """
        mime_type = part.get('mimeType', '')
        filename = part.get('filename', '')
        body = part.get('body', {})

        # Handle attachments
        if filename and self.config.include_attachments:
            self._save_attachment(part, msg_dir, msg_id)
            return

        # Handle text/html content
        if mime_type in ['text/plain', 'text/html']:
            data = body.get('data', '')
            if data:
                content = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

                # Save as appropriate file type
                ext = 'txt' if mime_type == 'text/plain' else 'html'
                filename = f"body.{ext}"

                # If both exist, number them
                save_path = msg_dir / filename
                counter = 1
                while save_path.exists():
                    filename = f"body_{counter}.{ext}"
                    save_path = msg_dir / filename
                    counter += 1

                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def _save_attachment(self, part: dict, msg_dir: Path, msg_id: str) -> None:
        """
        Save an email attachment.

        Args:
            part: Message part containing attachment
            msg_dir: Directory to save to
            msg_id: Message ID
        """
        filename = part.get('filename', 'attachment')
        filename = sanitize_filename(filename)

        attachment_id = part['body'].get('attachmentId')
        size = part['body'].get('size', 0)

        if not attachment_id:
            # Inline attachment
            data = part['body'].get('data', '')
            if data:
                content = base64.urlsafe_b64decode(data)
        else:
            # Download attachment from API with rate limiting
            try:
                request = self.client.service.users().messages().attachments().get(
                    userId='me',
                    messageId=msg_id,
                    id=attachment_id
                )
                attachment = self.client._execute_with_backoff(
                    request,
                    f"get attachment {filename[:20]}"
                )

                data = attachment.get('data', '')
                content = base64.urlsafe_b64decode(data)
            except Exception as e:
                logger.error(f"Error downloading attachment {filename}: {e}")
                self.client.increment_stat('errors')
                return

        # Save attachment
        attachments_dir = msg_dir / 'attachments'
        attachments_dir.mkdir(exist_ok=True)

        save_path = attachments_dir / filename
        counter = 1
        while save_path.exists():
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            new_filename = f"{name}_{counter}.{ext}" if ext else f"{filename}_{counter}"
            save_path = attachments_dir / new_filename
            counter += 1

        with open(save_path, 'wb') as f:
            f.write(content)

        self.client.increment_stat('total_attachments')
        self.client.increment_stat('total_size_bytes', size)

        logger.debug(f"Saved attachment: {filename} ({size} bytes)")
