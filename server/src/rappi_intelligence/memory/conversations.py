"""SQLite-backed conversation history for chat sessions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from rappi_intelligence.shared.config import CONVERSATIONS_DB_PATH


@dataclass(frozen=True)
class ConversationMessage:
    """Single persisted conversation turn."""

    role: str
    content: str


class ConversationStore:
    """Persist message history keyed by conversation id."""

    def __init__(self, db_path: Path = CONVERSATIONS_DB_PATH) -> None:
        self.db_path = db_path
        self._initialize()

    def ensure_conversation(self, history_id: str | None = None) -> str:
        """Return an existing history id or create a new conversation."""

        if history_id and self._conversation_exists(history_id):
            return history_id

        new_history_id = history_id or uuid4().hex
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO conversations(history_id)
                VALUES (?)
                """,
                (new_history_id,),
            )
        return new_history_id

    def append_message(self, history_id: str, role: str, content: str) -> None:
        """Append one message to the conversation."""

        normalized_role = role.lower().strip()
        if normalized_role not in {"user", "assistant", "system"}:
            raise ValueError(f"Unsupported message role: {role}")
        if not content.strip():
            return

        self.ensure_conversation(history_id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_messages(history_id, role, content)
                VALUES (?, ?, ?)
                """,
                (history_id, normalized_role, content),
            )
            connection.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE history_id = ?
                """,
                (history_id,),
            )

    def get_messages(
        self,
        history_id: str,
        limit: int = 12,
    ) -> list[ConversationMessage]:
        """Return the most recent messages in chronological order."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE history_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (history_id, limit),
            ).fetchall()
        return [
            ConversationMessage(role=str(row["role"]), content=str(row["content"]))
            for row in reversed(rows)
        ]

    def _conversation_exists(self, history_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM conversations
                WHERE history_id = ?
                """,
                (history_id,),
            ).fetchone()
        return row is not None

    def _initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    history_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    history_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(history_id) REFERENCES conversations(history_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversation_messages_history
                ON conversation_messages(history_id, id)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
