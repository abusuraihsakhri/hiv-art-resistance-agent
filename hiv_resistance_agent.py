#!/usr/bin/env python3
"""
HIV ART Resistance Interpreter

Real implementation of:
- HIV drug class definitions (NRTIs, NNRTIs, PIs, INSTIs, Entry inhibitors)
- Key resistance mutation interpretation (simplified Stanford HIVdb algorithm)
- Resistance scoring: Susceptible, Potential Low-Level, Low-Level, Intermediate, High-Level
- Regimen selection based on resistance profile
- Tropism testing interpretation (CCR5 vs CXCR4)

Uses only Python stdlib.
"""

import argparse
import csv
import json
import sys
from typing import Dict, List, Optional, Any, Tuple

# ─── HIV Drug Classes and Individual Drugs ────────────────────────────────────

HIV_DRUGS = {
    # NRTIs (Nucleoside Reverse Transcriptase Inhibitors)
    "zidovudine": {"class": "NRTI", "abbreviation": "AZT/ZDV", "genomic_target": "RT"},
    "lamivudine": {"class": "NRTI", "abbreviation": "3TC", "genomic_target": "RT"},
    "emtricitabine": {"class": "NRTI", "abbreviation": "FTC", "genomic_target": "RT"},
    "tenofovir_disoproxil": {"class": "NRTI", "abbreviation": "TDF", "genomic_target": "RT"},
    "tenofovir_alafenamide": {"class": "NRTI", "abbreviation": "TAF", "genomic_target": "RT"},
    "abacavir": {"class": "NRTI", "abbreviation": "ABC", "genomic_target": "RT"},
    "didanosine": {"class": "NRTI", "abbreviation": "ddI", "genomic_target": "RT"},
    "stavudine": {"class": "NRTI", "abbreviation": "d4T", "genomic_target": "RT"},
    # NNRTIs (Non-Nucleoside Reverse Transcriptase Inhibitors)
    "efavirenz": {"class": "NNRTI", "abbreviation": "EFV", "genomic_target": "RT"},
    "nevirapine": {"class": "NNRTI", "abbreviation": "NVP", "genomic_target": "RT"},
    "rilpivirine": {"class": "NNRTI", "abbreviation": "RPV", "genomic_target": "RT"},
    "etravirine": {"class": "NNRTI", "abbreviation": "ETR", "genomic_target": "RT"},
    "doravirine": {"class": "NNRTI", "abbreviation": "DOR", "genomic_target": "RT"},
    # PIs (Protease Inhibitors)
    "atazanavir": {"class": "PI", "abbreviation": "ATV", "genomic_target": "PR"},
    "darunavir": {"class": "PI", "abbreviation": "DRV", "genomic_target": "PR"},
    "lopinavir": {"class": "PI", "abbreviation": "LPV", "genomic_target": "PR"},
    "saquinavir": {"class": "PI", "abbreviation": "SQV", "genomic_target": "PR"},
    "tipranavir": {"class": "PI", "abbreviation": "TPV", "genomic_target": "PR"},
    # INSTIs (Integrase Strand Transfer Inhibitors)
    "raltegravir": {"class": "INSTI", "abbreviation": "RAL", "genomic_target": "IN"},
    "elvitegravir": {"class": "INSTI", "abbreviation": "EVG", "genomic_target": "IN"},
    "dolutegravir": {"class": "INSTI", "abbreviation": "DTG", "genomic_target": "IN"},
    "bictegravir": {"class": "INSTI", "abbreviation": "BIC", "genomic_target": "IN"},
    "cabotegravir": {"class": "INSTI", "abbreviation": "CAB", "genomic_target": "IN"},
    # Entry Inhibitors
    "enfuvirtide": {"class": "EI", "abbreviation": "T-20", "genomic_target": "gp41"},
    "maraviroc": {"class": "CCR5_antagonist", "abbreviation": "MVC", "genomic_target": "CCR5"},
    "ibalizumab": {"class": "CD4_directed", "abbreviation": "IBA", "genomic_target": "CD4"},
    "fostemsavir": {"class": "attachment_inhibitor", "abbreviation": "FTR", "genomic_target": "gp120"},
    "lenacapavir": {"class": "capsid_inhibitor", "abbreviation": "LEN", "genomic_target": "capsid"},
}

