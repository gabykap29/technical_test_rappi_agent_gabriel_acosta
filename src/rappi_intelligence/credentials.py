"""Encrypted local credential storage for LLM providers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet

from rappi_intelligence.config import FERNET_KEY_PATH, SECRETS_DB_PATH


@dataclass(frozen=True)
class ProviderCredential:
    """Stored configuration for an LLM provider."""

    provider: str
    model: str
    has_api_key: bool


class CredentialStore:
    """Persist encrypted provider API keys in a local SQLite database."""

    def __init__(
        self,
        db_path: Path = SECRETS_DB_PATH,
        key_path: Path = FERNET_KEY_PATH,
    ) -> None:
        self.db_path = db_path
        self.key_path = key_path
        self.fernet = Fernet(self._load_or_create_key())
        self._initialize()

    def save_provider(
        self,
        provider: str,
        model: str,
        api_key: str | None = None,
    ) -> None:
        """Create or update provider settings."""

        provider = provider.lower().strip()
        encrypted_key = self._encrypt(api_key) if api_key else self.get_encrypted_key(
            provider
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO provider_credentials(provider, model, encrypted_api_key)
                VALUES (?, ?, ?)
                ON CONFLICT(provider)
                DO UPDATE SET
                    model = excluded.model,
                    encrypted_api_key = excluded.encrypted_api_key,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (provider, model, encrypted_key),
            )

    def get_api_key(self, provider: str) -> str | None:
        """Return decrypted API key for the provider, if present."""

        encrypted_key = self.get_encrypted_key(provider)
        if not encrypted_key:
            return None
        return self.fernet.decrypt(encrypted_key).decode("utf-8")

    def get_model(self, provider: str) -> str | None:
        """Return configured model for the provider."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT model FROM provider_credentials WHERE provider = ?",
                (provider.lower().strip(),),
            ).fetchone()
        return str(row["model"]) if row else None

    def list_providers(self) -> list[ProviderCredential]:
        """List saved provider configurations without exposing secrets."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT provider, model, encrypted_api_key
                FROM provider_credentials
                ORDER BY provider
                """
            ).fetchall()
        return [
            ProviderCredential(
                provider=str(row["provider"]),
                model=str(row["model"]),
                has_api_key=bool(row["encrypted_api_key"]),
            )
            for row in rows
        ]

    def get_encrypted_key(self, provider: str) -> bytes | None:
        """Return encrypted key bytes without decrypting them."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT encrypted_api_key
                FROM provider_credentials
                WHERE provider = ?
                """,
                (provider.lower().strip(),),
            ).fetchone()
        if not row or not row["encrypted_api_key"]:
            return None
        return bytes(row["encrypted_api_key"])

    def _initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_credentials (
                    provider TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    encrypted_api_key BLOB,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _load_or_create_key(self) -> bytes:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            return self.key_path.read_bytes()
        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        return key

    def _encrypt(self, value: str | None) -> bytes | None:
        if not value:
            return None
        return self.fernet.encrypt(value.encode("utf-8"))
