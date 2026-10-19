from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1.routers import api_router
from fastapi.middleware.cors import CORSMiddleware
from app.clients.neo4j_client import neo4j_client
from app.crud.graph.schema import init_graph_schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Kết nối và kiểm tra schema Neo4j
    try:
        neo4j_client.connect()
        init_graph_schema()
    except Exception as e:
        print(f"[Warning] Neo4j startup check: {e}")
    yield
    # Shutdown: Đóng driver Neo4j
    neo4j_client.close()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=("API for CV evaluation, Semantic Matching & Knowledge Graph."),
        version="1.0.0",
        lifespan=lifespan,
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
