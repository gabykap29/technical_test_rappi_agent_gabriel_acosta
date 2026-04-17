"""Tests for encrypted provider credential storage."""

from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from rappi_intelligence.llm.providers import load_llm_config
from rappi_intelligence.security.credentials import CredentialStore


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


def test_credentials_store_base_url_and_can_clear_key() -> None:
    workspace_tmp = Path(".test_artifacts") / uuid4().hex
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    try:
        store = CredentialStore(
            db_path=workspace_tmp / "credentials.sqlite",
            key_path=workspace_tmp / "fernet.key",
        )

        store.save_provider(
            "ollama",
            "llama3.1",
            "cloud-token",
            base_url="https://ollama.com",
        )
        assert store.get_api_key("ollama") == "cloud-token"
        assert store.get_base_url("ollama") == "https://ollama.com"

        store.save_provider(
            "ollama",
            "llama3.1",
            base_url="http://localhost:11434",
            preserve_existing_key=False,
        )
        assert store.get_api_key("ollama") is None
        assert store.get_base_url("ollama") == "http://localhost:11434"
    finally:
        rmtree(workspace_tmp, ignore_errors=True)


def test_clear_api_keys_preserves_provider_settings() -> None:
    workspace_tmp = Path(".test_artifacts") / uuid4().hex
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    try:
        store = CredentialStore(
            db_path=workspace_tmp / "credentials.sqlite",
            key_path=workspace_tmp / "fernet.key",
        )
        store.save_provider(
            "openai",
            "gpt-4o-mini",
            "secret-value",
            base_url="https://api.openai.com",
        )

        cleared = store.clear_api_keys()

        assert cleared == 1
        assert store.get_api_key("openai") is None
        assert store.get_model("openai") == "gpt-4o-mini"
        assert store.get_base_url("openai") == "https://api.openai.com"
    finally:
        rmtree(workspace_tmp, ignore_errors=True)


def test_request_model_overrides_stored_provider_model() -> None:
    workspace_tmp = Path(".test_artifacts") / uuid4().hex
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    try:
        store = CredentialStore(
            db_path=workspace_tmp / "credentials.sqlite",
            key_path=workspace_tmp / "fernet.key",
        )
        store.save_provider("ollama", "llama3.1", base_url="http://localhost:11434")

        config = load_llm_config("ollama", model="mistral", store=store)

        assert config.model == "mistral"
    finally:
        rmtree(workspace_tmp, ignore_errors=True)
