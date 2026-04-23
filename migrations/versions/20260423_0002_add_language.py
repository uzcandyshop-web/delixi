"""add language column to users

Revision ID: 20260423_0002
Revises: 20260423_0001
Create Date: 2026-04-23 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260423_0002"
down_revision = "20260423_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("language", sa.String(8), nullable=False, server_default="ru"),
    )
    op.create_check_constraint(
        "chk_user_language",
        "users",
        "language IN ('ru','uz')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_user_language", "users", type_="check")
    op.drop_column("users", "language")
