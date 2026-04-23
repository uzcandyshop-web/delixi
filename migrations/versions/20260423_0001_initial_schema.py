"""initial schema with seed regions and tiers

Revision ID: 20260423_0001
Revises:
Create Date: 2026-04-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260423_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Need pgcrypto for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ---------- regions ----------
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(16), nullable=False, unique=True),
        sa.Column("name_ru", sa.String(128), nullable=False),
        sa.Column("name_uz", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
    )

    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200)),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="customer"),
        sa.Column("qr_token", sa.String(128), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("role IN ('customer','seller','admin')", name="chk_user_role"),
    )
    op.create_index("idx_users_region", "users", ["region_id"])
    op.create_index("idx_users_role", "users", ["role"])

    # ---------- bonus_tiers ----------
    op.create_table(
        "bonus_tiers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("min_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("max_amount", sa.Numeric(12, 2)),
        sa.Column("percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )

    # ---------- transactions ----------
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("bonus_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("bonus_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("amount > 0", name="chk_tx_amount_positive"),
    )
    op.create_index("idx_tx_customer", "transactions", ["customer_id", "created_at"])
    op.create_index("idx_tx_seller", "transactions", ["seller_id", "created_at"])
    op.create_index("idx_tx_region", "transactions", ["region_id", "created_at"])

    # ---------- bonus_ledger ----------
    op.create_table(
        "bonus_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delta", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("tx_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id")),
        sa.Column("redemption_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "reason IN ('purchase','redeem','adjust','expire')",
            name="chk_ledger_reason",
        ),
    )
    op.create_index("idx_ledger_user", "bonus_ledger", ["user_id", "created_at"])

    # ---------- prizes ----------
    op.create_table(
        "prizes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("cost_bonus", sa.Numeric(12, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
    )

    # ---------- redemptions ----------
    op.create_table(
        "redemptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("prize_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prizes.id"), nullable=False),
        sa.Column("cost_bonus", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("note", sa.Text()),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','issued')",
            name="chk_redemption_status",
        ),
    )

    # ---------- v_user_balance view ----------
    op.execute("""
        CREATE OR REPLACE VIEW v_user_balance AS
        SELECT u.id AS user_id,
               COALESCE(SUM(l.delta), 0) AS balance
        FROM users u
        LEFT JOIN bonus_ledger l ON l.user_id = u.id
        GROUP BY u.id;
    """)

    # ---------- seed: regions ----------
    op.bulk_insert(
        sa.table(
            "regions",
            sa.column("code", sa.String),
            sa.column("name_ru", sa.String),
            sa.column("name_uz", sa.String),
        ),
        [
            {"code": "TAS", "name_ru": "Ташкент", "name_uz": "Toshkent"},
            {"code": "SAM", "name_ru": "Самарканд", "name_uz": "Samarqand"},
            {"code": "BUH", "name_ru": "Бухара", "name_uz": "Buxoro"},
            {"code": "AND", "name_ru": "Андижан", "name_uz": "Andijon"},
            {"code": "FER", "name_ru": "Фергана", "name_uz": "Farg'ona"},
            {"code": "NAM", "name_ru": "Наманган", "name_uz": "Namangan"},
            {"code": "KAS", "name_ru": "Кашкадарья", "name_uz": "Qashqadaryo"},
            {"code": "SUR", "name_ru": "Сурхандарья", "name_uz": "Surxondaryo"},
            {"code": "SYR", "name_ru": "Сырдарья", "name_uz": "Sirdaryo"},
            {"code": "JIZ", "name_ru": "Джизак", "name_uz": "Jizzax"},
            {"code": "NAV", "name_ru": "Навои", "name_uz": "Navoiy"},
            {"code": "KHO", "name_ru": "Хорезм", "name_uz": "Xorazm"},
            {"code": "KAR", "name_ru": "Каракалпакстан", "name_uz": "Qoraqalpog'iston"},
            {"code": "TVI", "name_ru": "Ташкентская область", "name_uz": "Toshkent viloyati"},
        ],
    )

    # ---------- seed: default bonus tiers ----------
    op.bulk_insert(
        sa.table(
            "bonus_tiers",
            sa.column("min_amount", sa.Numeric),
            sa.column("max_amount", sa.Numeric),
            sa.column("percent", sa.Numeric),
        ),
        [
            {"min_amount": 0,        "max_amount": 500000,  "percent": 2},
            {"min_amount": 500000,   "max_amount": 2000000, "percent": 3},
            {"min_amount": 2000000,  "max_amount": None,    "percent": 5},
        ],
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_user_balance")
    op.drop_table("redemptions")
    op.drop_table("prizes")
    op.drop_index("idx_ledger_user", table_name="bonus_ledger")
    op.drop_table("bonus_ledger")
    op.drop_index("idx_tx_region", table_name="transactions")
    op.drop_index("idx_tx_seller", table_name="transactions")
    op.drop_index("idx_tx_customer", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("bonus_tiers")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_index("idx_users_region", table_name="users")
    op.drop_table("users")
    op.drop_table("regions")
