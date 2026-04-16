"""Tests for encrypted provider credential storage."""

from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from rappi_intelligence.credentials import CredentialStore


def test_credentials_are_encrypted_at_rest() -> None:
    workspace_tmp = Path(".test_artifacts") / uuid4().hex
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    try:
        store = CredentialStore(
            db_path=workspace_tmp / "credentials.sqlite",
            key_path=workspace_tmp / "fernet.key",
        )

        store.save_provider("openai", "gpt-4o-mini", "secret-value")

        encrypted_key = store.get_encrypted_key("openai")

        assert encrypted_key is not None
        assert b"secret-value" not in encrypted_key
        assert store.get_api_key("openai") == "secret-value"
        assert store.get_model("openai") == "gpt-4o-mini"
    finally:
        rmtree(workspace_tmp, ignore_errors=True)
