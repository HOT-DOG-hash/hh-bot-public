"""unify schema

Revision ID: 20250924_unify_schema
Revises: 
Create Date: 2025-09-24 18:00:00.000000
"""

from __future__ import annotations

from typing import Dict, Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20250924_unify_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename_legacy_tables(table_names: set[str]) -> Dict[str, str]:
    renamed: Dict[str, str] = {}
    for original in ("user", "users"):
        if original in table_names:
            legacy = "users_legacy"
            op.rename_table(original, legacy)
            table_names.add(legacy)
            table_names.discard(original)
            renamed["users"] = legacy
            break
    for original in ("resume", "resumes"):
        if original in table_names:
            legacy = "resumes_legacy"
            op.rename_table(original, legacy)
            table_names.add(legacy)
            table_names.discard(original)
            renamed["resumes"] = legacy
            break
    if "search_queries" in table_names:
        legacy = "search_queries_legacy"
        op.rename_table("search_queries", legacy)
        table_names.add(legacy)
        table_names.discard("search_queries")
        renamed["search_queries"] = legacy
    return renamed


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    legacy = _rename_legacy_tables(existing)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_id", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("tg_id", name="uq_users_tg_id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_last_activity", "users", ["last_activity"], unique=False)

    op.create_table(
        "search_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column("query", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_search_queries_user_id", "search_queries", ["user_id"], unique=False)
    op.create_index("ix_search_queries_chat_id", "search_queries", ["chat_id"], unique=False)
    op.create_index("ix_search_queries_created_at", "search_queries", ["created_at"], unique=False)

    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"], unique=False)
    op.create_index("ix_resumes_created_at", "resumes", ["created_at"], unique=False)

    users_map_by_legacy_id: Dict[int, int] = {}
    users_map_by_chat: Dict[str, int] = {}

    if "users" in legacy.values():
        # nothing to migrate
        pass

    if legacy.get("users"):
        rows = list(bind.execute(sa.text(f"SELECT * FROM {legacy['users']}" )).mappings())
        for row in rows:
            chat_id_value = None
            if "tg_id" in row and row["tg_id"]:
                chat_id_value = row["tg_id"]
            elif "chat_id" in row and row["chat_id"] is not None:
                chat_id_value = str(row["chat_id"])
            if chat_id_value is None:
                continue
            tg_id = str(chat_id_value)
            is_active = row.get("is_active", True)
            last_activity = row.get("last_activity")
            created_at = row.get("created_at")
            updated_at = row.get("updated_at")
            result = bind.execute(
                sa.text(
                    """
                    INSERT INTO users (tg_id, is_active, last_activity, created_at, updated_at)
                    VALUES (:tg_id, :is_active, COALESCE(:last_activity, CURRENT_TIMESTAMP), COALESCE(:created_at, CURRENT_TIMESTAMP), :updated_at)
                    RETURNING id
                    """
                ),
                {
                    "tg_id": tg_id,
                    "is_active": is_active if is_active is not None else True,
                    "last_activity": last_activity,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
            new_id = int(result.scalar_one())
            legacy_id = row.get("id")
            if legacy_id is not None:
                users_map_by_legacy_id[int(legacy_id)] = new_id
            users_map_by_chat[tg_id] = new_id
        op.drop_table(legacy["users"])

    def _ensure_user_for_chat(chat_id: Union[int, str, None]) -> int | None:
        if chat_id is None:
            return None
        key = str(chat_id)
        if key in users_map_by_chat:
            return users_map_by_chat[key]
        result = bind.execute(
            sa.text(
                """
                INSERT INTO users (tg_id, is_active, last_activity, created_at, updated_at)
                VALUES (:tg_id, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (tg_id) DO UPDATE SET tg_id = EXCLUDED.tg_id
                RETURNING id
                """
            ),
            {"tg_id": key},
        )
        new_id = int(result.scalar_one())
        users_map_by_chat[key] = new_id
        return new_id

    if legacy.get("resumes"):
        rows = list(bind.execute(sa.text(f"SELECT * FROM {legacy['resumes']}" )).mappings())
        for row in rows:
            target_user_id = None
            legacy_user_id = row.get("user_id")
            if legacy_user_id is not None and legacy_user_id in users_map_by_legacy_id:
                target_user_id = users_map_by_legacy_id[int(legacy_user_id)]
            else:
                target_user_id = _ensure_user_for_chat(row.get("chat_id"))
            if target_user_id is None:
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO resumes (id, user_id, title, text, file_path, created_at, updated_at)
                    VALUES (:id, :user_id, :title, :text, :file_path, COALESCE(:created_at, CURRENT_TIMESTAMP), :updated_at)
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": row.get("id"),
                    "user_id": target_user_id,
                    "title": row.get("title"),
                    "text": row.get("text"),
                    "file_path": row.get("file_path"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                },
            )
        op.drop_table(legacy["resumes"])

    if legacy.get("search_queries"):
        rows = list(bind.execute(sa.text(f"SELECT * FROM {legacy['search_queries']}" )).mappings())
        for row in rows:
            target_user_id = None
            legacy_user_id = row.get("user_id")
            if legacy_user_id is not None and legacy_user_id in users_map_by_legacy_id:
                target_user_id = users_map_by_legacy_id[int(legacy_user_id)]
            else:
                target_user_id = _ensure_user_for_chat(row.get("chat_id"))
            if target_user_id is None:
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO search_queries (id, user_id, chat_id, query, created_at)
                    VALUES (:id, :user_id, :chat_id, :query, COALESCE(:created_at, CURRENT_TIMESTAMP))
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": row.get("id"),
                    "user_id": target_user_id,
                    "chat_id": row.get("chat_id"),
                    "query": row.get("query"),
                    "created_at": row.get("created_at"),
                },
            )
        op.drop_table(legacy["search_queries"])


def downgrade() -> None:
    op.drop_index("ix_resumes_created_at", table_name="resumes")
    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")

    op.drop_index("ix_search_queries_created_at", table_name="search_queries")
    op.drop_index("ix_search_queries_chat_id", table_name="search_queries")
    op.drop_index("ix_search_queries_user_id", table_name="search_queries")
    op.drop_table("search_queries")

    op.drop_index("ix_users_last_activity", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
