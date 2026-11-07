import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.tasks import record_click
from app.core.config import settings
from app.core.dependencies import enforce_rate_limit, get_current_user
from app.db import get_db
from app.models import ClickEvent, ShortURL, User
from app.schemas import CountryClicks, DailyClicks, URLAnalytics, URLCreate, URLRead
from app.services.url_service import create_short_url

logger = logging.getLogger(__name__)
router = APIRouter(tags=["URLs"], dependencies=[Depends(enforce_rate_limit)])


def _to_url_read(record: ShortURL) -> URLRead:
    return URLRead(
        code=record.code,
        original_url=record.original_url,
        short_url=f"{settings.PUBLIC_BASE_URL}/{record.code}",
        created_at=record.created_at,
        expires_at=record.expires_at,
        is_active=record.is_active,
    )


def _owned_url(db: Session, code: str, user: User) -> ShortURL:
    record = db.query(ShortURL).filter(ShortURL.code == code, ShortURL.user_id == user.id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return record


@router.post("/api/v1/urls", response_model=URLRead, status_code=status.HTTP_201_CREATED)
def create_url(
    payload: URLCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        record = create_short_url(
            db,
            owner=user,
            original_url=str(payload.original_url),
            custom_code=payload.custom_code,
            expires_at=payload.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Short URL creation failed")
        raise HTTPException(status_code=500, detail="Could not create short URL") from exc
    return _to_url_read(record)


@router.get("/api/v1/urls/{code}", response_model=URLRead)
def get_url(code: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _to_url_read(_owned_url(db, code, user))


@router.delete("/api/v1/urls/{code}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_url(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = _owned_url(db, code, user)
    record.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/v1/urls/{code}/analytics", response_model=URLAnalytics)
def get_analytics(code: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = _owned_url(db, code, user)
    base = db.query(ClickEvent).filter(ClickEvent.url_id == record.id)
    total = base.count()

    daily_rows = (
        db.query(func.date(ClickEvent.clicked_at).label("day"), func.count(ClickEvent.id).label("clicks"))
        .filter(ClickEvent.url_id == record.id)
        .group_by(func.date(ClickEvent.clicked_at))
        .order_by(func.date(ClickEvent.clicked_at).desc())
        .limit(30)
        .all()
    )
    country_rows = (
        db.query(ClickEvent.country, func.count(ClickEvent.id).label("clicks"))
        .filter(ClickEvent.url_id == record.id, ClickEvent.country.is_not(None))
        .group_by(ClickEvent.country)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(10)
        .all()
    )
    referrer_rows = (
        db.query(ClickEvent.referrer, func.count(ClickEvent.id).label("clicks"))
        .filter(ClickEvent.url_id == record.id, ClickEvent.referrer.is_not(None))
        .group_by(ClickEvent.referrer)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(10)
        .all()
    )
    return URLAnalytics(
        code=record.code,
        total_clicks=total,
        daily_clicks=[DailyClicks(date=str(row.day), clicks=row.clicks) for row in daily_rows],
        top_countries=[CountryClicks(country=row[0], clicks=row[1]) for row in country_rows],
        top_referrers=[{"referrer": row[0], "clicks": row[1]} for row in referrer_rows],
    )


@router.get("/{code}", include_in_schema=False)
def redirect_to_original(code: str, request: Request, db: Session = Depends(get_db)):
    record = db.query(ShortURL).filter(ShortURL.code == code, ShortURL.is_active.is_(True)).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    now = datetime.now(timezone.utc)
    if record.expires_at is not None:
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise HTTPException(status_code=410, detail="This short URL has expired")

    client_ip = request.client.host if request.client else None
    try:
        record_click.delay(
            url_id=record.id,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
            ip_address=client_ip,
            clicked_at_iso=now.isoformat(),
        )
    except Exception as exc:
        # A click should still redirect even when the analytics queue is temporarily down.
        logger.warning("Could not enqueue click analytics for %s: %s", code, exc)

    return RedirectResponse(url=record.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
