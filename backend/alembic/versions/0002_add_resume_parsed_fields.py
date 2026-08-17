"""Add parsed resume data columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("parsed_skills", sa.JSON(), nullable=True))
    op.add_column("resumes", sa.Column("parsed_education", sa.JSON(), nullable=True))
    op.add_column(
        "resumes", sa.Column("parsed_experience_years", sa.Float(), nullable=True)
    )
    op.add_column(
        "resumes", sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("resumes", "parsed_at")
    op.drop_column("resumes", "parsed_experience_years")
    op.drop_column("resumes", "parsed_education")
    op.drop_column("resumes", "parsed_skills")
