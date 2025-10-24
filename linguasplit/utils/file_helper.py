"""
File operation utilities for LinguaSplit.
Handles file I/O, path operations, and file validation.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
import hashlib


class FileHelper:
    """
    Utilities for file operations.

    Features:
    - File validation
    - Safe file operations
    - Path handling
    - File info extraction
    """

    SUPPORTED_FORMATS = {
        'pdf': ['.pdf'],
        'text': ['.txt', '.md', '.markdown'],
        'json': ['.json'],
    }

    @staticmethod
    def is_supported_file(file_path: str, file_type: Optional[str] = None) -> bool:
        """
        Check if file is supported.

        Args:
            file_path: Path to file
            file_type: Optional specific file type to check (pdf, text, json)

        Returns:
            True if supported
        """
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            return False

        extension = path.suffix.lower()

        if file_type:
            # Check specific type
            if file_type in FileHelper.SUPPORTED_FORMATS:
                return extension in FileHelper.SUPPORTED_FORMATS[file_type]
            return False

        # Check all supported types
        all_extensions = []
        for extensions in FileHelper.SUPPORTED_FORMATS.values():
            all_extensions.extend(extensions)

        return extension in all_extensions

    @staticmethod
    def is_pdf(file_path: str) -> bool:
        """
        Check if file is a PDF.

        Args:
            file_path: Path to file

        Returns:
            True if PDF
        """
        return FileHelper.is_supported_file(file_path, 'pdf')

    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        Ensure directory exists, create if necessary.

        Args:
            directory: Directory path

        Returns:
            True if successful
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False

    @staticmethod
    def safe_filename(filename: str) -> str:
        """
        Create safe filename by removing invalid characters.

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe = filename

        for char in invalid_chars:
            safe = safe.replace(char, '_')

        # Remove leading/trailing spaces and dots
        safe = safe.strip('. ')

        # Ensure not empty
        if not safe:
            safe = 'unnamed'

        return safe

    @staticmethod
    def get_unique_filename(directory: str, filename: str) -> str:
        """
        Get unique filename by adding number suffix if file exists.

        Args:
            directory: Directory path
            filename: Desired filename

        Returns:
            Unique filename
        """
        path = Path(directory) / filename

        if not path.exists():
            return filename

        # Split name and extension
        stem = path.stem
        suffix = path.suffix

        # Add number suffix
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = Path(directory) / new_name

            if not new_path.exists():
                return new_name

            counter += 1

            # Safety limit
            if counter > 9999:
                return f"{stem}_{hashlib.md5(str(counter).encode()).hexdigest()[:8]}{suffix}"

    @staticmethod
    def get_output_filename(input_path: str, output_format: str = 'md') -> str:
        """
        Generate output filename from input path.

        Args:
            input_path: Input file path
            output_format: Output format extension (default: md)

        Returns:
            Output filename
        """
        path = Path(input_path)
        stem = path.stem

        # Clean the stem
        safe_stem = FileHelper.safe_filename(stem)

        # Ensure output_format has leading dot
        if not output_format.startswith('.'):
            output_format = f'.{output_format}'

        return f"{safe_stem}{output_format}"

    @staticmethod
    def read_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        Read text file safely.

        Args:
            file_path: Path to file
            encoding: File encoding

        Returns:
            File contents or None on error
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    @staticmethod
    def write_text_file(
        file_path: str,
        content: str,
        encoding: str = 'utf-8',
        overwrite: bool = True
    ) -> bool:
        """
        Write text file safely.

        Args:
            file_path: Path to file
            content: Content to write
            encoding: File encoding
            overwrite: Whether to overwrite existing file

        Returns:
            True if successful
        """
        try:
            path = Path(file_path)

            # Check if file exists and overwrite is False
            if path.exists() and not overwrite:
                print(f"File already exists: {file_path}")
                return False

            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False

    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes or None on error
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return None

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} PB"

    @staticmethod
    def get_file_info(file_path: str) -> Optional[dict]:
        """
        Get file information.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file info or None on error
        """
        try:
            path = Path(file_path)
            stat = path.stat()

            return {
                'path': str(path.absolute()),
                'name': path.name,
                'stem': path.stem,
                'extension': path.suffix,
                'size': stat.st_size,
                'size_formatted': FileHelper.format_file_size(stat.st_size),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
            }

        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return None

    @staticmethod
    def copy_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """
        Copy file safely.

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing file

        Returns:
            True if successful
        """
        try:
            src_path = Path(source)
            dst_path = Path(destination)

            if not src_path.exists():
                print(f"Source file not found: {source}")
                return False

            if dst_path.exists() and not overwrite:
                print(f"Destination file already exists: {destination}")
                return False

            # Ensure destination directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source, destination)
            return True

        except Exception as e:
            print(f"Error copying file from {source} to {destination}: {e}")
            return False

    @staticmethod
    def move_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """
        Move file safely.

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing file

        Returns:
            True if successful
        """
        try:
            src_path = Path(source)
            dst_path = Path(destination)

            if not src_path.exists():
                print(f"Source file not found: {source}")
                return False

            if dst_path.exists() and not overwrite:
                print(f"Destination file already exists: {destination}")
                return False

            # Ensure destination directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(source, destination)
            return True

        except Exception as e:
            print(f"Error moving file from {source} to {destination}: {e}")
            return False

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete file safely.

        Args:
            file_path: Path to file

        Returns:
            True if successful
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return True  # Already deleted

            path.unlink()
            return True

        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False

    @staticmethod
    def list_files(
        directory: str,
        pattern: str = '*',
        recursive: bool = False
    ) -> List[str]:
        """
        List files in directory.

        Args:
            directory: Directory path
            pattern: File pattern (e.g., '*.pdf')
            recursive: Whether to search recursively

        Returns:
            List of file paths
        """
        try:
            path = Path(directory)

            if not path.exists() or not path.is_dir():
                return []

            if recursive:
                files = path.rglob(pattern)
            else:
                files = path.glob(pattern)

            # Return only files (not directories)
            return [str(f) for f in files if f.is_file()]

        except Exception as e:
            print(f"Error listing files in {directory}: {e}")
            return []

    @staticmethod
    def get_relative_path(file_path: str, base_path: str) -> Optional[str]:
        """
        Get relative path from base path.

        Args:
            file_path: File path
            base_path: Base path

        Returns:
            Relative path or None on error
        """
        try:
            file_path = Path(file_path).absolute()
            base_path = Path(base_path).absolute()
            return str(file_path.relative_to(base_path))
        except Exception:
            return None

    @staticmethod
    def compute_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """
        Compute file hash.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm (md5, sha1, sha256)

        Returns:
            Hash hex string or None on error
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return None

            # Create hash object
            if algorithm == 'md5':
                hasher = hashlib.md5()
            elif algorithm == 'sha1':
                hasher = hashlib.sha1()
            elif algorithm == 'sha256':
                hasher = hashlib.sha256()
            else:
                return None

            # Read file in chunks
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)

            return hasher.hexdigest()

        except Exception as e:
            print(f"Error computing hash for {file_path}: {e}")
            return None

    @staticmethod
    def validate_path(path: str) -> Tuple[bool, str]:
        """
        Validate file path.

        Args:
            path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path:
            return (False, "Path is empty")

        try:
            path_obj = Path(path)

            # Check for invalid characters (platform-specific)
            if os.name == 'nt':  # Windows
                invalid = '<>:"|?*'
                for char in invalid:
                    if char in str(path_obj):
                        return (False, f"Path contains invalid character: {char}")

            # Check path length
            if len(str(path_obj)) > 255:
                return (False, "Path is too long")

            return (True, "")

        except Exception as e:
            return (False, f"Invalid path: {e}")
