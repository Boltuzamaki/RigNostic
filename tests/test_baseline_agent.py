"""Regression tests for evidence guards around model-generated findings."""

from rignostic.baseline.agent import _remove_unsupported_driver_conflicts


def finding(defect_type: str) -> dict[str, object]:
    return {
        "defect_type": defect_type,
        "affected_control": "jawOpen",
        "description": "claim",
        "likely_root_cause": "claim",
        "confidence": 0.95,
    }


def test_separate_shape_key_paths_are_not_driver_conflicts() -> None:
    result = {"detected_defects": [finding("Conflicting Drivers"), finding("Bad Range")]}
    observations = {
        "drivers": [
            {"owner": "Lips", "data_path": 'key_blocks["jawOpen"].value'},
            {"owner": "Lips", "data_path": 'key_blocks["mouthSmile_L"].value'},
        ]
    }

    filtered = _remove_unsupported_driver_conflicts(result, observations)

    assert [item["defect_type"] for item in filtered["detected_defects"]] == ["Bad Range"]


def test_exact_duplicate_driver_path_preserves_conflict_finding() -> None:
    result = {"detected_defects": [finding("Driver Conflict")]}
    driver = {"owner": "Lips", "data_path": 'key_blocks["jawOpen"].value'}

    filtered = _remove_unsupported_driver_conflicts(result, {"drivers": [driver, driver]})

    assert filtered["detected_defects"] == result["detected_defects"]
