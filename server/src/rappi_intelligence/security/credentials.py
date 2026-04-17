"""Encrypted local credential storage for LLM providers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet

from rappi_intelligence.shared.config import FERNET_KEY_PATH, SECRETS_DB_PATH


@dataclass(frozen=True)
class ProviderCredential:
    """Stored configuration for an LLM provider."""

    provider: str
    model: str
    has_api_key: bool
    base_url: str | None = None


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
        base_url: str | None = None,
        preserve_existing_key: bool = True,
    ) -> None:
        """Create or update provider settings."""

        provider = provider.lower().strip()
        if api_key:
            encrypted_key = self._encrypt(api_key)
        elif preserve_existing_key:
            encrypted_key = self.get_encrypted_key(provider)
        else:
            encrypted_key = None
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO provider_credentials(
                    provider,
                    model,
                    encrypted_api_key,
                    base_url
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(provider)
                DO UPDATE SET
                    model = excluded.model,
                    encrypted_api_key = excluded.encrypted_api_key,
                    base_url = excluded.base_url,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (provider, model, encrypted_key, base_url),
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

    def get_base_url(self, provider: str) -> str | None:
        """Return configured base URL for the provider."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT base_url FROM provider_credentials WHERE provider = ?",
                (provider.lower().strip(),),
            ).fetchone()
        return str(row["base_url"]) if row and row["base_url"] else None

    def list_providers(self) -> list[ProviderCredential]:
        """List saved provider configurations without exposing secrets."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT provider, model, encrypted_api_key, base_url
                FROM provider_credentials
                ORDER BY provider
                """
            ).fetchall()
        return [
            ProviderCredential(
                provider=str(row["provider"]),
                model=str(row["model"]),
                has_api_key=bool(row["encrypted_api_key"]),
                base_url=str(row["base_url"]) if row["base_url"] else None,
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

    def clear_api_keys(self, provider: str | None = None) -> int:
        """Remove stored API keys while preserving provider settings."""

        with self._connect() as connection:
            if provider:
                cursor = connection.execute(
                    """
                    UPDATE provider_credentials
                    SET encrypted_api_key = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE provider = ?
                      AND encrypted_api_key IS NOT NULL
                    """,
                    (provider.lower().strip(),),
                )
            else:
                cursor = connection.execute(
                    """
                    UPDATE provider_credentials
                    SET encrypted_api_key = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE encrypted_api_key IS NOT NULL
                    """
                )
            return cursor.rowcount

    def _initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_credentials (
                    provider TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    encrypted_api_key BLOB,
                    base_url TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(provider_credentials)"
                ).fetchall()
            }
            if "base_url" not in columns:
                connection.execute(
                    "ALTER TABLE provider_credentials ADD COLUMN base_url TEXT"
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
