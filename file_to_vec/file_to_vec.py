"""
A module for processing files into vector embeddings for storage in a vector
database. Supports different file types with customizable splitting strategies
and processing pipelines.
"""

import hashlib
import logging

from file_to_vec import FileToChunks

logger = logging.getLogger(__name__)


class UnsupportedFileTypeError(ValueError):
    """
    Raised when attempting to process a file type that doesn't have a
    registered splitter.
    """


class FailedToProcessFileError(Exception):
    """
    Raised when the file processing pipeline encounters an unrecoverable error.
    """


class FileToVec:
    """
    Processes files into vector embeddings for storage in a vector database.

    The class handles file content extraction, chunk splitting, embedding
    generation, and database operations. It supports incremental updates by
    tracking content hashes and only processing new or changed content.

    Example:
        file_to_vec = FileToVec(database_service)
        await file_to_vec("path/to/file.md", processor, db, ollama)
    """

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def __init__(self, database_service):
        self.logger = logger.getChild(self.__class__.__name__)
        self.database_service = database_service
        self.file_to_chunks = FileToChunks(
            database_service=database_service,
        )

    async def __call__(
        self,
        file_path: str,
        processor,
        ollama,
        db_table: str = None,
    ) -> [bool, Exception]:
        """
        Process a file and store its vector embeddings in the database.

        Args:
            file_path: Path to the file to process
            processor: Chunk processor instance for text processing
            ollama: Ollama client for generating embeddings
            db_table: Name of the database table to use

        Returns:
            bool: True if file was successfully processed, False otherwise

        Raises:
            FailedToProcessFileError: If unable to process or store the file
                                      chunks
            UnsupportedFileTypeError: If the file type is not supported
        """

        if db_table is not None:
            self.database_service.set_db_table(db_table)

        chunks, err = await self.file_to_chunks.process(file_path, processor)
        if err is not None:
            return None, err

        if chunks is None or chunks is False:
            return False, None

        for chunk in chunks:
            chunk["embedding"] = await ollama.get_embeddings(
                chunk["full_context"],
            )
            chunk["metadata"]["file_path"] = file_path

            processed, err = self.database_service.insert(chunk)
            if not processed:
                raise FailedToProcessFileError(f"Failed to process {file_path}")

        return True, None
