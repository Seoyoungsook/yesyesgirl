"""empty message

Revision ID: 28813e69abe7
Revises: 4b1481be346
Create Date: 2015-02-09 14:29:06.822000

"""

# revision identifiers, used by Alembic.
revision = '28813e69abe7'
down_revision = '4b1481be346'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('tags_list', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project', 'tags_list')
    ### end Alembic commands ###
