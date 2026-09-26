from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1.routers import api_router
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "An automated recruitment screening platform leveraging FastAPI "
            "and the all-MiniLM-L6-v2 transformer model to evaluate candidate–job "
            "fit through semantic similarity analysis."
        ),
        version="1.0.0",
    )
    app.include_router(router=api_router, prefix="/api/v1")

    return app


app = create_app()


# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
