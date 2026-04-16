"""HTTP API tests used by the Next.js frontend."""

from fastapi.testclient import TestClient

from rappi_intelligence.api import app


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
