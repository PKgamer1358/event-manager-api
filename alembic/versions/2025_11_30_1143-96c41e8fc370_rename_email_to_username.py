"""rename_email_to_username

Revision ID: 96c41e8fc370
Revises: 2f78d6bdf1c8
Create Date: 2025-11-30 11:43:13.824233

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96c41e8fc370'
down_revision = '2f78d6bdf1c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename email column to username
    op.alter_column('users', 'email', new_column_name='username')


def downgrade() -> None:
    # Rename username column back to email
    op.alter_column('users', 'username', new_column_name='email')

