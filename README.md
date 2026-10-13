# HIV ART Resistance Agent

An educational Python implementation of a **limited HIV-1 resistance mutation rule table**, with a command-line interpreter, a browser-based demonstration, and separate synthetic metric-audit utilities.

> **Not for clinical use.** The local mutation and interaction tables are incomplete and have not been validated against a current Stanford HIVdb release. A drug with a zero penalty in this model **cannot** be presumed susceptible. Regimen combinations are illustrative rather than patient-specific recommendations. Use a validated resistance interpretation service and specialist review for clinical decisions.

## Browser interface

The [browser interface source](web/index.html) runs the repository's Python interpreter in-browser using **Pyodide**. On a repository configured for GitHub Pages, the Pages workflow publishes the static interface together with a copy of the Python rules file. The published address must be verified before being documented here.

Enter *synthetic, non-identifiable* mutation codes (for example, `M184V,K103N`), optionally set the tropism, HLA-B*5701 and HIV/HBV demonstration flags, and run the analysis. The UI displays recognized and unrecognized mutations, nonzero local drug scores, and illustrative candidate combinations. Results can be exported as JSON.

The browser downloads Pyodide from jsDelivr. Analysis values remain in the browser tab; the UI does not POST entered mutations to a server. The initial runtime download requires network access. The application is **not air-gapped**.

## Python usage

Requires Python 3.10–3.12 for the tested CI configuration (package metadata currently allows Python 3.9+). Install the local package:

```bash
python -m pip install .
```

Run the standalone rule-table interpreter (standard library only when invoked directly):

```bash
python hiv_resistance_agent.py interpret --mutations M184V,K103N,N155H --tropism CCR5
python hiv_resistance_agent.py tropism --result CXCR4
python hiv_resistance_agent.py csv --input your_example.csv --output results.json
```

The `interpret` command returns mutation details, local drug scores, unrecognized mutations, and demonstration regimen candidates. Input mutation tokens are normalized and deduplicated. Unsupported mutations trigger a specialist-review result instead of being silently ignored.

## Separate synthetic metric-audit tools

This is a **demonstration metric-audit subsystem**, **not** genotypic HIV resistance interpretation. It accepts generic numeric metrics and status flags. The threshold values are synthetic, not HIV treatment thresholds or medical guideline cutoffs.

```bash
python cli.py audit --case-id DEMO-001 --primary 26.2 --secondary 12.5 --status DISCORDANT
python cli.py batch --input sample.csv --output results.csv
python cli.py chat status
python cli.py verify-audit
```

To run the optional FastAPI implementation:

```bash
python -m pip install ".[api]"
python cli.py serve --host 127.0.0.1 --port 8000
```

The metric API supports `/health` and `/api/audit` with synthetic numeric payloads. The `agents.api` module contains an additional metric-audit example. Neither API provides the browser mutation interpreter or supports clinical patient care.

## Security and privacy

- Use **synthetic/non-identifiable data only**. The regex-based PHI filter is incomplete and is **not** a HIPAA de-identification or compliance guarantee.
- The HMAC-SHA256 chain is an **in-memory, session-scoped demonstration**. It is not a persistent clinical audit log. Set `AUDIT_SECRET_KEY` for a stable session configuration; never commit its value.
- The mock language-model adapter never calls an actual LLM provider and does not validate clinical decisions.
- Docker Compose requires `AUDIT_SECRET_KEY` supplied via environment and binds the published port to `127.0.0.1` by default. **There is no authentication.** Do not expose the API publicly or process real patient information.
- The browser interface has no server-side patient storage or analytics built into this repository.

## Development, tests, and deployment

```bash
python -m pip install ".[test]"
python -m pytest -q
python -m compileall -q hiv_resistance_agent.py hiv_art_resistance_agent agents
```

GitHub Actions runs the test suite on Python 3.10, 3.11, and 3.12. A separate Pages workflow packages `web/index.html` and `hiv_resistance_agent.py` for static deployment when GitHub Pages is enabled. A Python server cannot run directly on GitHub Pages; the browser application uses Pyodide instead.

Docker (local-only default with an externally supplied key):

```bash
export AUDIT_SECRET_KEY="replace-with-a-long-random-secret"
docker compose up --build
```

## Technology and compatibility

Python, standard-library mutation-rule engine, optional FastAPI/Pydantic server, Pyodide for browser execution, and static HTML/CSS/JavaScript. The browser UI is designed for current Chromium, Firefox, and Safari versions with WebAssembly enabled; runtime loading has not yet been verified across every browser.

For current, validated interpretation and treatment guidance, consult the [Stanford HIV Drug Resistance Database](https://hivdb.stanford.edu/) and [NIH HIV treatment guidelines](https://clinicalinfo.hiv.gov/en/guidelines).

## License

MIT — see [LICENSE](LICENSE).
