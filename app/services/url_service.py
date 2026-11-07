import secrets
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ShortURL, User

BASE62 = string.digits + string.ascii_letters


def encode_base62(number: int) -> str:
    if number == 0:
        return BASE62[0]
    encoded = []
    while number:
        number, remainder = divmod(number, 62)
        encoded.append(BASE62[remainder])
    return "".join(reversed(encoded))


def generate_code(length: int = 8) -> str:
    # Uniform random Base62 key; uniqueness is enforced by the database constraint.
    return "".join(secrets.choice(BASE62) for _ in range(length))


def create_short_url(
    db: Session,
    owner: User,
    original_url: str,
    custom_code: str | None,
    expires_at,
) -> ShortURL:
    if custom_code:
        existing = db.query(ShortURL.id).filter(ShortURL.code == custom_code).first()
        if existing:
            raise ValueError("That custom short code is already in use")
        code = custom_code
    else:
        code = None
        for _ in range(8):
            candidate = generate_code()
            exists = db.query(ShortURL.id).filter(ShortURL.code == candidate).first()
            if not exists:
                code = candidate
                break
        if code is None:
            raise RuntimeError("Could not generate a unique code; please retry")

    record = ShortURL(
        code=code,
        original_url=original_url,
        user_id=owner.id,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if custom_code:
            raise ValueError("That custom short code is already in use") from exc
        raise RuntimeError("A short-code collision occurred; please retry") from exc
    db.refresh(record)
    return record
