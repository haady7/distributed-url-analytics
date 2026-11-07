"""Create users, short URLs, and click events."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "short_urls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("original_url", sa.String(length=2048), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_short_urls_code", "short_urls", ["code"], unique=True)
    op.create_index("ix_short_urls_user_created", "short_urls", ["user_id", "created_at"])

    op.create_table(
        "click_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("url_id", sa.Integer(), nullable=False),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("referrer", sa.String(length=2048), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["url_id"], ["short_urls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_click_events_url_clicked", "click_events", ["url_id", "clicked_at"])
    op.create_index("ix_click_events_country", "click_events", ["country"])


def downgrade() -> None:
    op.drop_index("ix_click_events_country", table_name="click_events")
    op.drop_index("ix_click_events_url_clicked", table_name="click_events")
    op.drop_table("click_events")
    op.drop_index("ix_short_urls_user_created", table_name="short_urls")
    op.drop_index("ix_short_urls_code", table_name="short_urls")
    op.drop_table("short_urls")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
