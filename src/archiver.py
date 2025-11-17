"""Archive emails into compressed format."""

import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Archiver:
    """Create compressed archives of downloaded emails."""

    def __init__(self, output_dir: Path):
        """Initialize archiver with output directory."""
        self.output_dir = output_dir

    def create_archive(
        self,
        source_dir: Path,
        password: Optional[str] = None,
        archive_format: str = 'zip'
    ) -> Path:
        """
        Create archive of email directory.

        Args:
            source_dir: Directory to archive
            password: Optional password for encryption
            archive_format: Archive format (zip, tar, gztar, bztar, xztar)

        Returns:
            Path to created archive
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"gmail_archive_{timestamp}"
        archive_path = self.output_dir / archive_name

        logger.info(f"Creating {archive_format} archive: {archive_name}")

        try:
            if archive_format == 'zip' and password:
                # For password-protected ZIP, we need pyminizip or py7zr
                # Using py7zr for better security
                return self._create_7z_archive(source_dir, archive_path, password)
            else:
                # Use shutil for standard archives
                final_path = shutil.make_archive(
                    str(archive_path),
                    archive_format,
                    source_dir
                )
                logger.info(f"Archive created: {final_path}")
                return Path(final_path)

        except Exception as e:
            logger.error(f"Error creating archive: {e}")
            raise

    def _create_7z_archive(
        self,
        source_dir: Path,
        archive_path: Path,
        password: str
    ) -> Path:
        """
        Create password-protected 7z archive.

        Args:
            source_dir: Directory to archive
            archive_path: Path for archive (without extension)
            password: Password for encryption

        Returns:
            Path to created archive
        """
        try:
            import py7zr

            final_path = archive_path.with_suffix('.7z')

            with py7zr.SevenZipFile(
                final_path,
                'w',
                password=password
            ) as archive:
                # Add all files from source directory
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        archive.write(file_path, arcname)

            logger.info(f"Encrypted 7z archive created: {final_path}")
            return final_path

        except ImportError:
            logger.warning("py7zr not available, falling back to unencrypted zip")
            final_path = shutil.make_archive(str(archive_path), 'zip', source_dir)
            return Path(final_path)
