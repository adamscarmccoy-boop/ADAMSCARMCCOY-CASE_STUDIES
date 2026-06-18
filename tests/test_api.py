import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.api import app

client = TestClient(app)

def test_execute_pipeline_endpoint_500_error():
    """Verify that a 500 error is returned when an exception occurs in the pipeline."""
    with patch("app.api.extract_and_index_session") as mock_extract:
        mock_extract.side_effect = Exception("Mocked failure")

        response = client.post(
            "/v1/agent/inference",
            json={"session_file_path": "fake.als", "prompt_query": "test"}
        )

        assert response.status_code == 500
        assert response.json() == {"detail": "Mocked failure"}
