"""
Clean up database entries by removing records that reference non-existent files.
"""

import os


class DatabaseCleaner:
    """
    A utility class that removes database records pointing to files that no
    longer exist.

    The cleaner checks each file path stored in the database against the actual
    filesystem and removes entries where the referenced files are missing.

    Example:
        cleaner = DatabaseCleaner(database_service)
        cleaner(db_table="my_documents")
    """

    def __init__(self, db_service):
        self.db_service = db_service

    def __call__(self, db_table: str = None) -> Exception:
        """
        Clean the database by removing entries for non-existent files.

        Checks all file paths stored in the database and removes entries where
        the referenced file no longer exists in the filesystem.

        Args:
            db_table: Optional table name to clean. If None, uses the default
            table
        """

        if db_table is not None:
            self.db_service.set_db_table(db_table)

        files_on_db, err = self.db_service.files_on_db()
        if err is not None:
            return err

        if len(files_on_db) == 0:
            return

        for file in files_on_db:
            if os.path.isfile(file):
                continue

            self.db_service.delete_documents_by_path(file)
