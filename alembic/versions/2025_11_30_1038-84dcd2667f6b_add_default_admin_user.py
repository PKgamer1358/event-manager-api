"""add_default_admin_user

Revision ID: 84dcd2667f6b
Revises: eb5bd3b90022
Create Date: 2025-11-30 10:38:24.130389

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import bcrypt


# revision identifiers, used by Alembic.
revision = '84dcd2667f6b'
down_revision = 'eb5bd3b90022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a connection to execute raw SQL
    connection = op.get_bind()
    
    # Hash the password using bcrypt
    password = "Super@123"
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
    
    # Check if the user already exists
    result = connection.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": "sadmin"}
    )
    
    if result.fetchone() is None:
        # Insert the default admin user
        connection.execute(
            sa.text("""
                INSERT INTO users (email, full_name, password_hash, is_admin, created_at)
                VALUES (:email, :full_name, :password_hash, :is_admin, :created_at)
            """),
            {
                "email": "sadmin",
                "full_name": "Super Admin",
                "password_hash": password_hash,
                "is_admin": True,
                "created_at": datetime.utcnow()
            }
        )
        connection.commit()


def downgrade() -> None:
    # Remove the default admin user
    connection = op.get_bind()
    connection.execute(
        sa.text("DELETE FROM users WHERE email = :email"),
        {"email": "sadmin"}
    )
    connection.commit()
