"""add_is_demo_flag

Revision ID: 4b5c6d7e8f9a
Revises: 3a4b5c6d7e8f
Create Date: 2026-09-11 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b5c6d7e8f9a'
down_revision: Union[str, Sequence[str], None] = '3a4b5c6d7e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add is_demo flag and index to articles."""
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.text('0'))
        )
        batch_op.create_index(
            batch_op.f('ix_articles_is_demo'),
            ['is_demo'],
            unique=False,
        )

    # Data migration: Deterministically identify the 16 curated seed/demo articles from seed.py
    seeded_demo_urls = (
        "'https://example.com/demo/articles/india-2nm-semiconductor-gujarat',"
        "'https://example.com/demo/articles/telangana-ai-city-masterplan',"
        "'https://example.com/demo/articles/isro-shukrayaan-venus-mission',"
        "'https://example.com/demo/articles/india-test-victory-lords',"
        "'https://example.com/demo/articles/western-ghats-corridor-expansion',"
        "'https://example.com/demo/articles/rbi-cross-border-upi-expansion',"
        "'https://example.com/demo/articles/ai-portable-tb-screening-rural',"
        "'https://example.com/demo/articles/delhi-quantum-computing-fellowship',"
        "'https://example.com/demo/articles/cyber-crime-deepfake-bust',"
        "'https://example.com/demo/articles/national-cinema-conclave-chennai',"
        "'https://example.com/demo/articles/rajasthan-stepwell-heritage-conservation',"
        "'https://example.com/demo/articles/un-methane-climate-treaty-geneva',"
        "'https://example.com/demo/articles/autonomous-commercial-aviation-milestone',"
        "'https://example.com/demo/articles/global-cbdc-interoperable-corridor',"
        "'https://example.com/demo/articles/jwst-water-vapor-exoplanet',"
        "'https://example.com/demo/articles/world-athletics-smart-stadiums'"
    )
    # Ensure all existing articles default to is_demo = 0
    op.execute("UPDATE articles SET is_demo = 0;")
    # Mark only the 16 curated seed articles (and any example.com demo variations) as demo
    op.execute(
        f"UPDATE articles SET is_demo = 1 "
        f"WHERE canonical_url IN ({seeded_demo_urls}) OR canonical_url LIKE '%example.com%';"
    )


def downgrade() -> None:
    """Downgrade schema to remove is_demo flag."""
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_articles_is_demo'))
        batch_op.drop_column('is_demo')
