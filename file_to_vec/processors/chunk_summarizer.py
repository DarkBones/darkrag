import math
import os
from typing import List


class ChunkSummarizer:
    """
    A utility class for summarizing document chunks using an LLM service.

    This class provides functionality to generate summaries for individual
    chunks of text and overall file summaries. It handles special cases where
    the document was written by the same person as the one running this app, 
    ensuring proper attribution in the summaries.

    The summarization process includes:
    1. Creating a file-level summary based on the first and last chunks
    2. Processing individual chunks with context from the file summary
    3. Creating comprehensive chunk representations with summaries and original
        content
    """

    SUMMARIZE_CHUNK_PROMPT = (
        "You are an AI that extracts summaries from document chunks.\n"
        "Create a concise summary of the main points in this chunk. Keep it "
        "concise but informative."
    )

    SUMMARIZE_FILE_PROMPT = (
        "You are an AI that extracts summaries from document chunks.\n"
        "The following is the beginning + the end of a file. Create a consise "
        "summary of what this file is about. It should be no longer than two "
        "short sentences."
    )

    WRITTEN_BY_ME_PROMPT = (
        "IMPORTANT INFORMATION: This content was written by "
        "{{full_name}}. Any mentions of 'I', 'me', or 'my' refer directly to "
        "{{pronoun_two}}self. When creating the summary, ALWAYS replace first-person "
        "references with {{full_name}}'s name to ensure clarity. DO NOT use "
        "generic terms like 'the author' or 'the engineer'. The summary must "
        "make it abundantly clear that the content is about {{full_name}}."
    )

    FILE_SUMMARY = (
        "File summary (for background only):\n"
        "<file_summary>\n{{file_summary}}\n</file_summary>\n"
        "Now, summarize the chunk below, focussing ONLY on the chunk's unique "
        "content, using the file summary only for additional context."
    )

    CHUNKS_TO_USE_FOR_FILE_SUMMARY = 4

    def __init__(self, llm_service, model_name = None):
        self.model_name = model_name
        if model_name is None:
            self.model_name = os.environ.get("SUMMARIZING_MODEL")

        self.llm_service = llm_service

    def _parse_written_by_me_prompt(self) -> str:
        prompt = self.WRITTEN_BY_ME_PROMPT
        prompt = prompt.replace(
            "{{full_name}}",
            os.environ.get("AUTHOR_FULL_NAME"),
        )
        prompt = prompt.replace(
            "{{pronoun_two}}",
            os.environ.get("AUTHOR_PRONOUN_TWO"),
        )
        return prompt

    async def process_chunks(
        self,
        all_chunks,
        chunks_to_process: List[dict],
        written_by_me: bool,
    ) -> [List[dict], Exception]:
        """
        Process a list of document chunks to generate summaries.

        This method takes a set of text chunks and processes them to create 
        enhanced versions that include summaries and context. For each chunk, it 
        generates a summary using the LLM service, adds file-level context if 
        available, and combines them with the original content.

        Args:
            all_chunks (List[dict]): Complete list of chunks from the document
            chunks_to_process (List[dict]): Subset of chunks that need processing
            written_by_me (bool): Flag indicating if the document was written by
                                  the specified author

        Returns:
            List[dict]: Processed chunks with added 'full_context' field
            containing:
                - File summary (if available)
                - Chunk summary
                - Original chunk content

        Notes:
            - File summary is generated from the first and last chunks of the 
                document
            - Special handling is applied for content written by the specified 
                author
            - Each processed chunk maintains its original data while adding the 
                enhanced context
        """

        processed_chunks = []
        if len(chunks_to_process) == 0:
            return [], None

        file_summary, err = await self._get_file_summary(all_chunks, written_by_me)
        if err is not None:
            return None, err

        file_summ_prompt = ""
        if file_summary:
            file_summ_prompt = self.FILE_SUMMARY
            file_summ_prompt = file_summ_prompt.replace("{{file_summary}}", file_summary)
        else:
            file_summary = ""


        for chunk in chunks_to_process:
            processed, err = await self._process_chunk(
                file_summ_prompt,
                file_summary,
                chunk,
                written_by_me,
            )

            if err is not None:
                return None, err

            processed_chunks.append(processed)

        return processed_chunks, None

    async def _get_file_summary(
        self,
        chunks: List[dict],
        written_by_me: bool,
    ) -> [str, Exception]:
        nr_init_chunks = min(self.CHUNKS_TO_USE_FOR_FILE_SUMMARY, len(chunks))
        if nr_init_chunks <= 1:
            return None, None

        init_chunk_contents = []
        start_chunks = math.ceil(nr_init_chunks / 2)
        end_chunks = nr_init_chunks - start_chunks
        for chunk in chunks[:start_chunks]:
            init_chunk_contents.append(chunk["content"])

        init_chunk_contents.append("...")

        for chunk in chunks[-end_chunks:]:
            init_chunk_contents.append(chunk["content"])

        chunk_str = "\n\n".join(init_chunk_contents)
        summary, err = await self._generate_document_summary(
            chunk_str,
            written_by_me,
        )

        if err is not None:
            return None, err

        return summary, None

    async def _generate_document_summary(
        self,
        initial_chunk: str,
        written_by_me: bool,
    ) -> [str, Exception]:
        prompt = self.SUMMARIZE_FILE_PROMPT
        if written_by_me:
            prompt = f"{prompt} {self._parse_written_by_me_prompt()}"
        print("SYSTEM_PROMPT:", prompt)

        res, err = await self._send_llm_message(
            system_prompt=prompt,
            message=initial_chunk,
        )

        if err is not None:
            return None, err
        
        return res, None

    async def _process_chunk(
        self,
        file_summ_prompt: str,
        file_summary: str,
        chunk: dict,
        written_by_me: bool,
    ) -> [dict, Exception]:
        prompt = self.SUMMARIZE_CHUNK_PROMPT
        if written_by_me:
            prompt = f"{prompt} {self._parse_written_by_me_prompt()}"

        if len(file_summ_prompt) > 0:
            prompt = f"{prompt}\n{file_summ_prompt}"

        print("SYSTEM_PROMPT:", prompt)
        messages = [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": chunk["content"],
            },
        ]
        summary, err = await self.llm_service.chat(
            messages=messages,
            model=self.model_name,
        )

        if err is not None:
            return None, err

        chunk["full_context"] = ""
        if len(file_summary) > 0:
            chunk["full_context"] += f"<file_summary>\n{file_summary}\n</file_summary>\n\n"

        chunk["full_context"] += f"<chunk_summary>\n{summary}\n</chunk_summary>"
        chunk["full_context"] += f"\n\n{chunk['content']}"
        return chunk, None

    async def _send_llm_message(self, system_prompt: str, message: str) -> [str, Exception]:
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": message,
            },
        ]

        response, err = await self.llm_service.chat(
            messages=messages,
            model=self.model_name,
        )

        if err is not None:
            return None, err

        return response, None
