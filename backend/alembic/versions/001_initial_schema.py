"""Initial schema — offers and price_history tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-08-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "offers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("region", sa.String(200), nullable=True),
        sa.Column("city", sa.String(200), nullable=True),
        sa.Column("hotel_name", sa.String(500), nullable=False),
        sa.Column("hotel_stars", sa.Numeric(2, 1), nullable=True),
        sa.Column("hotel_rating", sa.Numeric(3, 1), nullable=True),
        sa.Column("departure_date", sa.Date, nullable=False),
        sa.Column("return_date", sa.Date, nullable=False),
        sa.Column("duration_nights", sa.Integer, nullable=False),
        sa.Column("departure_city", sa.String(100), nullable=False),
        sa.Column("adults", sa.Integer, nullable=False),
        sa.Column("children", sa.Integer, nullable=False, server_default="0"),
        sa.Column("meal_type", sa.String(50), nullable=False),
        sa.Column("transport_type", sa.String(50), nullable=False),
        sa.Column("price_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_per_person", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PLN"),
        sa.Column("offer_url", sa.String(2000), nullable=False),
        sa.Column("image_url", sa.String(2000), nullable=True),
        sa.Column("travel_score", sa.Integer, nullable=True),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "provider",
            "external_id",
            "departure_date",
            "departure_city",
            "adults",
            "children",
            name="uq_offer_identity",
        ),
    )

    op.create_index("ix_offer_provider", "offers", ["provider"])
    op.create_index("ix_offer_country", "offers", ["country"])
    op.create_index("ix_offer_departure_date", "offers", ["departure_date"])
    op.create_index("ix_offer_price_per_person", "offers", ["price_per_person"])
    op.create_index("ix_offer_travel_score", "offers", ["travel_score"])
    op.create_index("ix_offer_is_available", "offers", ["is_available"])

    op.create_table(
        "price_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "offer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("price_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_per_person", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_price_history_offer_id", "price_history", ["offer_id"])
    op.create_index("ix_price_history_recorded_at", "price_history", ["recorded_at"])


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("offers")
