"""add contests, contest_works, contest_scores

Revision ID: 20260424_0005
Revises: 20260424_0004
Create Date: 2026-04-24 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260424_0005"
down_revision = "20260424_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Add 'judge' to user role check constraint ---
    op.drop_constraint("chk_user_role", "users", type_="check")
    op.create_check_constraint(
        "chk_user_role", "users",
        "role IN ('customer','seller','admin','judge')",
    )

    # --- contests: active contest metadata (single row expected) ---
    op.create_table(
        "contests",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("judge_chat_id", sa.BigInteger, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Only one active contest at a time
    op.execute(
        "CREATE UNIQUE INDEX idx_contests_one_active ON contests(is_active) WHERE is_active = true"
    )

    # --- contest_works: a submission by a customer ---
    op.create_table(
        "contest_works",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "contest_id", UUID(as_uuid=True),
            sa.ForeignKey("contests.id"), nullable=False,
        ),
        sa.Column(
            "user_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id"), nullable=False,
        ),
        sa.Column("photo_file_id", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("group_chat_id", sa.BigInteger, nullable=True),
        sa.Column("group_message_id", sa.BigInteger, nullable=True),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column("average_score", sa.Numeric(4, 2), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending','scoring','finalized')",
            name="chk_work_status",
        ),
    )
    op.create_index(
        "idx_works_contest_user", "contest_works",
        ["contest_id", "user_id"],
    )
    op.create_index(
        "idx_works_status", "contest_works", ["status"],
    )

    # --- contest_scores: one row per judge-per-work, with 5 criteria ---
    op.create_table(
        "contest_scores",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "work_id", UUID(as_uuid=True),
            sa.ForeignKey("contest_works.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "judge_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id"), nullable=False,
        ),
        sa.Column("c1", sa.Integer, nullable=False),
        sa.Column("c2", sa.Integer, nullable=False),
        sa.Column("c3", sa.Integer, nullable=False),
        sa.Column("c4", sa.Integer, nullable=False),
        sa.Column("c5", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "c1 BETWEEN 1 AND 10 AND c2 BETWEEN 1 AND 10 AND "
            "c3 BETWEEN 1 AND 10 AND c4 BETWEEN 1 AND 10 AND c5 BETWEEN 1 AND 10",
            name="chk_score_range",
        ),
        sa.UniqueConstraint("work_id", "judge_id", name="uq_work_judge"),
    )
    op.create_index(
        "idx_scores_work", "contest_scores", ["work_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_scores_work", "contest_scores")
    op.drop_table("contest_scores")
    op.drop_index("idx_works_status", "contest_works")
    op.drop_index("idx_works_contest_user", "contest_works")
    op.drop_table("contest_works")
    op.execute("DROP INDEX IF EXISTS idx_contests_one_active")
    op.drop_table("contests")
    op.drop_constraint("chk_user_role", "users", type_="check")
    op.create_check_constraint(
        "chk_user_role", "users",
        "role IN ('customer','seller','admin')",
    )
