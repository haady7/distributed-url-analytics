from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.routes import auth, urls
from app.db import get_db
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A distributed URL shortener with JWT authentication, Redis token-bucket rate limiting, "
        "MySQL persistence, and asynchronous click analytics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.include_router(auth.router)
app.include_router(urls.router)


@app.get("/health/live", tags=["health"])
def health_live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def health_ready(db: Session = Depends(get_db)):
    redis_client = Redis.from_url(settings.REDIS_URL)
    try:
        db.execute(text("SELECT 1"))
        redis_client.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="A required dependency is unavailable") from exc
    finally:
        redis_client.close()
    return JSONResponse({"status": "ready"})


@app.get("/", tags=["health"])
def root():
    return {"service": "LinkPulse", "docs": "/docs", "health": "/health/live"}
