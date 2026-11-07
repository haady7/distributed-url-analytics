from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import enforce_rate_limit, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
    dependencies=[Depends(enforce_rate_limit)],
)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.query(User.id).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    token = create_access_token(str(user.id))
    from app.core.config import settings

    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
