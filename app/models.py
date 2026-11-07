from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    urls: Mapped[list["ShortURL"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class ShortURL(Base):
    __tablename__ = "short_urls"
    __table_args__ = (Index("ix_short_urls_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    owner: Mapped[User] = relationship(back_populates="urls")
    clicks: Mapped[list["ClickEvent"]] = relationship(back_populates="url", cascade="all, delete-orphan")


class ClickEvent(Base):
    __tablename__ = "click_events"
    __table_args__ = (
        Index("ix_click_events_url_clicked", "url_id", "clicked_at"),
        Index("ix_click_events_country", "country"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("short_urls.id", ondelete="CASCADE"), nullable=False)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    url: Mapped[ShortURL] = relationship(back_populates="clicks")
