from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from papermind.config import settings
from papermind.ingestion.router import router as ingestion_router
from papermind.retrieval.router import router as retrieval_router
from papermind.web.limiter import limiter
from papermind.web.rate_limit import briefing_rate_limit_handler
from papermind.web.router import router as web_router

WEB_DIR = Path(__file__).resolve().parent / "web"


def create_app() -> FastAPI:
    application = FastAPI(
        title="Papermind",
        description="RAG-powered document Q&A API",
        version="0.1.0",
    )

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, briefing_rate_limit_handler)
    application.add_middleware(SlowAPIMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")

    application.include_router(ingestion_router, prefix="/api/v1")
    application.include_router(retrieval_router, prefix="/api/v1")
    application.include_router(web_router)

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "papermind.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
