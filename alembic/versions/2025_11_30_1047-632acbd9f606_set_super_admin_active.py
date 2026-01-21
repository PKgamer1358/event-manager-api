"""set_super_admin_active

Revision ID: 632acbd9f606
Revises: e4d68972415e
Create Date: 2025-11-30 10:47:14.550419

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '632acbd9f606'
down_revision = 'e4d68972415e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set super admin user as active
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET is_active = :is_active WHERE email = :email"),
        {"is_active": True, "email": "sadmin"}
    )
    connection.commit()


def downgrade() -> None:
    # Set super admin user as inactive
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET is_active = :is_active WHERE email = :email"),
        {"is_active": False, "email": "sadmin"}
    )
    connection.commit()

