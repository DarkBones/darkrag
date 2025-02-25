"""
OllamaService module for interacting with the Ollama API.

This module provides an interface to interact with the Ollama API,
allowing for chat operations and retrieval of text embeddings using asynchronous
HTTP requests.
"""

import logging
import os
from typing import List

import httpx

from settings import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Service class to interact with the Ollama API for chat and embedding
    functionalities.

    Attributes:
        ollama_url (str): The base URL for the Ollama API. Fetched from
                          environment variables if not provided.
    """

    OLLAMA_CONNECTION_ERROR = (
        "Could not connect to ollama. Check if ollama is running and able to "
        "accept connections at {{url}}"
    )

    def __init__(self, ollama_url: str = None):
        self.logger = logger.getChild(self.__class__.__name__)
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_URL")

    def base_url(self) -> str:
        """
        Returns the base URL of the Ollama API.

        Returns:
            str: The base URL of the Ollama API.
        """

        return self.ollama_url

    async def chat(
        self,
        messages: List[dict],
        model: str = None,
    ) -> str:
        """
        Sends a list of messages to the Ollama API and retrieves the chat
        response.

        Args:
            messages (List[dict]): A list of message dictionaries to send to the
                                   API.
            model (str, optional): The model to use for the chat. If None, it
                                   will use the 'DEFAULT_MODEL' from environment
                                   variables.
            debug_mode (bool, optional): If True, the payload is printed and a
                                         placeholder response is returned.

        Returns:
            str: The content of the API's chat response.

        Raises:
            ValueError: If the API call fails or returns a non-200 status code.
        """

        debug_mode = settings.get("debug_mode", False)

        if model is None:
            model = os.environ.get("DEFAULT_MODEL")

        url = f"{self.ollama_url}/api/chat"

        data = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        if debug_mode:
            print(data)
            return "Debug mode on. Placeholder response"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
                response = await client.post(url, json=data)
        except httpx.ConnectError as e:
            raise ConnectionError(
                self.OLLAMA_CONNECTION_ERROR.replace("{{url}}", self.ollama_url)
            )

        if response.status_code == 200:
            return response.json()["message"]["content"]

        err = f"{response.status_code}, {response.text}"
        self.logger.error(err)

        raise ValueError(err)

    async def get_embeddings(self, text: str) -> List[float]:
        """
        Retrieves text embeddings for a given input string from the Ollama API.

        Args:
            text (str): The input text for which embeddings are to be retrieved.

        Returns:
            List[float]: A list of floats representing the text embeddings.

        Raises:
            ValueError: If the API call fails or returns a non-200 status code.
        """

        model = os.environ.get("EMBEDDING_MODEL")
        url = f"{self.ollama_url}/api/embed"
        data = {
            "model": model,
            "input": text,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(url, json=data)

        try:
            if response.status_code == 200:
                return response.json()["embeddings"][0]
        except httpx.ConnectError as e:
            raise ConnectionError(
                self.OLLAMA_CONNECTION_ERROR.replace("{{url}}", self.ollama_url)
            )

        err = f"{response.status_code}, {response.text}"
        self.logger.error(err)

        raise ValueError(err)