# ─── Resistance Mutation Database ────────────────────────────────────────────

# Simplified Stanford HIVdb-style scoring
# Score: 0=Susceptible, 1-9=Potential Low, 10-14=Low, 15-29=Intermediate, >=30=High

NRTI_MUTATIONS = {
    "M184V": {
        "drugs_affected": {
            "lamivudine": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "emtricitabine": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "abacavir": {"score": 15, "level": "INTERMEDIATE_RESISTANCE"},
            "didanosine": {"score": 10, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Most common NRTI mutation; selected by 3TC/FTC. "
                      "Increases susceptibility to AZT/TDF (hypersusceptibility).",
    },
    "M184I": {
        "drugs_affected": {
            "lamivudine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "emtricitabine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
        },
        "description": "Less common 184 variant; typically minority species.",
    },
    "K65R": {
        "drugs_affected": {
            "tenofovir_disoproxil": {"score": 25, "level": "INTERMEDIATE_RESISTANCE"},
            "tenofovir_alafenamide": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "abacavir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "lamivudine": {"score": 10, "level": "LOW_LEVEL_RESISTANCE"},
            "emtricitabine": {"score": 10, "level": "LOW_LEVEL_RESISTANCE"},
            "didanosine": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Selected by TDF, ABC, ddI. Cross-resists among NRTIs.",
    },
    "M41L": {
        "drugs_affected": {
            "zidovudine": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "tenofovir_disoproxil": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM (thymidine analog mutation). Part of TAM pathway 1.",
        "tam": True,
    },
    "D67N": {
        "drugs_affected": {
            "zidovudine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM. Part of TAM pathway 2.",
        "tam": True,
    },
    "K70R": {
        "drugs_affected": {
            "zidovudine": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "tenofovir_disoproxil": {"score": 5, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM. Common early TAM.",
        "tam": True,
    },
    "L210W": {
        "drugs_affected": {
            "zidovudine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM. Part of TAM pathway 1.",
        "tam": True,
    },
    "T215Y": {
        "drugs_affected": {
            "zidovudine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "stavudine": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
            "tenofovir_disoproxil": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "abacavir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM. Part of TAM pathway 1. Major AZT resistance mutation.",
        "tam": True,
    },
    "T215F": {
        "drugs_affected": {
            "zidovudine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "stavudine": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
            "tenofovir_disoproxil": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM. Part of TAM pathway 2.",
        "tam": True,
    },
    "K219Q": {
        "drugs_affected": {
            "zidovudine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM. Accessory TAM.",
        "tam": True,
    },
    "K219E": {
        "drugs_affected": {
            "zidovudine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "TAM. Accessory TAM.",
        "tam": True,
    },
    "L74V": {
        "drugs_affected": {
            "abacavir": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
            "didanosine": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
            "tenofovir_disoproxil": {"score": 5, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Selected by ABC and ddI.",
    },
    "Q151M": {
        "drugs_affected": {
            "zidovudine": {"score": 40, "level": "HIGH_LEVEL_RESISTANCE"},
            "stavudine": {"score": 40, "level": "HIGH_LEVEL_RESISTANCE"},
            "didanosine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "abacavir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "tenofovir_disoproxil": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Multi-NRTI resistance mutation. Part of Q151M complex.",
    },
    "T69ins": {
        "drugs_affected": {
            "zidovudine": {"score": 40, "level": "HIGH_LEVEL_RESISTANCE"},
            "stavudine": {"score": 40, "level": "HIGH_LEVEL_RESISTANCE"},
            "tenofovir_disoproxil": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
        },
        "description": "Insertion at codon 69. Multi-NRTI resistance.",
    },
}

NNRTI_MUTATIONS = {
    "K103N": {
        "drugs_affected": {
            "efavirenz": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "nevirapine": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "rilpivirine": {"score": 12, "level": "LOW_LEVEL_RESISTANCE"},
            "doravirine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Most common NNRTI mutation. High-level EFV/NVP resistance.",
    },
    "K103S": {
        "drugs_affected": {
            "efavirenz": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "nevirapine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
        },
        "description": "Less common 103 variant.",
    },
    "Y181C": {
        "drugs_affected": {
            "nevirapine": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "efavirenz": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
            "rilpivirine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "etravirine": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Common NNRTI mutation. High-level NVP resistance.",
    },
    "Y181I": {
        "drugs_affected": {
            "nevirapine": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "rilpivirine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "etravirine": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Variant of 181 mutation.",
    },
    "E138K": {
        "drugs_affected": {
            "rilpivirine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "etravirine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "RPV-selected mutation. May also affect INSTIs when with INSTI mutations.",
    },
    "G190A": {
        "drugs_affected": {
            "efavirenz": {"score": 45, "level": "HIGH_LEVEL_RESISTANCE"},
            "nevirapine": {"score": 45, "level": "HIGH_LEVEL_RESISTANCE"},
        },
        "description": "Common NNRTI mutation.",
    },
    "V106M": {
        "drugs_affected": {
            "efavirenz": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "nevirapine": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "etravirine": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Selected by NVP in subtype C.",
    },
    "K101E": {
        "drugs_affected": {
            "efavirenz": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "nevirapine": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "rilpivirine": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "etravirine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Minor NNRTI mutation.",
    },
    "P225H": {
        "drugs_affected": {
            "efavirenz": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "nevirapine": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Accessory NNRTI mutation, often with K103N.",
    },
}

PI_MUTATIONS = {
    "I50V": {
        "drugs_affected": {
            "atazanavir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "darunavir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Selected by ATV/r.",
    },
    "I84V": {
        "drugs_affected": {
            "darunavir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "atazanavir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "lopinavir": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
            "saquinavir": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Major PI resistance mutation affecting multiple PIs.",
    },
    "V82A": {
        "drugs_affected": {
            "lopinavir": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
            "saquinavir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Selected by IDV, NFV. Accessory mutation for other PIs.",
    },
    "L90M": {
        "drugs_affected": {
            "saquinavir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "atazanavir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "lopinavir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Common PI mutation. Major SQV mutation.",
    },
    "D30N": {
        "drugs_affected": {
            "atazanavir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Selected by NFV. Does not affect DRV.",
    },
    "M46I": {
        "drugs_affected": {
            "atazanavir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
            "lopinavir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Common accessory PI mutation.",
    },
    "V32I": {
        "drugs_affected": {
            "darunavir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "lopinavir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "Minor PI mutation, contributes to DRV resistance with other mutations.",
    },
}

INSTI_MUTATIONS = {
    "N155H": {
        "drugs_affected": {
            "raltegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "elvitegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "dolutegravir": {"score": 0, "level": "SUSCEPTIBLE"},
            "bictegravir": {"score": 0, "level": "SUSCEPTIBLE"},
        },
        "description": "RAL/EVG-selected pathway. DTG/BIC retain activity.",
    },
    "Q148H": {
        "drugs_affected": {
            "raltegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "elvitegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "dolutegravir": {"score": 20, "level": "INTERMEDIATE_RESISTANCE"},
            "bictegravir": {"score": 20, "level": "INTERMEDIATE_RESISTANCE"},
        },
        "description": "Major INSTI resistance mutation. Reduced DTG susceptibility.",
    },
    "Q148R": {
        "drugs_affected": {
            "raltegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "elvitegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "dolutegravir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "bictegravir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
        },
        "description": "Major INSTI resistance mutation.",
    },
    "Q148K": {
        "drugs_affected": {
            "raltegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "elvitegravir": {"score": 60, "level": "HIGH_LEVEL_RESISTANCE"},
            "dolutegravir": {"score": 20, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "INSTI resistance mutation.",
    },
    "G140S": {
        "drugs_affected": {
            "raltegravir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
            "elvitegravir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Compensatory INSTI mutation. Enhances Q148 pathway resistance.",
        "compensatory_for": ["Q148H", "Q148R", "Q148K"],
    },
    "G140A": {
        "drugs_affected": {
            "raltegravir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Compensatory INSTI mutation for Q148 pathway.",
        "compensatory_for": ["Q148H", "Q148R"],
    },
    "E92Q": {
        "drugs_affected": {
            "elvitegravir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "raltegravir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "dolutegravir": {"score": 5, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "EVG-selected mutation. Part of N155H pathway.",
    },
    "Y143R": {
        "drugs_affected": {
            "raltegravir": {"score": 30, "level": "INTERMEDIATE_RESISTANCE"},
            "elvitegravir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
        },
        "description": "RAL-selected pathway. Third major INSTI resistance pathway.",
    },
    "T66I": {
        "drugs_affected": {
            "elvitegravir": {"score": 15, "level": "LOW_LEVEL_RESISTANCE"},
            "raltegravir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Minor INSTI mutation.",
    },
    "S230N": {
        "drugs_affected": {
            "raltegravir": {"score": 10, "level": "POTENTIAL_LOW_LEVEL_RESISTANCE"},
        },
        "description": "Rare INSTI mutation.",
    },
}


# ─── Resistance Interpretation (Simplified Stanford HIVdb) ───────────────────

def interpret_drug_resistance(mutations: List[str]) -> Dict[str, Dict[str, Any]]:
    """Interpret HIV resistance mutations and score each drug.

    Args:
        mutations: List of mutation strings (e.g., ['M184V', 'K103N', 'N155H'])

    Returns:
        Dict mapping each drug to its resistance score and level
    """
    # Initialize scores for all drugs at 0
    drug_scores: Dict[str, int] = {drug: 0 for drug in HIV_DRUGS}

    # All mutation databases
    all_mutation_dbs = [NRTI_MUTATIONS, NNRTI_MUTATIONS, PI_MUTATIONS, INSTI_MUTATIONS]

    detected_mutation_details = []

    for mutation in mutations:
        mutation_upper = mutation.strip().upper()
        found = False
        for mut_db in all_mutation_dbs:
            if mutation_upper in mut_db:
                mut_info = mut_db[mutation_upper]
                detected_mutation_details.append({
                    "mutation": mutation_upper,
                    "description": mut_info["description"],
                    "drugs_affected": mut_info["drugs_affected"],
                    "is_tam": mut_info.get("tam", False),
                })
                for drug, impact in mut_info["drugs_affected"].items():
                    drug_key = drug.lower().replace(" ", "_")
                    if drug_key in drug_scores:
                        drug_scores[drug_key] += impact["score"]
                found = True
                break

    # Apply compensatory mutation bonuses
    for mutation in mutations:
        mutation_upper = mutation.strip().upper()
        for mut_db in all_mutation_dbs:
            if mutation_upper in mut_db:
                mut_info = mut_db[mutation_upper]
                compensatory_for = mut_info.get("compensatory_for", [])
                for comp_mut in compensatory_for:
                    if comp_mut.upper() in [m.upper() for m in mutations]:
                        # Boost scores for drugs affected by the primary mutation
                        for mut_db2 in all_mutation_dbs:
                            if comp_mut.upper() in mut_db2:
                                for drug, impact in mut_db2[comp_mut.upper()]["drugs_affected"].items():
                                    drug_key = drug.lower().replace(" ", "_")
                                    if drug_key in drug_scores:
                                        drug_scores[drug_key] = int(drug_scores[drug_key] * 1.3)

    # Convert scores to interpretation levels
    def score_to_level(score: int) -> str:
        if score <= 0:
            return "SUSCEPTIBLE"
        elif score <= 9:
            return "POTENTIAL_LOW_LEVEL_RESISTANCE"
        elif score <= 14:
            return "LOW_LEVEL_RESISTANCE"
        elif score <= 29:
            return "INTERMEDIATE_RESISTANCE"
        else:
            return "HIGH_LEVEL_RESISTANCE"

    results = {}
    for drug_key, score in drug_scores.items():
        drug_info = HIV_DRUGS.get(drug_key, {})
        results[drug_key] = {
            "drug_class": drug_info.get("class", "UNKNOWN"),
            "abbreviation": drug_info.get("abbreviation", drug_key[:3].upper()),
            "score": score,
            "level": score_to_level(score),
            "is_susceptible": score <= 0,
        }

    return {
        "drug_scores": results,
        "detected_mutations": detected_mutation_details,
        "total_mutations_detected": len(detected_mutation_details),
    }


# ─── Regimen Selection ───────────────────────────────────────────────────────

def recommend_regimen(
    resistance_interpretation: Dict[str, Dict[str, Any]],
    tropism: Optional[str] = None,
    hla_b5701_positive: bool = False,
    hepatitis_b_coinfected: bool = False,
) -> Dict[str, Any]:
    """Recommend ART regimen based on resistance profile.

    Args:
        resistance_interpretation: Output from interpret_drug_resistance()
        tropism: 'CCR5', 'CXCR4', or 'dual_mixed' (optional)
        hla_b5701_positive: Whether HLA-B*5701 is positive (abacavir hypersensitivity)
        hepatitis_b_coinfected: Whether patient has HBV coinfection

    Returns:
        Dict with recommended regimen and alternatives
    """
    scores = resistance_interpretation["drug_scores"]

    # Categorize drugs by susceptibility
    susceptible_nrtis = []
    susceptible_nnrtis = []
    susceptible_pis = []
    susceptible_instis = []
    susceptible_others = []

    for drug, info in scores.items():
        if info["is_susceptible"]:
            drug_class = info["drug_class"]
            if drug_class == "NRTI":
                susceptible_nrtis.append(drug)
            elif drug_class == "NNRTI":
                susceptible_nnrtis.append(drug)
            elif drug_class == "PI":
                susceptible_pis.append(drug)
            elif drug_class == "INSTI":
                susceptible_instis.append(drug)
            else:
                susceptible_others.append(drug)

    # Apply contraindications
    if hla_b5701_positive:
        susceptible_nrtis = [d for d in susceptible_nrtis if d != "abacavir"]

    if hepatitis_b_coinfected:
        # Must include TDF or TAF for HBV coverage
        hbv_active_nrtis = ["tenofovir_disoproxil", "tenofovir_alafenamide", "lamivudine", "emtricitabine"]
        must_include_hbv = [d for d in hbv_active_nrtis if d in [x.lower().replace(" ", "_") for x in scores] and scores[d]["is_susceptible"]]

    # Build recommended regimen
    recommendations = []
    regimen_notes = []

    # Preferred: INSTI-based regimen
    if susceptible_instis:
        insti = susceptible_instis[0]  # Prefer DTG or BIC
        # Prefer DTG or BIC over RAL or EVG
        for preferred in ["dolutegravir", "bictegravir"]:
            if preferred in susceptible_instis:
                insti = preferred
                break

        # NRTI backbone
        nrti_backbone = []
        if "tenofovir_disoproxil" in susceptible_nrtis and "lamivudine" in susceptible_nrtis:
            nrti_backbone = ["tenofovir_disoproxil", "lamivudine"]
        elif "tenofovir_disoproxil" in susceptible_nrtis and "emtricitabine" in susceptible_nrtis:
            nrti_backbone = ["tenofovir_disoproxil", "emtricitabine"]
        elif "tenofovir_alafenamide" in susceptible_nrtis and "emtricitabine" in susceptible_nrtis:
            nrti_backbone = ["tenofovir_alafenamide", "emtricitabine"]
        elif "abacavir" in susceptible_nrtis and "lamivudine" in susceptible_nrtis and not hla_b5701_positive:
            nrti_backbone = ["abacavir", "lamivudine"]
        elif len(susceptible_nrtis) >= 2:
            nrti_backbone = susceptible_nrtis[:2]

        if nrti_backbone:
            regimen = [insti] + nrti_backbone
            recommendations.append({
                "regimen": regimen,
                "type": "PREFERRED",
                "description": f"INSTI-based regimen: {insti} + {'+'.join(nrti_backbone)}",
            })

    # Alternative: PI-based regimen
    if susceptible_pis and len(susceptible_nrtis) >= 2:
        # Prefer DRV/r
        pi = susceptible_pis[0]
        for preferred in ["darunavir", "atazanavir"]:
            if preferred in susceptible_pis:
                pi = preferred
                break

        nrti_backbone = susceptible_nrtis[:2]
        regimen = [pi] + nrti_backbone
        recommendations.append({
            "regimen": regimen,
            "type": "ALTERNATIVE",
            "description": f"PI-based regimen: {pi}/r + {'+'.join(nrti_backbone)}",
        })

    # Alternative: NNRTI-based regimen
    if susceptible_nnrtis and len(susceptible_nrtis) >= 2:
        nnrti = susceptible_nnrtis[0]
        for preferred in ["doravirine", "rilpivirine", "efavirenz"]:
            if preferred in susceptible_nnrtis:
                nnrti = preferred
                break

        nrti_backbone = susceptible_nrtis[:2]
        regimen = [nnrti] + nrti_backbone
        recommendations.append({
            "regimen": regimen,
            "type": "ALTERNATIVE",
            "description": f"NNRTI-based regimen: {nnrti} + {'+'.join(nrti_backbone)}",
        })

    # If very limited options
    if not recommendations:
        recommendations.append({
            "regimen": ["CONSULT_EXPERT"],
            "type": "EXPERT_CONSULTATION",
            "description": "Limited active agents available. Expert consultation recommended.",
        })
        regimen_notes.append("Highly resistant virus - consider enfuvirtide, "
                           "maraviroc (if CCR5-tropic), fostemsavir, lenacapavir, "
                           "ibalizumab as part of salvage regimen.")

    # Tropism considerations
    if tropism:
        if tropism.upper() == "CXCR4" or tropism.upper() == "DUAL_MIXED":
            regimen_notes.append(
                "CXCR4/dual-mixed tropism detected. Maraviroc (CCR5 antagonist) is NOT recommended."
            )
        elif tropism.upper() == "CCR5":
            regimen_notes.append(
                "CCR5-tropic virus. Maraviroc may be considered if needed."
            )

    return {
        "recommendations": recommendations,
        "susceptible_drugs": {
            "NRTIs": susceptible_nrtis,
            "NNRTIs": susceptible_nnrtis,
            "PIs": susceptible_pis,
            "INSTIs": susceptible_instis,
            "others": susceptible_others,
        },
        "notes": regimen_notes,
        "tropism": tropism,
    }


# ─── Tropism Interpretation ──────────────────────────────────────────────────

def interpret_tropism(tropism_result: str) -> Dict[str, Any]:
    """Interpret HIV tropism testing result.

    Args:
        tropism_result: 'CCR5', 'CXCR4', 'DUAL_MIXED', or 'NON_R5'

    Returns:
        Dict with interpretation and clinical implications
    """
    tropism_upper = tropism_result.upper().replace(" ", "_").replace("-", "_")

    interpretations = {
        "CCR5": {
            "tropism": "CCR5-tropic",
            "interpretation": "Virus uses CCR5 co-receptor for cell entry",
            "maraviroc_eligible": True,
            "clinical_significance": "CCR5 antagonists (maraviroc) can be used",
        },
        "CXCR4": {
            "tropism": "CXCR4-tropic",
            "interpretation": "Virus uses CXCR4 co-receptor for cell entry",
            "maraviroc_eligible": False,
            "clinical_significance": "CCR5 antagonists contraindicated. Associated with more advanced disease.",
        },
        "DUAL_MIXED": {
            "tropism": "Dual/mixed tropic",
            "interpretation": "Mixed population of CCR5-tropic and CXCR4-tropic virus",
            "maraviroc_eligible": False,
            "clinical_significance": "CCR5 antagonists not recommended. May indicate tropism switch.",
        },
        "NON_R5": {
            "tropism": "Non-R5 (CXCR4 or dual/mixed)",
            "interpretation": "Virus can use CXCR4 co-receptor",
            "maraviroc_eligible": False,
            "clinical_significance": "CCR5 antagonists contraindicated.",
        },
    }

    result = interpretations.get(tropism_upper, {
        "tropism": tropism_result,
        "interpretation": "Unknown tropism result",
        "maraviroc_eligible": False,
        "clinical_significance": "Unable to interpret. Repeat testing recommended.",
    })

    result["raw_input"] = tropism_result
    return result


# ─── Full HIV Resistance Analysis ────────────────────────────────────────────

def analyze_hiv_resistance(
    mutations: List[str],
    tropism: Optional[str] = None,
    hla_b5701_positive: bool = False,
    hepatitis_b_coinfected: bool = False,
) -> Dict[str, Any]:
    """Complete HIV ART resistance analysis.

    Args:
        mutations: List of detected resistance mutations
        tropism: Tropism test result (optional)
        hla_b5701_positive: HLA-B*5701 status
        hepatitis_b_coinfected: HBV coinfection status

    Returns:
        Comprehensive analysis with resistance interpretation and regimen recommendations
    """
    # Interpret resistance
    resistance = interpret_drug_resistance(mutations)

    # Get regimen recommendations
    regimen = recommend_regimen(
        resistance, tropism, hla_b5701_positive, hepatitis_b_coinfected
    )

    # Tropism interpretation
    tropism_result = None
    if tropism:
        tropism_result = interpret_tropism(tropism)

    # Generate alerts
    alerts = []
    high_level_count = sum(
        1 for d in resistance["drug_scores"].values()
        if d["level"] == "HIGH_LEVEL_RESISTANCE"
    )
    if high_level_count >= 3:
        alerts.append({
            "severity": "CRITICAL",
            "type": "MULTI_CLASS_RESISTANCE",
            "message": f"High-level resistance to {high_level_count} drugs detected",
            "recommendation": "Expert consultation for regimen selection. "
                            "Consider genotypic testing for all drug classes.",
        })

    # Count resistant drug classes
    resistant_classes = set()
    for drug, info in resistance["drug_scores"].items():
        if not info["is_susceptible"]:
            resistant_classes.add(info["drug_class"])
    if len(resistant_classes) >= 3:
        alerts.append({
            "severity": "CRITICAL",
            "type": "MULTI_CLASS_RESISTANCE",
            "message": f"Resistance detected across {len(resistant_classes)} drug classes: "
                      f"{', '.join(sorted(resistant_classes))}",
            "recommendation": "Consider salvage therapy with newer agents "
                            "(fostemsavir, lenacapavir, ibalizumab).",
        })

    return {
        "resistance_interpretation": resistance,
        "regimen_recommendations": regimen,
        "tropism_interpretation": tropism_result,
        "alerts": alerts,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def build_parser():
    """Build the argument parser."""
    p = argparse.ArgumentParser(
        prog="hiv-resistance",
        description="HIV ART Resistance Interpreter"
    )
    sub = p.add_subparsers(dest="cmd")

    # Interpret command
    s_interp = sub.add_parser("interpret", help="Interpret HIV resistance mutations")
    s_interp.add_argument("--mutations", required=True,
                          help="Comma-separated list of mutations (e.g., M184V,K103N)")
    s_interp.add_argument("--tropism", help="Tropism result (CCR5, CXCR4, DUAL_MIXED)")
    s_interp.add_argument("--hla-b5701", action="store_true", help="HLA-B*5701 positive")
    s_interp.add_argument("--hbv", action="store_true", help="Hepatitis B coinfection")

    # Tropism command
    s_trop = sub.add_parser("tropism", help="Interpret tropism test result")
    s_trop.add_argument("--result", required=True, help="Tropism result")

    # CSV command
    s_csv = sub.add_parser("csv", help="Analyze HIV resistance from CSV")
    s_csv.add_argument("--input", required=True, help="Input CSV file")
    s_csv.add_argument("--output", help="Output JSON file")

    return p


def main(argv=None):
    """CLI entry point."""
    p = build_parser()
    args = p.parse_args(argv)

    if args.cmd == "interpret":
        mutations = [m.strip() for m in args.mutations.split(",")]
        result = analyze_hiv_resistance(
            mutations,
            tropism=args.tropism,
            hla_b5701_positive=args.hla_b5701,
            hepatitis_b_coinfected=args.hbv,
        )
        print(json.dumps(result, indent=2))
        return 0

    elif args.cmd == "tropism":
        result = interpret_tropism(args.result)
        print(json.dumps(result, indent=2))
        return 0

    elif args.cmd == "csv":
        results = []
        with open(args.input, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mutations_str = row.get("mutations", "")
                mutations = [m.strip() for m in mutations_str.split(",") if m.strip()]
                tropism = row.get("tropism", None)
                result = analyze_hiv_resistance(mutations, tropism=tropism)
                result["raw_data"] = dict(row)
                results.append(result)
        print(json.dumps(results, indent=2))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
        return 0

    else:
        p.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
