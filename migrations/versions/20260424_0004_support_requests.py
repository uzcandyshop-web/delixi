"""add support_requests table

Revision ID: 20260424_0004
Revises: 20260424_0003
Create Date: 2026-04-24 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260424_0004"
down_revision = "20260424_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_requests",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id"), nullable=False,
        ),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("photo_file_id", sa.String(512), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("group_chat_id", sa.BigInteger, nullable=True),
        sa.Column("group_message_id", sa.BigInteger, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolver_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id"), nullable=True,
        ),
        sa.Column("resolution_note", sa.Text, nullable=True),
        sa.CheckConstraint(
            "category IN ('engineer','complaint','techsupport')",
            name="chk_support_category",
        ),
        sa.CheckConstraint(
            "status IN ('open','accepted','in_progress','resolved','rejected')",
            name="chk_support_status",
        ),
    )
    op.create_index(
        "idx_support_user_created", "support_requests",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_support_status_created", "support_requests",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_support_status_created", "support_requests")
    op.drop_index("idx_support_user_created", "support_requests")
    op.drop_table("support_requests")
