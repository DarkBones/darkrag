"""
A utility module for extracting text content from files with encoding fallback
and error handling.
"""

import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    A class for reading text files with automatic encoding fallback and
    comprehensive error handling.

    The class attempts to read files using UTF-8 encoding first, falling back to
    ISO-8859-1 if UTF-8 fails. All errors are logged and handled gracefully,
    returning an empty string in case of failures.
    """

    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)

    @classmethod
    def extract(cls, file_path: Union[str, Path]) -> str:
        """
        Extract text content from a file with automatic encoding detection.

        Args:
            file_path (Union[str, Path]): Path to the file to read

        Returns:
            str: The contents of the file, or empty string if reading fails
        """

        return cls()._extract_impl(file_path)

    def _extract_impl(self, file_path: Union[str, Path]) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            self.logger.warning(
                f"Could not read {file_path} as UTF-8, trying ISO-8859-1"
            )
            try:
                with open(file_path, "r", encoding="ISO-8859-1") as file:
                    return file.read()
            except IOError as e:
                self.logger.error(f"Could not read file {file_path}: {e}")
                return ""
        except FileNotFoundError:
            self.logger.error(f"File not found - {file_path}")
            return ""
        except IOError as e:
            self.logger.error(f"Unexpected error reading {file_path}: {e}")
            return ""
