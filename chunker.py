"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?:])\s+")


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _pack(units: list[str], max_size: int) -> list[str]:
    """Greedily pack whole units (sentences or lines) up to max_size each."""
    pieces: list[str] = []
    current = ""
    for unit in units:
        if current and len(current) + 1 + len(unit) > max_size:
            pieces.append(current)
            current = unit
        else:
            current = f"{current} {unit}".strip() if current else unit
    if current:
        pieces.append(current)
    return pieces


def _split_paragraph(paragraph: str, max_size: int) -> list[str]:
    """
    Break an over-long paragraph into pieces without cutting mid-sentence.

    Tries sentence boundaries first. If a piece is still too big — no
    sentence punctuation anywhere, which happens with irs_tax's giant
    tax-bracket tables — falls back to packing individual lines instead.
    """
    if len(paragraph) <= max_size:
        return [paragraph]

    by_sentence = _pack(_SENTENCE_SPLIT.split(paragraph), max_size)

    pieces: list[str] = []
    for piece in by_sentence:
        if len(piece) <= max_size:
            pieces.append(piece)
        else:
            # ponytail: no sentence punctuation to split on (e.g. a markdown
            # table with no periods) — pack lines instead. Rows past the
            # first chunk lose their header row; a table-aware parser isn't
            # worth it for the handful of tables in this corpus.
            pieces.extend(_pack(piece.split("\n"), max_size))
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents on paragraph breaks, falling back to sentences (then
    lines) only for paragraphs too big to keep whole. Never cuts mid-sentence.

    A chunk boundary starts a new chunk with whole trailing units carried
    forward from the end of the previous one, up to config.CHUNK_OVERLAP
    characters, so a lead-in sentence doesn't get orphaned from what follows.
    """
    chunk_size = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP

    chunks: list[Chunk] = []
    for doc in documents:
        units: list[str] = []
        for paragraph in _PARAGRAPH_SPLIT.split(doc.text):
            paragraph = paragraph.strip()
            if paragraph:
                units.extend(_split_paragraph(paragraph, chunk_size))

        index = 0
        current = ""
        current_units: list[str] = []
        for unit in units:
            candidate = f"{current}\n\n{unit}" if current else unit
            if len(candidate) > chunk_size and current:
                chunks.append(
                    Chunk(
                        text=current,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

                carried: list[str] = []
                carried_len = 0
                for prev_unit in reversed(current_units):
                    if carried_len + len(prev_unit) > overlap:
                        break
                    carried.insert(0, prev_unit)
                    carried_len += len(prev_unit)
                current_units = carried + [unit]
                current = "\n\n".join(current_units)
            else:
                current = candidate
                current_units.append(unit)

        if current:
            chunks.append(
                Chunk(
                    text=current,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
