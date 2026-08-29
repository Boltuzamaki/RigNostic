import json

import pytest

from rignostic.evaluation.evaluator import defect_matches, evaluate, load_gold, normalize
from rignostic.evaluation.schemas import AgentResult, Defect


def defect(**overrides) -> Defect:
    values = {
        "defect_type": "muted_driver",
        "affected_control": "eyeBlink_L",
        "root_cause": "driver_muted",
    }
    values.update(overrides)
    return Defect(**values)


def test_schema_round_trip() -> None:
    original = AgentResult(case_id="case_01", detected_defects=[defect()])
    restored = AgentResult.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored == original


def test_confidence_validation() -> None:
    with pytest.raises(ValueError):
        defect(confidence=1.1)


def test_transparent_normalization_and_matching() -> None:
    assert normalize("Muted Driver") == "muted_driver"
    assert defect_matches(defect(defect_type="muted driver"), defect())


def test_evaluation_does_not_double_match() -> None:
    result = AgentResult(case_id="case_01", detected_defects=[defect(), defect()])
    metrics = evaluate([result], {"case_01": [defect()]})
    assert metrics.correctly_detected == 1
    assert metrics.false_positives == 1
    assert metrics.defect_detection_recall == 1


def test_load_gold(tmp_path) -> None:
    path = tmp_path / "gold.json"
    path.write_text(json.dumps({"case_id": "case_01", "defects": [defect().__dict__]}))
    case_id, defects = load_gold(path)
    assert case_id == "case_01"
    assert defects == [defect()]
