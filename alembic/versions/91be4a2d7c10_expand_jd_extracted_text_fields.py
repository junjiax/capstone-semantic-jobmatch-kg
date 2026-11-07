"""Expand JD extracted text columns.

Revision ID: 91be4a2d7c10
Revises: 43dff02d5e87
Create Date: 2026-11-04 10:48:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91be4a2d7c10"
down_revision: Union[str, Sequence[str], None] = "43dff02d5e87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "JD",
        "Expertise",
        existing_type=sa.String(length=200),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "JD",
        "Qualification",
        existing_type=sa.String(length=200),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "JD",
        "Responsibility",
        existing_type=sa.String(length=200),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "JD",
        "Responsibility",
        existing_type=sa.Text(),
        type_=sa.String(length=200),
        existing_nullable=True,
    )
    op.alter_column(
        "JD",
        "Qualification",
        existing_type=sa.Text(),
        type_=sa.String(length=200),
        existing_nullable=True,
    )
    op.alter_column(
        "JD",
        "Expertise",
        existing_type=sa.Text(),
        type_=sa.String(length=200),
        existing_nullable=True,
    )
