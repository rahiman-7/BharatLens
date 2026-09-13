"""add_language_code

Revision ID: 5c6d7e8f9a0b
Revises: 4b5c6d7e8f9a
Create Date: 2026-09-12 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c6d7e8f9a0b'
down_revision: Union[str, Sequence[str], None] = '4b5c6d7e8f9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add language_code column and composite index."""
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('language_code', sa.String(length=10), nullable=False, server_default='en')
        )
        batch_op.create_index(
            batch_op.f('ix_articles_language_code'),
            ['language_code'],
            unique=False,
        )
        batch_op.create_index(
            'idx_articles_state_lang_published',
            ['state', 'language_code', 'published_at'],
            unique=False,
        )

    # Ensure all existing articles default to language_code = 'en'
    op.execute("UPDATE articles SET language_code = 'en' WHERE language_code IS NULL OR language_code = '';")


def downgrade() -> None:
    """Downgrade schema to remove language_code column and indexes."""
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_index('idx_articles_state_lang_published')
        batch_op.drop_index(batch_op.f('ix_articles_language_code'))
        batch_op.drop_column('language_code')
