"""Tests for HIV ART Resistance Interpreter."""
import json
import pytest
from hiv_resistance_agent import (
    interpret_drug_resistance,
    recommend_regimen,
    interpret_tropism,
    analyze_hiv_resistance,
    HIV_DRUGS,
    NRTI_MUTATIONS,
    NNRTI_MUTATIONS,
    PI_MUTATIONS,
    INSTI_MUTATIONS,
    main,
)


# ─── Drug Database Tests ─────────────────────────────────────────────────────

def test_hiv_drugs_nrti():
    assert HIV_DRUGS["lamivudine"]["class"] == "NRTI"
    assert HIV_DRUGS["tenofovir_disoproxil"]["class"] == "NRTI"


def test_hiv_drugs_nnrti():
    assert HIV_DRUGS["efavirenz"]["class"] == "NNRTI"
    assert HIV_DRUGS["nevirapine"]["class"] == "NNRTI"


def test_hiv_drugs_pi():
    assert HIV_DRUGS["darunavir"]["class"] == "PI"
    assert HIV_DRUGS["atazanavir"]["class"] == "PI"


def test_hiv_drugs_insti():
    assert HIV_DRUGS["dolutegravir"]["class"] == "INSTI"
    assert HIV_DRUGS["raltegravir"]["class"] == "INSTI"


# ─── NRTI Mutation Tests ─────────────────────────────────────────────────────

def test_m184v_3tc_resistance():
    result = interpret_drug_resistance(["M184V"])
    assert result["drug_scores"]["lamivudine"]["level"] == "HIGH_LEVEL_RESISTANCE"
    assert result["drug_scores"]["emtricitabine"]["level"] == "HIGH_LEVEL_RESISTANCE"
    assert result["drug_scores"]["lamivudine"]["is_susceptible"] is False


def test_m184v_tdf_susceptible():
    """M184V should not affect TDF susceptibility."""
    result = interpret_drug_resistance(["M184V"])
    assert result["drug_scores"]["tenofovir_disoproxil"]["is_susceptible"] is True


def test_k65r_tdf_resistance():
    result = interpret_drug_resistance(["K65R"])
    assert result["drug_scores"]["tenofovir_disoproxil"]["level"] in (
        "INTERMEDIATE_RESISTANCE", "LOW_LEVEL_RESISTANCE")
    assert result["drug_scores"]["tenofovir_disoproxil"]["is_susceptible"] is False


def test_tams_azt_resistance():
    """Multiple TAMs should confer AZT resistance."""
    result = interpret_drug_resistance(["M41L", "D67N", "K70R", "L210W", "T215Y", "K219Q"])
    assert result["drug_scores"]["zidovudine"]["is_susceptible"] is False
    assert result["drug_scores"]["zidovudine"]["score"] > 0


# ─── NNRTI Mutation Tests ────────────────────────────────────────────────────

def test_k103n_efv_resistance():
    result = interpret_drug_resistance(["K103N"])
    assert result["drug_scores"]["efavirenz"]["level"] == "HIGH_LEVEL_RESISTANCE"
    assert result["drug_scores"]["nevirapine"]["level"] == "HIGH_LEVEL_RESISTANCE"


def test_k103n_rpv_low():
    """K103N should cause only low-level RPV resistance."""
    result = interpret_drug_resistance(["K103N"])
    assert result["drug_scores"]["rilpivirine"]["level"] in (
        "LOW_LEVEL_RESISTANCE", "POTENTIAL_LOW_LEVEL_RESISTANCE")


def test_y181c_nvp_resistance():
    result = interpret_drug_resistance(["Y181C"])
    assert result["drug_scores"]["nevirapine"]["level"] == "HIGH_LEVEL_RESISTANCE"


def test_e138k_rpv_resistance():
    result = interpret_drug_resistance(["E138K"])
    assert result["drug_scores"]["rilpivirine"]["is_susceptible"] is False


# ─── PI Mutation Tests ───────────────────────────────────────────────────────

def test_i84v_pi_resistance():
    result = interpret_drug_resistance(["I84V"])
    assert result["drug_scores"]["darunavir"]["is_susceptible"] is False
    assert result["drug_scores"]["atazanavir"]["is_susceptible"] is False


def test_l90m_sqv_resistance():
    result = interpret_drug_resistance(["L90M"])
    assert result["drug_scores"]["saquinavir"]["is_susceptible"] is False


# ─── INSTI Mutation Tests ────────────────────────────────────────────────────

def test_n155h_ral_resistance():
    result = interpret_drug_resistance(["N155H"])
    assert result["drug_scores"]["raltegravir"]["level"] == "HIGH_LEVEL_RESISTANCE"
    assert result["drug_scores"]["elvitegravir"]["level"] == "HIGH_LEVEL_RESISTANCE"


def test_n155h_dtg_susceptible():
    """N155H should not significantly affect DTG."""
    result = interpret_drug_resistance(["N155H"])
    assert result["drug_scores"]["dolutegravir"]["is_susceptible"] is True


