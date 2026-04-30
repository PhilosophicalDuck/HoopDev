import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.database import create_tables, engine
from app.backend.routers import auth, users, sessions, highlights, benchmarks, workouts, camera, dashboard
from app.backend.routers import live_session
from app.backend.routers import video_upload
from app.backend.routers import chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


def _migrate_db() -> None:
    """Add columns introduced after initial schema creation (SQLite-safe)."""
    from sqlalchemy import text
    with engine.connect() as conn:
        for col, definition in [
            ("source", "VARCHAR NOT NULL DEFAULT 'live'"),
            ("video_path", "VARCHAR"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE drill_sessions ADD COLUMN {col} {definition}"))
                conn.commit()
                logger.info("Migration: added drill_sessions.%s", col)
            except Exception:
                pass  # Column already exists — ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Basketball Training App backend...")
    create_tables()
    _migrate_db()
    highlights_dir = Path(__file__).parent.parent.parent / "highlights"
    highlights_dir.mkdir(exist_ok=True)
    (highlights_dir / "uploads").mkdir(exist_ok=True)
    logger.info("Database ready. Highlights dir: %s", highlights_dir)
    yield
    # Shutdown
    logger.info("Backend shutting down.")


app = FastAPI(
    title="Basketball Training App",
    version="1.0.0",
    description="Live drill feedback, workout selection, and progress tracking.",
    lifespan=lifespan,
)

# Allow the React dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(highlights.router)
app.include_router(benchmarks.router)
app.include_router(workouts.router)
app.include_router(camera.router)
app.include_router(live_session.router)
app.include_router(dashboard.router)
app.include_router(video_upload.router)
app.include_router(video_upload.ws_router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
