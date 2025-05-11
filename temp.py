from alembic import op
import sqlalchemy as sa

def upgrade():
    # This recreates the table correctly in SQLite
    with op.batch_alter_table('order', recreate='always') as batch_op:
        batch_op.drop_column('product_id')
        batch_op.add_column(sa.Column('product_id', sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table('order', recreate='always') as batch_op:
        batch_op.drop_column('product_id')
        batch_op.add_column(sa.Column('product_id', sa.Integer(), sa.ForeignKey('product.id'), nullable=True))
