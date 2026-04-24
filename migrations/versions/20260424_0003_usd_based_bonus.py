"""add exchange rates and usd_rate to transactions

Revision ID: 20260424_0003
Revises: 20260423_0002
Create Date: 2026-04-24 10:00:00.000000
"""
from decimal import Decimal
from alembic import op
import sqlalchemy as sa

revision = "20260424_0003"
down_revision = "20260423_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- new table: exchange_rates ---
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("rate", sa.Numeric(14, 4), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="cbu.uz"),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("effective_date", sa.Date(), nullable=False),
    )
    op.create_index(
        "idx_exchange_rates_currency_date",
        "exchange_rates",
        ["currency", "effective_date"],
        unique=True,
    )

    # --- add usd_rate column to transactions ---
    op.add_column(
        "transactions",
        sa.Column("usd_rate", sa.Numeric(14, 4), nullable=True),
    )

    # --- seed fallback rate (today's approximate value) ---
    # Using a fresh rate as of late April 2026. The bot will refresh this
    # automatically on first start via fetch_cbu_rate().
    op.execute(
        "INSERT INTO exchange_rates (currency, rate, source, effective_date) "
        "VALUES ('USD', 12190.43, 'seed', CURRENT_DATE) "
        "ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.drop_column("transactions", "usd_rate")
    op.drop_index("idx_exchange_rates_currency_date", table_name="exchange_rates")
    op.drop_table("exchange_rates")
