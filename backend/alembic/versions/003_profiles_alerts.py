"""Add travel_profiles and alert_events tables.

Revision ID: 003_profiles_alerts
Revises: 002_explorer_indexes
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision = "003_profiles_alerts"
down_revision = "002_explorer_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "travel_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("countries", ARRAY(sa.String(100)), nullable=True),
        sa.Column("regions", ARRAY(sa.String(200)), nullable=True),
        sa.Column("departure_cities", ARRAY(sa.String(100)), nullable=True),
        sa.Column("date_from", sa.Date, nullable=True),
        sa.Column("date_to", sa.Date, nullable=True),
        sa.Column("duration_min", sa.Integer, nullable=True),
        sa.Column("duration_max", sa.Integer, nullable=True),
        sa.Column("budget_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("adults", sa.Integer, nullable=True),
        sa.Column("children", sa.Integer, nullable=True),
        sa.Column("hotel_stars_min", sa.Numeric(2, 1), nullable=True),
        sa.Column("meal_types", ARRAY(sa.String(50)), nullable=True),
        sa.Column("providers", ARRAY(sa.String(50)), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "alert_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "offer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "profile_id",
            UUID(as_uuid=True),
            sa.ForeignKey("travel_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("message", sa.String(1000), nullable=False),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_alert_event_offer_id", "alert_events", ["offer_id"])
    op.create_index("ix_alert_event_profile_id", "alert_events", ["profile_id"])
    op.create_index("ix_alert_event_alert_type", "alert_events", ["alert_type"])
    op.create_index("ix_alert_event_is_read", "alert_events", ["is_read"])
    op.create_index("ix_alert_event_triggered_at", "alert_events", ["triggered_at"])


def downgrade() -> None:
    op.drop_index("ix_alert_event_triggered_at", table_name="alert_events")
    op.drop_index("ix_alert_event_is_read", table_name="alert_events")
    op.drop_index("ix_alert_event_alert_type", table_name="alert_events")
    op.drop_index("ix_alert_event_profile_id", table_name="alert_events")
    op.drop_index("ix_alert_event_offer_id", table_name="alert_events")
    op.drop_table("alert_events")
    op.drop_table("travel_profiles")
