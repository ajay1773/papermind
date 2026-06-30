import logging

from papermind.ingestion.chunker import chunk_pdf
from papermind.memory import MemoryService
from papermind.vectorstore import store_chunks

logger = logging.getLogger(__name__)


async def ingest_document(bytes_data: bytes, filename: str, openalex_id: str = "") -> list[dict]:
    chunks = chunk_pdf(bytes_data, filename, openalex_id=openalex_id)
    logger.info("Chunked %s into %d chunks", filename, len(chunks))
    await store_chunks(chunks)
    paper_id = openalex_id or filename
    MemoryService().add_indexed_paper(paper_id=paper_id, title=filename, source=filename)
    return chunks