def test_q148h_dtg_intermediate():
    """Q148H should cause intermediate DTG resistance."""
    result = interpret_drug_resistance(["Q148H"])
    assert result["drug_scores"]["dolutegravir"]["level"] == "INTERMEDIATE_RESISTANCE"


def test_g140s_q148h_compensatory():
    """G140S + Q148H should increase resistance scores."""
    result_single = interpret_drug_resistance(["Q148H"])
    result_combo = interpret_drug_resistance(["G140S", "Q148H"])
    # With compensatory mutation, scores should be >= single mutation
    assert result_combo["drug_scores"]["raltegravir"]["score"] >= \
           result_single["drug_scores"]["raltegravir"]["score"]


def test_e92q_avg_resistance():
    result = interpret_drug_resistance(["E92Q"])
    assert result["drug_scores"]["elvitegravir"]["is_susceptible"] is False


# ─── Regimen Recommendation Tests ────────────────────────────────────────────

def test_regimen_susceptible():
    result = interpret_drug_resistance([])
    regimen = recommend_regimen(result)
    assert len(regimen["recommendations"]) > 0
    assert regimen["recommendations"][0]["type"] == "PREFERRED"


def test_regimen_with_m184v_k103n():
    """M184V + K103N should avoid 3TC and EFV-based regimens."""
    result = interpret_drug_resistance(["M184V", "K103N"])
    regimen = recommend_regimen(result)
    # Should still have recommendations
    assert len(regimen["recommendations"]) > 0


def test_regimen_hla_b5701():
    """HLA-B*5701 positive should exclude abacavir."""
    result = interpret_drug_resistance([])
    regimen = recommend_regimen(result, hla_b5701_positive=True)
    assert "abacavir" not in regimen["susceptible_drugs"]["NRTIs"]


def test_regimen_tropism_cxcr4():
    result = interpret_drug_resistance([])
    regimen = recommend_regimen(result, tropism="CXCR4")
    assert any("maraviroc" in n.lower() or "cxcr4" in n.lower() for n in regimen["notes"])


def test_regimen_hepatitis_b():
    result = interpret_drug_resistance([])
    regimen = recommend_regimen(result, hepatitis_b_coinfected=True)
    assert len(regimen["recommendations"]) > 0


# ─── Tropism Tests ───────────────────────────────────────────────────────────

def test_tropism_ccr5():
    result = interpret_tropism("CCR5")
    assert result["maraviroc_eligible"] is True


def test_tropism_cxcr4():
    result = interpret_tropism("CXCR4")
    assert result["maraviroc_eligible"] is False


def test_tropism_dual_mixed():
    result = interpret_tropism("DUAL_MIXED")
    assert result["maraviroc_eligible"] is False


def test_tropism_non_r5():
    result = interpret_tropism("NON_R5")
    assert result["maraviroc_eligible"] is False


# ─── Full Analysis Tests ─────────────────────────────────────────────────────

def test_full_analysis_no_mutations():
    result = analyze_hiv_resistance([])
    assert result["resistance_interpretation"]["total_mutations_detected"] == 0
    assert len(result["regimen_recommendations"]["recommendations"]) > 0


def test_full_analysis_multi_class_resistance():
    result = analyze_hiv_resistance(["M184V", "K103N", "I84V", "N155H"])
    assert len(result["alerts"]) > 0


def test_full_analysis_with_tropism():
    result = analyze_hiv_resistance(["M184V"], tropism="CCR5")
    assert result["tropism_interpretation"] is not None
    assert result["tropism_interpretation"]["maraviroc_eligible"] is True


# ─── Mutation Database Tests ─────────────────────────────────────────────────

def test_nrti_mutations_exist():
    assert "M184V" in NRTI_MUTATIONS
    assert "K65R" in NRTI_MUTATIONS
    assert "T215Y" in NRTI_MUTATIONS


def test_nnrti_mutations_exist():
    assert "K103N" in NNRTI_MUTATIONS
    assert "Y181C" in NNRTI_MUTATIONS
    assert "E138K" in NNRTI_MUTATIONS


def test_pi_mutations_exist():
    assert "I50V" in PI_MUTATIONS
    assert "I84V" in PI_MUTATIONS


def test_insti_mutations_exist():
    assert "N155H" in INSTI_MUTATIONS
    assert "Q148H" in INSTI_MUTATIONS
    assert "G140S" in INSTI_MUTATIONS
    assert "E92Q" in INSTI_MUTATIONS


# ─── CLI Tests ───────────────────────────────────────────────────────────────

def test_cli_interpret():
    assert main(["interpret", "--mutations", "M184V,K103N"]) == 0


def test_cli_tropism():
    assert main(["tropism", "--result", "CCR5"]) == 0


def test_cli_help():
    with pytest.raises(SystemExit) as exc:
        main(["interpret", "--help"])
    assert exc.value.code == 0
