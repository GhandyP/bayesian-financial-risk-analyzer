"""Contract tests for the hand-written Python <-> Dart seam.

The response schema and the request limits exist twice: once in Pydantic
(`backend/models.py` + `risk_limits.py`) and once in the Dart client
(`flutter_app/lib/...`). Nothing links them at compile time, so these tests link
them at test time, in both directions:

- the response example the Dart suite decodes is regenerated from
  `RiskResponse`, so renaming or retyping a field fails here;
- the Dart limit constants are parsed and compared against the Pydantic
  constraints, so changing a bound on one side only fails here.

Regenerate the committed response example after an intended schema change:

    python -m backend.test_contract
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

from backend.models import RiskRequest, RiskResponse
from risk_limits import MAX_RETURNS, MIN_RETURNS

CONTRACT_DIR = Path(__file__).resolve().parent / "contract"
RESPONSE_EXAMPLE = CONTRACT_DIR / "risk_response.example.json"
FLUTTER_LIMITS = MODEL_DIR / "flutter_app" / "lib" / "config" / "risk_limits.dart"

_DART_CONST = re.compile(r"static const (?:int|double) (\w+) = ([0-9]+(?:\.[0-9]+)?);")


def build_example_response() -> dict[str, object]:
    """Canonical response payload, shared with the Dart test suite."""
    return RiskResponse(
        var_value=50_000.0,
        threshold_probability=0.05,
        investment_amount=1_000_000.0,
        var_confidence=0.95,
        loss_threshold=50_000.0,
        parameter_means={"media_retorno": -0.001, "desviacion_retorno": 0.02, "nu": 8.0},
        histogram_base64="iVBORw0KGgo=",
    ).model_dump()


def _dart_constants(source: str) -> dict[str, float]:
    return {name: float(value) for name, value in _DART_CONST.findall(source)}


def test_response_example_matches_the_dart_contract() -> None:
    """A response field rename or type change must fail here, not at runtime."""
    committed = json.loads(RESPONSE_EXAMPLE.read_text(encoding="utf-8"))

    assert committed == build_example_response(), (
        "The committed response example is stale. If the schema change was "
        "intended, regenerate it with `python -m backend.test_contract` and "
        "update the Dart client and its fixtures to match."
    )


def test_flutter_limits_match_the_backend_constraints() -> None:
    """Every mirrored client bound must equal the constraint the backend declares."""
    dart = _dart_constants(FLUTTER_LIMITS.read_text(encoding="utf-8"))
    properties = RiskRequest.model_json_schema()["properties"]

    assert dart["returnsMinCount"] == MIN_RETURNS
    assert dart["returnsMaxCount"] == MAX_RETURNS

    assert dart["investmentMinExclusive"] == properties["investment_amount"]["exclusiveMinimum"]
    assert dart["varConfidenceMin"] == properties["var_confidence"]["minimum"]
    assert (
        dart["varConfidenceMaxExclusive"]
        == properties["var_confidence"]["exclusiveMaximum"]
    )
    assert dart["lossThresholdMin"] == properties["loss_threshold"]["minimum"]

    assert dart["drawsMin"] == properties["draws"]["minimum"]
    assert dart["drawsMax"] == properties["draws"]["maximum"]
    assert dart["tuneMin"] == properties["tune"]["minimum"]
    assert dart["tuneMax"] == properties["tune"]["maximum"]
    assert dart["targetAcceptMin"] == properties["target_accept"]["minimum"]
    assert dart["targetAcceptMax"] == properties["target_accept"]["maximum"]


if __name__ == "__main__":
    CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSE_EXAMPLE.write_text(
        json.dumps(build_example_response(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {RESPONSE_EXAMPLE}")
