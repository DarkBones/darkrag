"""
DatabaseService module for interacting with the Supabase vector database.
"""

import hashlib
import logging
import os
from typing import List

import httpx

from database.supabase import Supabase
from settings import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service class to interact with the Supabase vector database.

    Attributes:
        db_table (str): The table in the database to query. Fetched from
        environment variables if not provided.
    """

    SUPABASE_CONNECTION_ERROR = (
        "Could not connect to Supabase. Check if Supabase is running and able "
        "to accept connections."
    )

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def __init__(self, db_table: str = None):
        self.logger = logger.getChild(self.__class__.__name__)
        self.db_table = db_table
        self.set_db_table(db_table)

        self.db = Supabase()

    def set_db_table(self, db_table: str = None):
        """
        Set the database table name for operations.

        If no table name is provided, falls back to the DEFAULT_DATABASE_TABLE
        environment variable. If neither is available, retains any existing
        table name.

        Args:
            db_table: Optional table name to use for database operations
        """

        if db_table is None:
            self.db_table = os.environ.get("DEFAULT_DATABASE_TABLE")
            return
        self.db_table = db_table

    def content_exists_in_database(self, content: str) -> bool:
        """
        Check if content already exists in the database using MD5 hash
        comparison.

        Bypasses the check and returns False if debug mode is enabled, allowing
        reprocessing of existing content for debugging purposes.

        Args:
            content: The text content to check for existence

        Returns:
            bool: True if the content exists in the database, False otherwise
        """

        debug_mode = settings.get("debug_mode", False)
        if debug_mode:
            return False

        try:
            md5 = self._hash_text(content)
            response = (
                self.db.table(self.db_table)
                .select("*")
                .eq(
                    "content_hash",
                    md5,
                )
            ).execute()
            return len(response.data) > 0
        except httpx.ConnectError:
            raise ConnectionError(self.SUPABASE_CONNECTION_ERROR)
        except Exception as e:
            raise e

    def insert(self, data: dict) -> bool:
        """
        Inserts a record into the Supabase table.

        This method blindly accepts a data dictionary and inserts it into the
        table. It assumes that all fields in the data are valid columns in the
        table.

        :param data: Dictionary containing the data to insert.
        :return: True if the insert was successful, False otherwise.
        """

        debug_mode = settings.get("debug_mode", False)
        if debug_mode:
            return True

        try:
            data["content_hash"] = self._hash_text(data["content"])
            response = self.db.table(self.db_table).insert(data).execute()

            ids = [record.get("id") for record in response.data if "id" in record]

            if len(ids) == 0:
                return False

            self.logger.info(f"Inserted data with ids = {ids}")
            return True
        except httpx.ConnectError:
            raise ConnectionError(self.SUPABASE_CONNECTION_ERROR)
        except Exception as e:
            raise e

    def delete_documents_by_path(self, path: str):
        """
        Deletes documents from the Supabase table where metadata->>'file_path'
        matches the provided path.

        :param path: The file path to match in the metadata.
        """

        debug_mode = settings.get("debug_mode", False)
        if debug_mode:
            self.logger.info(f"MOCK DELETE PATH: {path}")
            return

        try:
            response = (
                self.db.table(self.db_table)
                .delete()
                .filter("metadata->>file_path", "eq", path)
                .execute()
            )

            ids = [record.get("id") for record in response.data if "id" in record]

            if len(ids) == 0:
                return

            self.logger.info(f"Deleted {len(ids)} rows of data: {ids}")
        except httpx.ConnectError:
            raise ConnectionError(self.SUPABASE_CONNECTION_ERROR)
        except Exception as e:
            raise e

    def delete_document_by_id(self, row_id: int):
        """
        Delete rows by id.

        :param id: The row_id of the row to delete
        """

        debug_mode = settings.get("debug_mode", False)
        if debug_mode:
            self.logger.info(f"MOCK DELETE ID: {row_id}")
            return None

        try:
            response = (
                self.db.table(self.db_table)
                .delete()
                .filter("id", "eq", row_id)
                .execute()
            )

            self.logger.info(f"Deleted row with id: {id}")
            return response
        except httpx.ConnectError:
            raise ConnectionError(self.SUPABASE_CONNECTION_ERROR)
        except Exception as e:
            raise e

    def files_on_db(self) -> List[str]:
        """
        Returns a list of unique file paths found in the metadata of all the
        rows.
        """

        try:
            response = (
                self.db.table(self.db_table)
                .select("id", "metadata->>file_path")
                .execute()
            )

            paths = set()
            for row in response.data:
                path = row.get("file_path")
                if path is None:
                    # If there's no path in the metadata, just delete the row
                    self.delete_document_by_id(row.get("id"))

                paths.add(path)

            return list(paths)
        except httpx.ConnectError:
            raise ConnectionError(self.SUPABASE_CONNECTION_ERROR)
        except Exception as e:
            raise e

    def get_hashes_by_path(self, path: str) -> List[dict]:
        """
        Returns a list of md5 hashes associated with a given path.
        """

        try:
            response = (
                self.db.table(self.db_table)
                .select("id, content_hash")
                .filter("metadata->>file_path", "eq", path)
                .execute()
            )
            return response.data
        except httpx.ConnectError:
            raise ConnectionError(self.SUPABASE_CONNECTION_ERROR)
        except Exception as e:
            raise e

    def delete_by_content_hash(self, path: str, content_hash: str):
        """
        Deletes rows by a given a file path and content hash combination.
        """

        debug_mode = settings.get("debug_mode", False)
        if debug_mode:
            self.logger.info(f"MOCK DELETE HASH: {content_hash}")
            return []

        try:
            response = (
                self.db.table(self.db_table)
                .delete()
                .filter("metadata->>file_path", "eq", path)
                .eq("content_hash", content_hash)
                .execute()
            )
        except httpx.ConnectError:
            raise ConnectionError(self.SUPABASE_CONNECTION_ERROR)
        except Exception as e:
            raise e
            return response.data
