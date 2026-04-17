"""Tests for SQLite conversation memory."""

from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from rappi_intelligence.memory.conversations import ConversationStore


def test_conversation_store_creates_and_reads_messages() -> None:
    workspace_tmp = Path(".test_artifacts") / uuid4().hex
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    try:
        store = ConversationStore(db_path=workspace_tmp / "conversations.sqlite")

        history_id = store.ensure_conversation()
        store.append_message(history_id, "user", "Hola")
        store.append_message(history_id, "assistant", "Respuesta")

        messages = store.get_messages(history_id)

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hola"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Respuesta"
    finally:
        rmtree(workspace_tmp, ignore_errors=True)


def test_conversation_store_reuses_existing_history_id() -> None:
    workspace_tmp = Path(".test_artifacts") / uuid4().hex
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    try:
        store = ConversationStore(db_path=workspace_tmp / "conversations.sqlite")

        history_id = store.ensure_conversation("known-history")
        same_history_id = store.ensure_conversation("known-history")

        assert history_id == "known-history"
        assert same_history_id == "known-history"
    finally:
        rmtree(workspace_tmp, ignore_errors=True)
