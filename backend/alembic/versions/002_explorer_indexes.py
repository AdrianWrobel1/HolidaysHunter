"""Add Explorer indexes for efficient filtering and sorting.

Revision ID: 002_explorer_indexes
Revises: 001_initial
"""

from alembic import op

revision = "002_explorer_indexes"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_offer_explorer",
        "offers",
        ["is_available", "country", "departure_date", "price_per_person"],
    )
    op.create_index("ix_offer_region", "offers", ["region"])
    op.create_index("ix_offer_departure_city", "offers", ["departure_city"])
    op.create_index("ix_offer_duration", "offers", ["duration_nights"])
    op.create_index("ix_offer_meal_type", "offers", ["meal_type"])


def downgrade() -> None:
    op.drop_index("ix_offer_meal_type", table_name="offers")
    op.drop_index("ix_offer_duration", table_name="offers")
    op.drop_index("ix_offer_departure_city", table_name="offers")
    op.drop_index("ix_offer_region", table_name="offers")
    op.drop_index("ix_offer_explorer", table_name="offers")
