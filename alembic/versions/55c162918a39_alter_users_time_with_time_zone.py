"""alter users time with time zone

Revision ID: 55c162918a39
Revises: 
Create Date: 2015-12-12 10:46:56.684989

"""

# revision identifiers, used by Alembic.
revision = '55c162918a39'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('users', 'last_login_date',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(timezone=False))
    op.alter_column('users', 'registered_date',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(timezone=False))

def downgrade():
    pass
