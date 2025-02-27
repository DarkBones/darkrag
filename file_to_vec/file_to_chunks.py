"""
File chunking module that handles content extraction and splitting for vector
database storage.

This module provides functionality for:
- Extracting content from supported file types
- Splitting content into processable chunks
- Managing chunk deduplication through hash tracking
- Handling incremental updates by identifying new or modified content
- Integrating with database services for persistence

The primary class FileToChunks manages the chunking pipeline while handling
edge cases like empty files, unsupported file types, and content deduplication.

Typical usage:
    chunker = FileToChunks(database_service)
    chunks = await chunker.process("path/to/file.md", processor)
"""

import hashlib
import logging
import os
from typing import Callable, List, Optional, Tuple

from file_to_vec import ContentExtractor
from file_to_vec.splitters import MarkdownSplitter
from settings import settings

logger = logging.getLogger(__name__)

class UnsupportedFileTypeError(ValueError):
    """
    Raised when attempting to process a file type that doesn't have a
    registered splitter.
    """


class FileToChunks:
    """
    Handles the extraction and chunking of file content with database
    integration for deduplication and incremental processing.
    """

    def __init__(
        self,
        database_service,
    ):
        self.logger = logger.getChild(self.__class__.__name__)
        self.database_service = database_service

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    async def process(
        self,
        file_path: str,
        processor,
    ) -> [List[dict], None]:
        """
        Process a file into chunks with deduplication.
        """

        content, splitter = self._prepare_file_content(file_path)
        if not content or len(content) <= 5:
            return [], None

        chunks, err = self._generate_chunks(file_path, splitter, content)
        if err is not None:
            return None, err

        if not chunks:
            return [], None

        chunks_to_process = self._filter_chunks_for_processing(chunks)
        if not chunks_to_process:
            return [], None

        return await processor.process_chunks(
            chunks,
            chunks_to_process,
            self._is_written_by_me(file_path),
        )

    def _prepare_file_content(
        self,
        file_path: str,
    ) -> Tuple[str, Optional[Callable]]:
        try:
            file_type = file_path.split(".")[-1]
            splitter = self._get_splitter(file_type)
            content = ContentExtractor.extract(file_path)
            return content, splitter
        except UnsupportedFileTypeError as e:
            self.logger.error(
                "Failed to process %s: %s",
                file_path,
                str(e),
            )
            return "", None

    def _generate_chunks(
        self,
        file_path: str,
        splitter: Callable,
        content: str,
    ) -> [List[dict], Exception]:
        chunks = splitter(content)
        chunk_hashes = {self._hash_text(chunk["content"]) for chunk in chunks}

        existing_chunk_hashes, err = self.database_service.get_hashes_by_path(
            file_path,
        )
        if err is not None:
            return None, err

        for ech in existing_chunk_hashes:
            if ech["content_hash"] not in chunk_hashes:
                self.database_service.delete_by_content_hash(
                    file_path,
                    ech["content_hash"],
                )

        return chunks, None

    def _filter_chunks_for_processing(
        self,
        chunks: List[dict],
    ) -> List[dict]:
        chunks_not_in_db = []
        for chunk in chunks:
            persisted, err = self.database_service.content_exists_in_database(
                chunk["content"],
            )
            if persisted:
                continue
            chunks_not_in_db.append(chunk)

        return chunks_not_in_db

    @staticmethod
    def _is_written_by_me(file_path: str) -> bool:
        return os.environ.get("AUTHOR_NAME") in file_path.split("/")

    @staticmethod
    def _get_splitter(file_type: str) -> Callable:
        match file_type:
            case "md":
                return MarkdownSplitter()
            case _:
                raise UnsupportedFileTypeError(
                    f"File type '{file_type}' is not supported.",
                )
