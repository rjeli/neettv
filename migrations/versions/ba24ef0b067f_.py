"""empty message

Revision ID: ba24ef0b067f
Revises: 0f7b57936d85
Create Date: 2020-01-20 05:27:07.973236

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba24ef0b067f'
down_revision = '0f7b57936d85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invite_code',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('code')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('invite_code')
    # ### end Alembic commands ###
