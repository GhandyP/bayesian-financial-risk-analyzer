"""Tests for FastAPI backend endpoints."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock pymc before importing the main module
sys.modules["pymc"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()

# Add parent directory to path for imports
MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

from Analisis_Riesgo_PyMC import run_risk_analysis
from backend.main import app
from backend.models import RiskResponse

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root health check endpoint."""

    def test_root_returns_ok(self) -> None:
        """GET / should return status ok."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAnalyseEndpoint:
    """Tests for the /analyse risk analysis endpoint."""

    @patch("backend.main.run_risk_analysis")
    def test_analyse_with_valid_returns(self, mock_run) -> None:
        """POST /analyse with valid returns should return 200 and results."""
        mock_result = MagicMock()
        mock_result.var_value = 50000.0
        mock_result.threshold_probability = 0.05
        mock_result.investment_amount = 1000000.0
        mock_result.var_confidence = 0.95
        mock_result.loss_threshold = 50000.0
        mock_result.parameter_means = {"media_retorno": -0.001, "desviacion_retorno": 0.02, "nu": 8.0}
        mock_result.histogram_base64 = "base64encodedstring"
        mock_run.return_value = mock_result

        payload = {
            "returns": [-0.01, 0.005, -0.003, 0.006, -0.002, 0.01, -0.005, 0.003, -0.008, 0.004],
            "investment_amount": 1000000,
            "var_confidence": 0.95,
            "loss_threshold": 50000,
            "draws": 500,
            "tune": 200,
            "target_accept": 0.9,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "var_value" in data
        assert "threshold_probability" in data
        assert "investment_amount" in data
        assert "parameter_means" in data
        mock_run.assert_called_once()

    def test_analyse_with_insufficient_returns(self) -> None:
        """POST /analyse with fewer than 10 returns should return 400."""
        payload = {
            "returns": [-0.01, 0.005, -0.003],
            "investment_amount": 1000000,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_analyse_with_negative_investment(self) -> None:
        """POST /analyse with negative investment should return 422."""
        payload = {
            "returns": [-0.01] * 10,
            "investment_amount": -1000,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 422

    def test_analyse_with_invalid_var_confidence(self) -> None:
        """POST /analyse with var_confidence outside [0.8, 1.0) should return 422."""
        payload = {
            "returns": [-0.01] * 10,
            "var_confidence": 0.5,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 422

    @patch("backend.main.run_risk_analysis")
    def test_analyse_response_matches_contract(self, mock_run) -> None:
        """Response payload should validate against the RiskResponse model."""
        mock_result = MagicMock()
        mock_result.var_value = 50000.0
        mock_result.threshold_probability = 0.05
        mock_result.investment_amount = 1000000.0
        mock_result.var_confidence = 0.95
        mock_result.loss_threshold = 50000.0
        mock_result.parameter_means = {"media_retorno": -0.001, "desviacion_retorno": 0.02, "nu": 8.0}
        mock_result.histogram_base64 = "base64encodedstring"
        mock_run.return_value = mock_result

        payload = {
            "returns": [-0.01, 0.005, -0.003, 0.006, -0.002, 0.01, -0.005, 0.003, -0.008, 0.004],
            "investment_amount": 1000000,
            "var_confidence": 0.95,
            "loss_threshold": 50000,
            "draws": 500,
            "tune": 200,
            "target_accept": 0.9,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 200

        data = response.json()
        parsed = RiskResponse.model_validate(data)
        assert parsed.var_value == 50000.0
        assert parsed.threshold_probability == 0.05
        assert parsed.investment_amount == 1000000.0
        assert parsed.var_confidence == 0.95
        assert parsed.loss_threshold == 50000.0
        assert parsed.parameter_means.media_retorno == -0.001
        assert parsed.parameter_means.desviacion_retorno == 0.02
        assert parsed.histogram_base64 == "base64encodedstring"
        assert isinstance(parsed.var_value, float)
        assert isinstance(parsed.parameter_means.media_retorno, float)

    @pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
    def test_analyse_rejects_non_finite_returns(self, bad_value: float) -> None:
        """POST /analyse with NaN or infinite returns should return 422."""
        payload = {
            "returns": [-0.01] * 9 + [bad_value],
            "investment_amount": 1000000,
        }
        # Send the raw body: httpx refuses to serialize NaN/Infinity, but the JSON
        # wire format allows those literals and the server must reject them.
        body = json.dumps(payload)
        response = client.post(
            "/analyse",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_analyse_rejects_too_many_returns(self) -> None:
        """POST /analyse with more than MAX_RETURNS returns should return 422."""
        payload = {
            "returns": [-0.01] * 2001,
            "investment_amount": 1000000,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()

    @patch("backend.main.run_risk_analysis")
    def test_analyse_accepts_returns_at_upper_bound(self, mock_run) -> None:
        """POST /analyse with exactly MAX_RETURNS returns passes request validation."""
        mock_result = MagicMock()
        mock_result.var_value = 50000.0
        mock_result.threshold_probability = 0.05
        mock_result.investment_amount = 1000000.0
        mock_result.var_confidence = 0.95
        mock_result.loss_threshold = 50000.0
        mock_result.parameter_means = {"media_retorno": -0.001, "desviacion_retorno": 0.02, "nu": 8.0}
        mock_result.histogram_base64 = "base64encodedstring"
        mock_run.return_value = mock_result

        payload = {
            "returns": [-0.01] * 2000,
            "investment_amount": 1000000,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 200
        mock_run.assert_called_once()

    @patch("backend.main.run_risk_analysis")
    def test_analyse_maps_model_value_error_to_400(self, mock_run) -> None:
        """A ValueError raised by the model should surface as HTTP 400."""
        mock_run.side_effect = ValueError("Datos de entrada invalidos")
        payload = {
            "returns": [-0.01 for _ in range(10)],
            "investment_amount": 1000000,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Datos de entrada invalidos"

    @patch("backend.main.asyncio.wait_for")
    @patch("backend.main.run_risk_analysis")
    def test_analyse_times_out_to_504(self, mock_run, mock_wait_for) -> None:
        """Inference that exceeds the timeout should surface as HTTP 504."""
        mock_wait_for.side_effect = TimeoutError()
        payload = {
            "returns": [-0.01 for _ in range(10)],
            "investment_amount": 1000000,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 504
        assert response.json()["detail"] == "Inference timed out"


class TestModelDefensiveValidation:
    """Defensive checks inside Analisis_Riesgo_PyMC (before PyMC sampling)."""

    def test_model_rejects_non_finite_returns(self) -> None:
        """run_risk_analysis should raise ValueError on NaN/infinite returns."""
        with pytest.raises(ValueError, match="NaN o infinito"):
            run_risk_analysis([-0.01] * 9 + [float("nan")])

    def test_model_rejects_insufficient_returns(self) -> None:
        """run_risk_analysis should raise ValueError on fewer than 10 returns."""
        with pytest.raises(ValueError, match="al menos 10"):
            run_risk_analysis([-0.01] * 3)

    def test_model_rejects_too_many_returns(self) -> None:
        """run_risk_analysis should reject oversized historical series."""
        with pytest.raises(ValueError, match="maximo de retornos"):
            run_risk_analysis([-0.01] * 2001)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
