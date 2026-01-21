"""add category and club to events

Revision ID: cf559d72b2b3
Revises: b0d8e72f839f
Create Date: 2026-01-03 16:31:37.913083

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cf559d72b2b3'
down_revision = 'b0d8e72f839f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    
   # 1. Add columns as nullable
 op.add_column('events', sa.Column('category', sa.String(), nullable=True))
 op.add_column('events', sa.Column('club', sa.String(), nullable=True))

# 2. Backfill existing rows
 op.execute("UPDATE events SET category = 'Technical' WHERE category IS NULL")

# 3. Enforce NOT NULL
 op.alter_column('events', 'category', nullable=False)


   
    # ### end Alembic commands ###


def downgrade() -> None:
    
    op.drop_column('events', 'club')
    op.drop_column('events', 'category')
