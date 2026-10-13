"""Email delivery outcomes reported by Resend

Additive only: one nullable column on notifications_sent and a new table,
so a container still running the previous code keeps working while this
applies.

Revision ID: 003
Revises: 002
Create Date: 2026-10-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications_sent",
        sa.Column("provider_message_id", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_notifications_sent_provider_message_id",
        "notifications_sent",
        ["provider_message_id"],
    )
    op.create_table(
        "email_events",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("svix_id", sa.String(64), nullable=False, unique=True),
        sa.Column("provider_message_id", sa.String(64), nullable=False),
        sa.Column(
            "notification_id",
            sa.Uuid,
            sa.ForeignKey("notifications_sent.id"),
            nullable=True,
        ),
        sa.Column(
            "subscriber_id",
            sa.Uuid,
            sa.ForeignKey("subscribers.id"),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.Enum(
                "delivered",
                "delivery_delayed",
                "bounced",
                "complained",
                name="emaileventtype",
            ),
            nullable=False,
        ),
        sa.Column("bounce_type", sa.String(50), nullable=True),
        sa.Column("detail", sa.String(500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_email_events_provider_message_id", "email_events", ["provider_message_id"]
    )
    op.create_index("ix_email_events_notification_id", "email_events", ["notification_id"])


def downgrade() -> None:
    op.drop_index("ix_email_events_notification_id", table_name="email_events")
    op.drop_index("ix_email_events_provider_message_id", table_name="email_events")
    op.drop_table("email_events")
    op.execute("DROP TYPE IF EXISTS emaileventtype")
    op.drop_index(
        "ix_notifications_sent_provider_message_id", table_name="notifications_sent"
    )
    op.drop_column("notifications_sent", "provider_message_id")
