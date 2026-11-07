from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.rate_limit import allow_request
from app.core.security import decode_access_token
from app.db import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    subject = decode_access_token(credentials.credentials)
    if subject is None or not subject.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, int(subject))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or missing")
    return user


def enforce_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    try:
        allowed = allow_request(client_ip)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Rate limiter is temporarily unavailable") from exc
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again shortly.",
            headers={"Retry-After": "1"},
        )
