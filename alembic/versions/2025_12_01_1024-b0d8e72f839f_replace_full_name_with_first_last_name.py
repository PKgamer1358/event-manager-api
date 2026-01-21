"""replace_full_name_with_first_last_name

Revision ID: b0d8e72f839f
Revises: 80c9fadf39db
Create Date: 2025-12-01 10:24:26.797792

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0d8e72f839f'
down_revision = '80c9fadf39db'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns
    op.add_column('users', sa.Column('first_name', sa.String(length=120), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=120), nullable=True))
    
    # Migrate existing full_name data (split by space, first word as first_name, rest as last_name)
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE users 
            SET first_name = SPLIT_PART(full_name, ' ', 1),
                last_name = SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1)
            WHERE full_name IS NOT NULL AND full_name != ''
        """)
    )
    connection.commit()
    
    # Drop old column
    op.drop_column('users', 'full_name')


def downgrade() -> None:
    # Add back full_name column
    op.add_column('users', sa.Column('full_name', sa.String(length=120), nullable=True))
    
    # Migrate data back (combine first_name and last_name)
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE users 
            SET full_name = CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, ''))
            WHERE first_name IS NOT NULL OR last_name IS NOT NULL
        """)
    )
    connection.commit()
    
    # Drop new columns
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')

