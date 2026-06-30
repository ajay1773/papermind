from pydantic import BaseModel


class PaperMetadata(BaseModel):
    title: str
    abstract: str
    doi: str
    openalex_id: str
    pdf_url: str | None
    year: int
    authors: list[str]
