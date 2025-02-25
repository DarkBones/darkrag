from abc import ABC
from typing import List


class BaseSplitter(ABC):
    """
    Base class for text splitters.
    """

    def split_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk size must be greater than chunk overlap")

        # if the text is short enough, return it directly
        if len(text) <= chunk_size:
            return [text]

        splits = []
        start = 0
        while start < len(text):
            segment = text[start:]
            # Leave room for overlap by using (chunk_size - chunk_overlap)
            next_pos = self._find_next_position(
                segment,
                chunk_size - chunk_overlap,
            )

            overlap = 0
            if start > overlap and chunk_overlap > 0:
                overlap = self._find_previous_position(
                    text[: start - 1],
                    max(chunk_overlap, (chunk_size - len(segment)) * 0.8),
                )
            splits.append(text[start - overlap : start + next_pos])
            start += next_pos + 1
        return splits

    def _find_next_position(self, text: str, max_size: int) -> int:
        if len(text) <= max_size:
            return len(text)

        # Try breaking at a paragraph break, then line, sentence, and finally word.
        for break_fn in [
            # self._find_paragraph_break,
            # self._find_line_break,
            self._find_sentence_break,
            self._find_word_break,
        ]:
            pos = break_fn(text, max_size)
            if pos != -1:
                return pos
        return max_size

    @staticmethod
    def _find_previous_position(text: str, overlap: int) -> str:
        if overlap == 0:
            return 0

        pos = 0
        for i, c in enumerate(text[::-1]):
            if i > overlap:
                break

            if c == " ":
                pos = i

        return pos + 1

    @staticmethod
    def _find_paragraph_break(text: str, max_size: int) -> int:
        idx = text.find("\n\n")
        return idx + 2 if 0 < idx <= max_size else -1

    @staticmethod
    def _find_line_break(text: str, max_size: int) -> int:
        idx = text.find("\n")
        return idx + 1 if 0 < idx <= max_size else -1

    @staticmethod
    def _find_sentence_break(text: str, max_size: int) -> int:
        last_break = -1
        current = 0
        while current < len(text) and current < max_size:
            if text[current] in ".?!":
                # Advance past any extra punctuation characters.
                temp = current + 1
                while temp < len(text) and text[temp] in ".?!":
                    temp += 1
                last_break = temp
            current += 1
        return last_break

    @staticmethod
    def _find_word_break(text: str, max_size: int) -> int:
        """
        Accumulate words until adding the next word (plus a space) would
        push the chunk size to max_size or more. If the very first word is
        longer than max_size, return the full length of that word.
        """

        i = 0
        size = 0
        last_break = 0
        # Loop over words in the raw text without collapsing extra spaces.
        while i < len(text):
            # Find the end of the current word.
            j = i
            while j < len(text) and text[j] != " ":
                j += 1
            word_length = j - i
            candidate = size + word_length + 1

            # If adding this word would exceed max_size...
            if candidate >= max_size:
                # If this is the first word and it exceeds max_size,
                # then just return the full word (ignoring max_size).
                if size == 0:
                    return j
                break

            size = candidate
            last_break = j

            # Skip following spaces.
            while j < len(text) and text[j] == " ":
                j += 1
            i = j

        if last_break > 0:
            return last_break

        return len(text)
