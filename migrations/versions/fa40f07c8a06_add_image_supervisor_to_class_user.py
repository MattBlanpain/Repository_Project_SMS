"""add image, supervisor to class User

Revision ID: fa40f07c8a06
Revises: 
Create Date: 2023-12-29 16:17:20.821500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa40f07c8a06'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
    with op.batch_alter_table('user', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('image_file', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('is_supervisor_of', sa.Integer(), nullable=True))
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=150),
               nullable=False)
        batch_op.alter_column('first_name',
               existing_type=sa.VARCHAR(length=150),
               type_=sa.String(length=20),
               existing_nullable=True)
        batch_op.alter_column('last_name',
               existing_type=sa.VARCHAR(length=150),
               type_=sa.String(length=20),
               existing_nullable=True)
        batch_op.create_foreign_key('fk_test_user_id_user', 'user', ['is_supervisor_of'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('last_name',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=150),
               existing_nullable=True)
        batch_op.alter_column('first_name',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=150),
               existing_nullable=True)
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=150),
               nullable=True)
        batch_op.drop_column('is_supervisor_of')
        batch_op.drop_column('image_file')

    # ### end Alembic commands ###