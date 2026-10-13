"""Regression coverage for input safety and documented local-model limits."""
import pytest

from hiv_resistance_agent import interpret_drug_resistance, recommend_regimen, analyze_hiv_resistance
from hiv_art_resistance_agent.cli import parse_csv_boolean, parse_finite_metric
from agents.base import AuditTrail


def test_duplicate_mutation_does_not_double_score():
    once = interpret_drug_resistance(["M184V"])
    twice = interpret_drug_resistance(["M184V", "m184v", " M184V "])
    assert twice["drug_scores"] == once["drug_scores"]
    assert twice["total_mutations_detected"] == 1


def test_unknown_mutation_is_not_silently_treated_as_susceptible():
    report = analyze_hiv_resistance(["ZZ999Q"])
    assert report["resistance_interpretation"]["unrecognized_mutations"] == ["ZZ999Q"]
    assert report["regimen_recommendations"]["recommendations"][0]["type"] == "EXPERT_CONSULTATION"


def test_entry_inhibitors_without_genotypic_rules_are_not_labeled_susceptible():
    score = interpret_drug_resistance([])["drug_scores"]["maraviroc"]
    assert score["level"] == "NOT_EVALUATED"
    assert score["is_susceptible"] is False


def test_hbv_regimen_candidates_include_tenofovir_and_3tc_or_ftc():
    report = interpret_drug_resistance([])
    recommendations = recommend_regimen(report, hepatitis_b_coinfected=True)["recommendations"]
    assert recommendations
    for item in recommendations:
        if item["type"] == "EXPERT_CONSULTATION":
            continue
        assert set(item["regimen"]) & {"tenofovir_disoproxil", "tenofovir_alafenamide"}
        assert set(item["regimen"]) & {"lamivudine", "emtricitabine"}


@pytest.mark.parametrize(("text", "expected"), [
    ("True", True), ("false", False), ("0", False), ("1", True),
    (" no ", False), ("yes", True), ("", False),
])
def test_csv_boolean_parsing(text, expected):
    assert parse_csv_boolean(text) is expected


def test_invalid_csv_boolean_rejected():
    with pytest.raises(ValueError):
        parse_csv_boolean("unexpected")


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nonfinite_csv_metrics_rejected(value):
    with pytest.raises(ValueError):
        parse_finite_metric(value)


def test_audit_trail_returns_defensive_copy():
    audit = AuditTrail(secret_key="regression-key")
    audit.log("system", "test", "RUN", {"status": "OK"})
    exported = audit.get_trail()
    exported[0]["payload_hash"] = "tampered"
    assert audit.verify_integrity() is True


def test_static_web_console_has_no_fabricated_audit_results():
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / "web" / "index.html").read_text()
    assert 'loadPyodide' in html
    assert 'DOSSIER-SIM-' not in html
    assert 'HMAC_SHA256_e83' not in html
    assert "/api/audit" not in html
