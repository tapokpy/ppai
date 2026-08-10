"""business rules + message extra_data

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_business_rules_category", "business_rules", ["category"])
    op.create_index("ix_business_rules_is_active", "business_rules", ["is_active"])

    op.add_column("messages", sa.Column("extra_data", postgresql.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "extra_data")
    op.drop_index("ix_business_rules_is_active", table_name="business_rules")
    op.drop_index("ix_business_rules_category", table_name="business_rules")
    op.drop_table("business_rules")
