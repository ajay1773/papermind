from pathlib import Path
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse

from papermind.config import settings
from papermind.ingestion.service import ingest_document

logger = logging.getLogger(__name__)

router = APIRouter()
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-document", response_class=HTMLResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".txt", ".md"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}. Use .pdf, .txt, or .md")
    bytes_data = await file.read()
    if len(bytes_data) > 1024 * 1024 * 10:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

    await ingest_document(bytes_data, file.filename)
    return HTMLResponse(content=f"Document uploaded successfully: {file.filename}")
