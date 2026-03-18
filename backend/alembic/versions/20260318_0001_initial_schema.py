"""initial schema

Revision ID: 20260318_0001
Revises:
Create Date: 2026-03-18 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "20260318_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "instances",
        sa.Column("instance_name", sa.String(length=120), nullable=False),
        sa.Column("instance_external_id", sa.String(length=150), nullable=True),
        sa.Column("owner_jid", sa.String(length=150), nullable=True),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("profile_name", sa.String(length=255), nullable=True),
        sa.Column("profile_pic_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_name"),
    )
    op.create_index("ix_instances_instance_name", "instances", ["instance_name"], unique=False)

    op.create_table(
        "contacts",
        sa.Column("instance_id", sa.String(), nullable=False),
        sa.Column("remote_jid", sa.String(length=180), nullable=False),
        sa.Column("push_name", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("profile_pic_url", sa.String(length=1024), nullable=True),
        sa.Column("is_business", sa.Boolean(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id", "remote_jid", name="uq_contacts_instance_remote_jid"),
    )
    op.create_index("ix_contacts_instance_id", "contacts", ["instance_id"], unique=False)

    op.create_table(
        "chats",
        sa.Column("instance_id", sa.String(), nullable=False),
        sa.Column("remote_jid", sa.String(length=180), nullable=False),
        sa.Column("chat_name", sa.String(length=255), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unread_count", sa.Integer(), nullable=False),
        sa.Column("is_group", sa.Boolean(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id", "remote_jid", name="uq_chats_instance_remote_jid"),
    )
    op.create_index("ix_chats_instance_id", "chats", ["instance_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("instance_id", sa.String(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=True),
        sa.Column("message_external_id", sa.String(length=255), nullable=False),
        sa.Column("remote_jid", sa.String(length=180), nullable=False),
        sa.Column("from_me", sa.Boolean(), nullable=False),
        sa.Column("sender_jid", sa.String(length=180), nullable=True),
        sa.Column("sender_name", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("message_type", sa.String(length=40), nullable=False),
        sa.Column("media_url", sa.String(length=1024), nullable=True),
        sa.Column("media_mimetype", sa.String(length=120), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("embedding", Vector(dim=384), nullable=True),
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id", "message_external_id", name="uq_messages_instance_external"),
    )
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"], unique=False)
    op.create_index("ix_messages_instance_id", "messages", ["instance_id"], unique=False)
    op.create_index("ix_messages_remote_jid", "messages", ["remote_jid"], unique=False)
    op.create_index("ix_messages_timestamp", "messages", ["timestamp"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_messages_embedding "
        "ON messages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "batch_messages",
        sa.Column("instance_id", sa.String(), nullable=False),
        sa.Column("recipients", sa.JSON(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("sent_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_batch_messages_instance_id", "batch_messages", ["instance_id"], unique=False)

    op.create_table(
        "scheduled_messages",
        sa.Column("instance_id", sa.String(), nullable=False),
        sa.Column("recipients", sa.JSON(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=40), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("sent_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("error_log", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduled_messages_instance_id", "scheduled_messages", ["instance_id"], unique=False)
    op.create_index("ix_scheduled_messages_scheduled_at", "scheduled_messages", ["scheduled_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scheduled_messages_scheduled_at", table_name="scheduled_messages")
    op.drop_index("ix_scheduled_messages_instance_id", table_name="scheduled_messages")
    op.drop_table("scheduled_messages")

    op.drop_index("ix_batch_messages_instance_id", table_name="batch_messages")
    op.drop_table("batch_messages")

    op.drop_index("ix_messages_timestamp", table_name="messages")
    op.drop_index("ix_messages_remote_jid", table_name="messages")
    op.drop_index("ix_messages_instance_id", table_name="messages")
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.execute("DROP INDEX IF EXISTS ix_messages_embedding")
    op.drop_table("messages")

    op.drop_index("ix_chats_instance_id", table_name="chats")
    op.drop_table("chats")

    op.drop_index("ix_contacts_instance_id", table_name="contacts")
    op.drop_table("contacts")

    op.drop_index("ix_instances_instance_name", table_name="instances")
    op.drop_table("instances")
