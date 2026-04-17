"""HTTP API tests used by the Next.js frontend."""

from fastapi.testclient import TestClient

from rappi_intelligence.api import app
from rappi_intelligence.api.routes import providers
from rappi_intelligence.api.routes.chat import _stream_event


def test_dataset_overview_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/dataset/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["countries"] == 9
    assert payload["metrics"] == 14
    assert payload["zones"] > 1000


def test_providers_endpoint_returns_defaults() -> None:
    client = TestClient(app)

    response = client.get("/providers")

    assert response.status_code == 200
    payload = response.json()
    assert "ollama" in payload["supported"]
    assert "openai" in payload["defaultModels"]


def test_chat_endpoint_returns_reusable_history_id() -> None:
    client = TestClient(app)

    first_response = client.post(
        "/chat",
        json={
            "question": "Cuales son las 5 zonas con mayor Lead Penetration?",
            "provider": None,
            "model": None,
            "base_url": None,
            "require_llm": False,
        },
    )

    assert first_response.status_code == 200
    first_payload = first_response.json()
    history_id = first_payload["history_id"]
    assert history_id

    second_response = client.post(
        "/chat",
        json={
            "question": "Y cuales son las de menor performance?",
            "history_id": history_id,
            "provider": None,
            "model": None,
            "base_url": None,
            "require_llm": False,
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["history_id"] == history_id


def test_report_stream_events_are_not_wrapped_as_text_chunks() -> None:
    chart_chunk = '{"type": "chart", "chart": {"type": "pie", "data": {"data": []}}}\n\n'

    event = _stream_event(chart_chunk)

    assert event["type"] == "chart"
    assert "content" not in event


def test_markdown_stream_chunks_remain_text_chunks() -> None:
    event = _stream_event("# Generando análisis de datos...\n\n")

    assert event == {"type": "chunk", "content": "# Generando análisis de datos...\n\n"}


def test_clear_providers_endpoint_removes_api_keys(monkeypatch) -> None:
    class FakeCredentialStore:
        def clear_api_keys(self) -> int:
            return 2

    monkeypatch.setattr(providers, "CredentialStore", FakeCredentialStore)
    client = TestClient(app)

    response = client.post("/providers/clear")

    assert response.status_code == 200
    assert response.json() == {"status": "cleared", "cleared": 2}
