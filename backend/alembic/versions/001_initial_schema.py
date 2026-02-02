"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscribers",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), unique=True, nullable=True),
        sa.Column("phone", sa.String(), unique=True, nullable=True),
        sa.Column(
            "notification_preference",
            sa.Enum("email", "sms", "both", name="notificationpreference"),
            nullable=False,
        ),
        sa.Column("unsubscribe_token", sa.String(), unique=True, nullable=False),
        sa.Column("confirmed", sa.Boolean(), default=False, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
    )

    op.create_table(
        "king_tide_events",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "event_datetime", sa.DateTime(timezone=True), nullable=False, index=True
        ),
        sa.Column("predicted_height", sa.Float(), nullable=False),
        sa.Column("station_id", sa.String(), nullable=False),
        sa.Column(
            "seven_day_alert_sent", sa.Boolean(), default=False, nullable=False
        ),
        sa.Column(
            "forty_eight_hour_alert_sent", sa.Boolean(), default=False, nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
    )

    op.create_table(
        "notifications_sent",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "subscriber_id",
            sa.Uuid,
            sa.ForeignKey("subscribers.id"),
            nullable=False,
        ),
        sa.Column(
            "king_tide_event_id",
            sa.Uuid,
            sa.ForeignKey("king_tide_events.id"),
            nullable=True,
        ),
        sa.Column(
            "notification_type",
            sa.Enum(
                "seven_day_alert",
                "forty_eight_hour_reminder",
                "confirmation",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column(
            "sent_at", sa.DateTime(timezone=True), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("notifications_sent")
    op.drop_table("king_tide_events")
    op.drop_table("subscribers")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS notificationpreference")
