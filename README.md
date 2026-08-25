# HIV ART Resistance Interpreter

Clinical tool for interpreting HIV genotypic resistance mutations and recommending antiretroviral therapy (ART) regimens based on a simplified Stanford HIVdb algorithm.

## Features

- **Drug Class Coverage**: NRTIs, NNRTIs, PIs, INSTIs, Entry inhibitors
- **Key Resistance Mutation Interpretation**:
  - NRTI: M184V (3TC/FTC), K65R (TDF), TAMs (M41L, D67N, K70R, L210W, T215Y/F, K219Q/E)
  - NNRTI: K103N (efavirenz), Y181C (nevirapine), E138K (rilpivirine)
  - PI: I50V (atazanavir), I84V (darunavir), L90M (saquinavir)
  - INSTI: N155H, Q148H/R/K, G140S (raltegravir), E92Q (dolutegravir)
- **Stanford HIVdb-style Scoring**: Susceptible, Potential Low-Level, Low-Level, Intermediate, High-Level
- **Regimen Selection**: Based on resistance profile with contraindication awareness
- **Tropism Testing**: CCR5 vs CXCR4 interpretation with maraviroc eligibility
- **Compensatory Mutation Handling**: G140S + Q148H synergy

## Quick Start

```bash
# Interpret resistance mutations
python cli.py interpret --mutations M184V,K103N,N155H

# With tropism testing
python cli.py interpret --mutations M184V --tropism CCR5

# Interpret tropism result
python cli.py tropism --result CXCR4
```

## Python API

```python
from hiv_resistance_agent import analyze_hiv_resistance

result = analyze_hiv_resistance(
    mutations=["M184V", "K103N", "I84V"],
    tropism="CCR5",
    hla_b5701_positive=False,
)
print(result["regimen_recommendations"]["recommendations"][0]["description"])
```

## Testing

```bash
python -m pytest test_hiv_resistance_agent.py -v
```

## Standards

- Stanford HIVdb Algorithm (simplified)
- DHHS Guidelines for the Use of Antiretroviral Agents (2024)
- IAS-USA Drug Resistance Mutations (2023)

## License

MIT
