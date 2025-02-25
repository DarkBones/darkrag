import unittest

from base_splitter import BaseSplitter


class BaseSplitterTest(unittest.TestCase):
    def test_split_text(self):
        test_cases = [
            {
                "text": "",
                "chunk_size": 100,
                "chunk_overlap": 50,
                "want_splits": [""],
            },
            {
                "text": "No splits needed",
                "chunk_size": 100,
                "chunk_overlap": 50,
                "want_splits": [
                    "No splits needed",
                ],
            },
            {
                "text": "This is one sentence. This is two sentence.",
                "chunk_size": 25,
                "chunk_overlap": 0,
                "want_splits": [
                    "This is one sentence.",
                    "This is two sentence.",
                ],
            },
            {
                "text": "This is one sentence.. This is two sentence?! This is thr sentence!!",
                "chunk_size": 25,
                "chunk_overlap": 0,
                "want_splits": [
                    "This is one sentence..",
                    "This is two sentence?!",
                    "This is thr sentence!!",
                ],
            },
            {
                "text": "Very tiny. Short sentences. With. Large..  Chunk size. Split.",
                "chunk_size": 45,
                "chunk_overlap": 0,
                "want_splits": [
                    "Very tiny. Short sentences. With. Large..",
                    " Chunk size. Split.",
                ],
            },
            {
                "text": "This sentence is too long so it will be split by words.",
                "chunk_size": 26,
                "chunk_overlap": 0,
                "want_splits": [
                    "This sentence is too",
                    "long so it will be split",
                    "by words.",
                ],
            },
            {
                "text": "This sentence is too  long  and has   random multiple   spaces.",
                "chunk_size": 26,
                "chunk_overlap": 0,
                "want_splits": [
                    "This sentence is too",
                    " long  and has   random",
                    "multiple   spaces.",
                ],
            },
            {
                "text": "thisisjustonebigwordthatwecannotpossiblysplitintosmallerchunks smol",
                "chunk_size": 10,
                "chunk_overlap": 0,
                "want_splits": [
                    "thisisjustonebigwordthatwecannotpossiblysplitintosmallerchunks",
                    "smol",
                ],
            },
            {
                "text": "This is. A collection of sentences. What will the overlap do?",
                "chunk_size": 55,
                "chunk_overlap": 20,
                "want_splits": [
                    "This is. A collection of sentences.",
                    "of sentences. What will the overlap do?",
                ],
            },
            {
                "text": "This sentence is too long so it will be split by words.",
                "chunk_size": 26,
                "chunk_overlap": 10,
                "want_splits": [
                    "This sentence",
                    "sentence is too long so",
                    "long so it will be",
                    "it will be split by words.",
                ],
            },
        ]

        for tc in test_cases:
            splits = BaseSplitter().split_text(
                text=tc["text"],
                chunk_size=tc["chunk_size"],
                chunk_overlap=tc["chunk_overlap"],
            )
            self.assertEqual(splits, tc["want_splits"])


if __name__ == "__main__":
    unittest.main()
