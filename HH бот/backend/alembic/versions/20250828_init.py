from alembic import op
import sqlalchemy as sa

revision = "20250828_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, unique=True, index=True),
        sa.Column("last_activity", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_table(
        "search_queries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, index=True),
        sa.Column("query", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, index=True),
        sa.Column("text", sa.Text, nullable=True),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )

def downgrade():
    op.drop_table("resumes")
    op.drop_table("search_queries")
    op.drop_table("users")
