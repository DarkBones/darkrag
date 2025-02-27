"""
Markdown splitter that breaks markdown into sections, then further into blocks,
and finally into chunks based on chunk_size and overlap.
"""

import os
from typing import Dict, List, Optional, Tuple

from langchain_text_splitters import MarkdownHeaderTextSplitter

from settings import settings

from .base_splitter import BaseSplitter


class MarkdownSplitter(BaseSplitter):
    """
    Splits the given markdown text into sections and further into blocks and chunks.
    """

    # Line classification methods
    @staticmethod
    def _is_line_quote(line: str) -> bool:
        return line.lstrip().startswith(">")

    @staticmethod
    def _is_line_empty(line: str) -> bool:
        return not line or line.isspace()

    @staticmethod
    def _is_code_block_start(line: str) -> bool:
        return line.lstrip().startswith("```")

    # Block finding methods
    @staticmethod
    def _find_code_block_end(lines: List[str]) -> int:
        """
        Finds the end of a code block by looking for the next line starting
        with ```.
        """

        return next(
            (i + 1 for i, l in enumerate(lines) if l.lstrip().startswith("```")),
            -1,
        )

    def _find_quote_block_end(self, lines: List[str]) -> int:
        """
        Finds the end index of a block of quote lines.
        """

        return next(
            (i for i, l in enumerate(lines) if not self._is_line_quote(l)), len(lines)
        )

    def _create_code_block(
        self, lines: List[str], start: int
    ) -> Tuple[Optional[Dict], int]:
        """
        Creates a code block from the current line and returns a tuple of:
        (block dict or None, new index).
        """

        end_offset = self._find_code_block_end(lines[start + 1 :])
        if end_offset > 0:
            end = start + 1 + end_offset
            block = {
                "type": "block",
                "content": "\n".join(lines[start:end]),
            }
            return block, end
        return None, start + 1

    def _create_quote_block(
        self,
        lines: List[str],
        start: int,
    ) -> Tuple[Dict, int]:
        """
        Creates a quote block from the current lines.
        """

        end_offset = self._find_quote_block_end(lines[start:])
        block = {
            "type": "block",
            "content": "\n".join(lines[start : start + end_offset]),
        }
        return block, start + end_offset

    # Main interface
    def __call__(
        self,
        text: str,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ) -> List[Dict]:
        """
        Splits markdown text into chunks.
        """

        chunk_size = chunk_size or settings.get("chunk_size", 1000)
        chunk_overlap = chunk_overlap or settings.get("chunk_overlap", 100)

        sections = []
        # Split text into sections using header-based splitting.
        for section in self._split_into_sections(text):
            blocks = self._split_section_into_blocks(
                section.page_content, section.metadata
            )
            sections.append(blocks)

        chunks = self._split_into_chunks(sections, chunk_size, chunk_overlap)
        chunks = self._preprocess_chunks(chunks)
        return chunks

    @staticmethod
    def _preprocess_chunks(chunks):
        for chunk in chunks:
            metadata = chunk["metadata"]
            headers = []
            for key in metadata.keys():
                if key == "Header1":
                    headers.append(f"# {metadata[key]}")
                    continue
                if key == "Header2":
                    headers.append(f"## {metadata[key]}")
                    continue
                if key == "Header3":
                    headers.append(f"### {metadata[key]}")
                    continue
                if key == "Header4":
                    headers.append(f"#### {metadata[key]}")
                    continue

            if len(headers) > 0:
                chunk_headers = (
                    f"<chunk_headers>\n{', '.join(headers)}\n</chunk_headers>"
                )
                chunk_content = f"<chunk_content>\n{chunk['content']}\n</chunk_content>"
                chunk["content"] = f"{chunk_headers}\n\n{chunk_content}"

            chunk["metadata"] = {
                "headers": chunk["metadata"],
            }
        return chunks

    # Chunk assembly
    def _split_into_chunks(
        self, sections: List[List[Dict]], chunk_size: int, chunk_overlap: int
    ) -> List[Dict]:
        """
        Combine blocks from sections into chunks based on chunk_size and
        chunk_overlap.
        """

        chunks = []
        current_blocks = []
        current_size = 0

        def flush_current_chunk():
            nonlocal current_blocks, current_size, chunks
            if current_blocks:
                combined = "\n\n".join(b["content"] for b in current_blocks)
                chunks.append(
                    {
                        "content": combined,
                        "metadata": current_blocks[0]["metadata"],
                    }
                )
                current_blocks = []
                current_size = 0

        for section in sections:
            # Reset per section
            current_blocks = []
            current_size = 0
            for block in section:
                block_size = len(block["content"])
                # If block fits in current chunk, add it.
                if current_size + block_size <= chunk_size:
                    current_blocks.append(block)
                    current_size += block_size
                    continue

                flush_current_chunk()

                # Now, try fitting the block in a fresh chunk.
                if block_size <= chunk_size:
                    current_blocks.append(block)
                    current_size += block_size
                    continue

                # If block is too big and cannot be split further, force
                # add it.
                if block["type"] == "block":
                    current_blocks.append(block)
                    current_size += block_size
                    continue

                # Otherwise, split the block content using BaseSplitter's
                # split_text.
                splits = self.split_text(
                    text=block["content"],
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                for split in splits:
                    chunks.append(
                        {
                            "content": split,
                            "metadata": block["metadata"],
                        }
                    )

            # Flush any remaining blocks
            flush_current_chunk()

        return chunks

    # Section splitting
    def _split_into_sections(self, text: str):
        """
        Splits the markdown text into sections based on header markers.
        """

        headers_to_split_on = [
            ("#", "Header1"),
            ("##", "Header2"),
            ("###", "Header3"),
        ]
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
        )
        return splitter.split_text(text)

    # Block splitting
    def _split_section_into_blocks(
        self,
        text: str,
        metadata: Dict,
    ) -> List[Dict]:
        """
        Splits a section of markdown text into blocks (paragraphs, code blocks,
        quotes).
        """

        blocks = []
        lines = text.split("\n")
        current_paragraph = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if self._is_line_empty(line):
                i += 1
                continue

            if self._is_code_block_start(line):
                if current_paragraph:
                    blocks.append(
                        self._create_paragraph_block(
                            current_paragraph,
                            metadata,
                        )
                    )
                    current_paragraph = []
                block, i = self._create_code_block(lines, i)
                if block:
                    block["metadata"] = metadata
                    blocks.append(block)
                continue

            if self._is_line_quote(line):
                if current_paragraph:
                    blocks.append(
                        self._create_paragraph_block(
                            current_paragraph,
                            metadata,
                        )
                    )
                    current_paragraph = []
                block, i = self._create_quote_block(lines, i)
                block["metadata"] = metadata
                blocks.append(block)
                continue

            # Accumulate normal paragraph lines.
            current_paragraph.append(line.strip())
            i += 1

        if current_paragraph:
            blocks.append(
                self._create_paragraph_block(
                    current_paragraph,
                    metadata,
                )
            )
        return blocks

    @staticmethod
    def _create_paragraph_block(paragraph: List[str], metadata: Dict) -> Dict:
        """
        Creates a paragraph block from accumulated lines.
        """

        return {
            "type": "paragraph",
            "content": "\n".join(paragraph),
            "metadata": metadata,
        }
