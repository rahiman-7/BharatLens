"""add_story_groups

Revision ID: 3a4b5c6d7e8f
Revises: 2f3a05526c9d
Create Date: 2026-09-11 01:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a4b5c6d7e8f'
down_revision: Union[str, Sequence[str], None] = '2f3a05526c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add story_groups and article relationships."""
    # 1. Create story_groups table
    op.create_table(
        'story_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('representative_article_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['representative_article_id'],
            ['articles.id'],
            name='fk_story_groups_rep_article',
            ondelete='SET NULL',
            use_alter=True,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('story_groups', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_story_groups_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_story_groups_representative_article_id'), ['representative_article_id'], unique=False)

    # 2. Add story_group_id column and foreign key to articles table
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('story_group_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_articles_story_group',
            'story_groups',
            ['story_group_id'],
            ['id'],
            ondelete='SET NULL',
            use_alter=True,
        )
        batch_op.create_index(batch_op.f('ix_articles_story_group_id'), ['story_group_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema to remove story_groups."""
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_articles_story_group_id'))
        batch_op.drop_constraint('fk_articles_story_group', type_='foreignkey')
        batch_op.drop_column('story_group_id')

    with op.batch_alter_table('story_groups', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_story_groups_representative_article_id'))
        batch_op.drop_index(batch_op.f('ix_story_groups_id'))

    op.drop_table('story_groups')
