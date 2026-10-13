"""Subscriber signup source and lifecycle timestamps

Additive only: nullable columns, nothing dropped or renamed, so a running
container on the previous code keeps working while this applies.

Revision ID: 002
Revises: 001
Create Date: 2026-10-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subscribers", sa.Column("signup_referrer", sa.String(500), nullable=True))
    op.add_column("subscribers", sa.Column("signup_utm_source", sa.String(100), nullable=True))
    op.add_column("subscribers", sa.Column("signup_utm_medium", sa.String(100), nullable=True))
    op.add_column("subscribers", sa.Column("signup_utm_campaign", sa.String(100), nullable=True))
    op.add_column("subscribers", sa.Column("signup_landing_path", sa.String(200), nullable=True))
    op.add_column("subscribers", sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscribers", sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("subscribers", "unsubscribed_at")
    op.drop_column("subscribers", "confirmed_at")
    op.drop_column("subscribers", "signup_landing_path")
    op.drop_column("subscribers", "signup_utm_campaign")
    op.drop_column("subscribers", "signup_utm_medium")
    op.drop_column("subscribers", "signup_utm_source")
    op.drop_column("subscribers", "signup_referrer")
