"""empty message

Revision ID: 15fe102c44be
Revises: 2dd643f35c2b
Create Date: 2014-11-03 11:51:45.696000

"""

# revision identifiers, used by Alembic.
revision = '15fe102c44be'
down_revision = '2dd643f35c2b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('member',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('users')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('created', mysql.DATETIME(), nullable=False),
    sa.Column('updated', mysql.DATETIME(), nullable=False),
    sa.Column('name', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('profile_url', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('access_token', mysql.VARCHAR(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )
    op.drop_table('member')
    ### end Alembic commands ###