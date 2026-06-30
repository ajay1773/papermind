import re
from dataclasses import dataclass, field

from papermind.ingestion.parser import extract_with_llamaparse
from papermind.ingestion.semantic_chunker import semantic_split


@dataclass
class Chunk:
    chunk_id: int
    type: str      # "prose" | "table" | "heading"
    heading: str
    text: str
    page: int
    source: str
    openalex_id: str = ""
    char_count: int = field(init=False)

    def __post_init__(self):
        self.char_count = len(self.text)

    def to_dict(self):
        return self.__dict__


def _split_long_text(text: str, max_chars: int = 1500) -> list[str]:
    """Split prose at sentence boundaries when it exceeds max_chars."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sub_chunks, current, current_len = [], [], 0

    for sentence in sentences:
        if current_len + len(sentence) > max_chars and current:
            sub_chunks.append(" ".join(current))
            current, current_len = [sentence], len(sentence)
        else:
            current.append(sentence)
            current_len += len(sentence)

    if current:
        sub_chunks.append(" ".join(current))

    return sub_chunks


def _parse_markdown_blocks(markdown: str) -> list[dict]:
    blocks = []
    current_page = 1
    in_table = False
    table_lines = []

    def flush_table(page: int):
        if table_lines:
            blocks.append({
                "type": "table",
                "text": "\n".join(table_lines),
                "page": page,
            })
            table_lines.clear()

    for line in markdown.splitlines():

        page_match = (
            re.match(r'<!--\s*[Pp]age\s+(\d+)\s*-->', line) or
            re.match(r'<page_number>(\d+)</page_number>', line)
        )
        if page_match:
            flush_table(current_page)
            current_page = int(page_match.group(1))
            continue

        if line.strip().startswith("|"):
            in_table = True
            if not re.match(r'^\|\s*[-:]+\s*(\|\s*[-:]+\s*)+\|?$', line.strip()):
                table_lines.append(line)
            continue

        if in_table:
            flush_table(current_page)
            in_table = False

        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("#"):
            heading_text = re.sub(r'^#+\s*', '', stripped)
            blocks.append({
                "type": "heading",
                "text": heading_text,
                "page": current_page,
                "level": len(re.match(r'^(#+)', stripped).group(1)),
            })
            continue

        if re.match(r'^(Figure|Fig\.)\s+\d+[\.:]\s*', stripped, re.IGNORECASE):
            blocks.append({
                "type": "figure_caption",
                "text": stripped,
                "page": current_page,
            })
            continue

        blocks.append({
            "type": "prose",
            "text": stripped,
            "page": current_page,
        })

    flush_table(current_page)

    return blocks


def _assemble_chunks(blocks: list[dict], source: str,
                     max_prose_chars: int = 1500,
                     openalex_id: str = "") -> list[Chunk]:
    chunks = []
    chunk_id = 0
    current_heading = "Introduction"
    current_prose = []
    current_page = 1

    def flush_prose():
        nonlocal chunk_id
        text = " ".join(current_prose).strip()
        if not text:
            return

        if len(text) < 150:
            current_prose.clear()
            return

        semantic_subs: list[str] = semantic_split(text)

        for sub in semantic_subs:
            if len(sub) > max_prose_chars:
                for piece in _split_long_text(sub, max_prose_chars):
                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        type="prose",
                        heading=current_heading,
                        text=piece,
                        page=current_page,
                        source=source,
                        openalex_id=openalex_id,
                    ))
                    chunk_id += 1
            else:
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    type="prose",
                    heading=current_heading,
                    text=sub,
                    page=current_page,
                    source=source,
                    openalex_id=openalex_id,
                ))
                chunk_id += 1

        current_prose.clear()

    for block in blocks:
        if block["type"] == "heading":
            flush_prose()
            current_heading = block["text"]
            current_page = block["page"]

        elif block["type"] == "table":
            flush_prose()
            chunks.append(Chunk(
                chunk_id=chunk_id,
                type="table",
                heading=current_heading,
                text=block["text"],
                page=block["page"],
                source=source,
                openalex_id=openalex_id,
            ))
            chunk_id += 1

        elif block["type"] == "figure_caption":
            flush_prose()
            chunks.append(Chunk(
                chunk_id=chunk_id,
                type="figure_caption",
                heading=current_heading,
                text=block["text"],
                page=block["page"],
                source=source,
                openalex_id=openalex_id,
            ))
            chunk_id += 1

        else:
            current_prose.append(block["text"])
            current_page = block["page"]

    flush_prose()
    return chunks


def _remove_noise_sections(chunks: list[Chunk]) -> list[Chunk]:
    NOISE_HEADINGS = {"references", "acknowledgements", "bibliography", "works cited", "appendix", "appendices"}
    return [chunk for chunk in chunks if chunk.heading.lower() not in NOISE_HEADINGS]


def chunk_pdf(contents: bytes, filename: str,
              max_prose_chars: int = 1500,
              openalex_id: str = "") -> list[dict]:
    markdown = extract_with_llamaparse(contents)
    blocks = _parse_markdown_blocks(markdown)
    chunks = _assemble_chunks(blocks, filename, max_prose_chars, openalex_id)
    chunks = _remove_noise_sections(chunks)
    return [c.to_dict() for c in chunks]
