from fastapi import APIRouter, HTTPException

from papermind.common.schemas import QueryRequest, QueryResponse, SourceInfo
from papermind.retrieval.pipeline import run_query

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        result = await run_query(request.query)
        return QueryResponse(answer=result["answer"], sources=[SourceInfo(**c) for c in result["sources"]])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
