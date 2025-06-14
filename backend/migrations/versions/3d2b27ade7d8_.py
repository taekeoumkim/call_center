"""empty message

Revision ID: 3d2b27ade7d8
Revises: 
Create Date: 2025-06-03 23:30:20.596859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d2b27ade7d8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('token_blocklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('jti', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_token_blocklist_jti'), ['jti'], unique=True)

    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('client_calls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.String(length=20), nullable=False),
    sa.Column('audio_file_path', sa.String(length=255), nullable=True),
    sa.Column('transcribed_text', sa.Text(), nullable=True),
    sa.Column('risk_level', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('assigned_counselor_id', sa.Integer(), nullable=True),
    sa.Column('received_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assigned_counselor_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('encrypted_files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('file_type', sa.String(length=10), nullable=False),
    sa.Column('file_storage_path', sa.String(length=255), nullable=False),
    sa.Column('nonce_for_file', sa.LargeBinary(), nullable=False),
    sa.Column('encrypted_dek_trad', sa.LargeBinary(), nullable=False),
    sa.Column('pqc_kem_ciphertext', sa.LargeBinary(), nullable=False),
    sa.Column('nonce_for_dek_encryption', sa.LargeBinary(), nullable=False),
    sa.Column('encrypted_dek_by_pqc_shared_secret', sa.LargeBinary(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('file_storage_path')
    )
    op.create_table('consultation_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_call_id', sa.Integer(), nullable=False),
    sa.Column('counselor_id', sa.Integer(), nullable=False),
    sa.Column('encrypted_client_name', sa.LargeBinary(), nullable=True),
    sa.Column('encrypted_client_age', sa.LargeBinary(), nullable=True),
    sa.Column('encrypted_memo_text', sa.LargeBinary(), nullable=True),
    sa.Column('encrypted_transcribed_text', sa.LargeBinary(), nullable=True),
    sa.Column('encrypted_dek_trad', sa.LargeBinary(), nullable=True),
    sa.Column('pqc_kem_ciphertext', sa.LargeBinary(), nullable=True),
    sa.Column('pqc_secret_key', sa.LargeBinary(), nullable=True),
    sa.Column('nonce_for_dek_encryption', sa.LargeBinary(), nullable=True),
    sa.Column('encrypted_dek_by_pqc_shared_secret', sa.LargeBinary(), nullable=True),
    sa.Column('client_gender', sa.String(length=10), nullable=True),
    sa.Column('risk_level_recorded', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_call_id'], ['client_calls.id'], ),
    sa.ForeignKeyConstraint(['counselor_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('client_call_id')
    )
    op.create_table('file_permissions',
    sa.Column('file_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('granted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['encrypted_files.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('file_id', 'user_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('file_permissions')
    op.drop_table('consultation_reports')
    op.drop_table('encrypted_files')
    op.drop_table('client_calls')
    op.drop_table('users')
    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_token_blocklist_jti'))

    op.drop_table('token_blocklist')
    # ### end Alembic commands ###
