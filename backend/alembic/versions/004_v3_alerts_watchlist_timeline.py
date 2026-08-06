"""Add transport_types, notification_policy, alert priority, watchlists, ignores, and timeline tables.

Revision ID: 004_v3_alerts_watchlist_timeline
Revises: 003_profiles_alerts
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision = "004_v3_alerts_watchlist_timeline"
down_revision = "003_profiles_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. TravelProfiles columns
    op.add_column(
        "travel_profiles",
        sa.Column("transport_types", ARRAY(sa.String(50)), nullable=True),
    )
    op.add_column(
        "travel_profiles",
        sa.Column(
            "notification_policy",
            sa.String(50),
            nullable=False,
            server_default="HIGH_AND_MUST_SEE",
        ),
    )

    # GIN index for transport_types array
    op.create_index(
        "ix_travel_profiles_transport_types",
        "travel_profiles",
        ["transport_types"],
        postgresql_using="gin",
    )

    # 2. AlertEvents columns
    op.add_column(
        "alert_events",
        sa.Column("priority_score", sa.Numeric(5, 2), nullable=True),
    )
    op.add_column(
        "alert_events",
        sa.Column("priority_level", sa.String(50), nullable=True),
    )
    op.add_column(
        "alert_events",
        sa.Column("reasons_json", JSONB, nullable=True),
    )

    op.create_index("ix_alert_events_priority_level", "alert_events", ["priority_level"])

    # 3. OfferWatchlists table
    op.create_table(
        "offer_watchlists",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_chat_id", sa.String(100), nullable=False),
        sa.Column(
            "offer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("last_notified_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("last_notified_deal_score", sa.Integer, nullable=True),
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
        sa.UniqueConstraint("user_chat_id", "offer_id", name="uq_user_watchlist_offer"),
    )
    op.create_index("ix_offer_watchlists_user_chat_id", "offer_watchlists", ["user_chat_id"])
    op.create_index("ix_offer_watchlists_offer_id", "offer_watchlists", ["offer_id"])

    # 4. OfferIgnores table
    op.create_table(
        "offer_ignores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_chat_id", sa.String(100), nullable=False),
        sa.Column(
            "offer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ignored_priority_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ignored_price", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "ignored_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_chat_id", "offer_id", name="uq_user_ignore_offer"),
    )
    op.create_index("ix_offer_ignores_user_chat_id", "offer_ignores", ["user_chat_id"])
    op.create_index("ix_offer_ignores_offer_id", "offer_ignores", ["offer_id"])

    # 5. AlertTimeline table
    op.create_table(
        "alert_timeline",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
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
        sa.Column("user_chat_id", sa.String(100), nullable=True),
        sa.Column("priority_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("priority_level", sa.String(50), nullable=False),
        sa.Column("reasons", JSONB, nullable=True),
        sa.Column("price_per_person", sa.Numeric(10, 2), nullable=False),
        sa.Column("deal_score", sa.Integer, nullable=True),
        sa.Column("value_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("notification_status", sa.String(50), nullable=False),
    )
    op.create_index("ix_alert_timeline_timestamp", "alert_timeline", ["timestamp"])
    op.create_index("ix_alert_timeline_offer_id", "alert_timeline", ["offer_id"])
    op.create_index("ix_alert_timeline_profile_id", "alert_timeline", ["profile_id"])
    op.create_index(
        "ix_alert_timeline_notification_status", "alert_timeline", ["notification_status"]
    )


def downgrade() -> None:
    op.drop_table("alert_timeline")
    op.drop_table("offer_ignores")
    op.drop_table("offer_watchlists")
    op.drop_index("ix_alert_events_priority_level", table_name="alert_events")
    op.drop_column("alert_events", "reasons_json")
    op.drop_column("alert_events", "priority_level")
    op.drop_column("alert_events", "priority_score")
    op.drop_index("ix_travel_profiles_transport_types", table_name="travel_profiles")
    op.drop_column("travel_profiles", "notification_policy")
    op.drop_column("travel_profiles", "transport_types")
