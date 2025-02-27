import logging
import os
from typing import List

from fastapi import FastAPI, Request

from database import Supabase
from file_to_vec import FileToVec
from file_to_vec.processors import ChunkSummarizer
from services import DatabaseCleaner, DatabaseService, OllamaService

app = FastAPI()
db_service = DatabaseService()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def list_all_knowledge_files():
    """
    Lists all the file paths in the data directory and returns a list of file
    paths.
    """

    return [
        os.path.join(root, file)
        for root, _, files in os.walk("/data")
        for file in files
    ]


async def _process_file_paths(
    file_paths: List[str],
    db_table: str = None,
) -> dict:
    file_vectorizer = FileToVec(
        database_service=db_service,
    )

    processed_files = []
    unprocessed_files = []

    for file_path in file_paths:
        processed, err = await file_vectorizer(
            file_path=file_path,
            processor=ChunkSummarizer(
                llm_service=OllamaService(),
            ),
            ollama=OllamaService(),
            db_table=db_table,
        )

        if err is not None:
            return {
                "error": str(err),
            }

        if processed:
            processed_files.append(file_path)
            continue
        unprocessed_files.append(file_path)

    return {
        "message": "success",
        "processed_files": processed_files,
        "unprocessed_files": unprocessed_files,
    }


@app.get("/")
async def status():
    return "darkrag is running and ready to accept requests"


@app.post("/store/delete_files")
async def delete_files(request: Request):
    """
    Delete given list of file_paths from the database.
    """

    body = await request.json()
    file_paths = body.get("file_paths", [])
    for path in file_paths:
        db_service.delete_documents_by_path(f"/data/{path}")


@app.post("/store/process_all")
async def process_all(request: Request):
    """
    Process and embed all files in the knowledge base.
    """

    body = await request.json()
    db_table = body.get("db_table")

    file_paths = list_all_knowledge_files()
    return await _process_file_paths(
        file_paths=file_paths,
        db_table=db_table,
    )


@app.post("/store/process_files")
async def process_files(request: Request):
    """
    Process a given list of files.
    """

    body = await request.json()
    file_paths = [f"/data/{p}" for p in body.get("file_paths", [])]
    db_table = body.get("db_table")

    return await _process_file_paths(
        file_paths=file_paths,
        db_table=db_table,
    )


@app.post("/store/clean_database")
async def clean_database(request: Request):
    """
    Iterates over all files in the database and deletes any that are no longer
    in the knowledge base.
    """

    body = await request.json()
    db_table = body.get("db_table")

    cleaner = DatabaseCleaner(db_service=db_service)
    cleaner(db_table)

    return {
        "message": "success",
    }
