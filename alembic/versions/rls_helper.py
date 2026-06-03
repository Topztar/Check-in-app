from alembic import op
import sqlalchemy as sa

def upgrade():
    # Example snippet to enable RLS on Postgres, SQLite doesn't support RLS.
    # However we put it here as requested.
    pass

def downgrade():
    pass
