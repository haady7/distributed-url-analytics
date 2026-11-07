import hmac
import logging
from datetime import datetime, timezone

from app.analytics.celery_app import celery_app
from app.core.config import settings
from app.db import SessionLocal
from app.models import ClickEvent

logger = logging.getLogger(__name__)


def _lookup_location(ip_address: str | None) -> tuple[str | None, str | None]:
    if not ip_address or not settings.GEOIP_DB_PATH:
        return None, None
    try:
        import geoip2.database

        with geoip2.database.Reader(settings.GEOIP_DB_PATH) as reader:
            result = reader.city(ip_address)
            country = result.country.name
            city = result.city.name
            return country, city
    except Exception as exc:  # GeoIP is optional; click tracking must still succeed.
        logger.debug("GeoIP lookup skipped: %s", exc)
        return None, None


@celery_app.task(name="app.analytics.tasks.record_click", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def record_click(
    url_id: int,
    user_agent: str | None,
    referrer: str | None,
    ip_address: str | None,
    clicked_at_iso: str | None = None,
) -> None:
    country, city = _lookup_location(ip_address)
    ip_hash = (
        hmac.new(
            settings.SECRET_KEY.get_secret_value().encode("utf-8"),
            ip_address.encode("utf-8"),
            "sha256",
        ).hexdigest()
        if ip_address
        else None
    )
    clicked_at = datetime.fromisoformat(clicked_at_iso) if clicked_at_iso else datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        event = ClickEvent(
            url_id=url_id,
            user_agent=(user_agent or "")[:512] or None,
            referrer=(referrer or "")[:2048] or None,
            ip_hash=ip_hash,
            country=country,
            city=city,
            clicked_at=clicked_at,
        )
        db.add(event)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
