"""
Command-Line Interface for HIV-Resistance Sentinel: Genotypic Mutation Interpretation & ART Optimization Agent.
"""
import argparse
import csv
import json
import math
import sys
from .models import ClinicalCasePayload
from .agents import HIVResistanceCoordinator

coordinator = HIVResistanceCoordinator()


def parse_csv_boolean(value):
    """Interpret CSV booleans explicitly instead of treating nonempty strings as true."""
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"", "0", "false", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean: {value!r}; expected true/false, yes/no, or 1/0")


def parse_finite_metric(value):
    metric = float(value)
    if not math.isfinite(metric):
        raise ValueError("Metrics must be finite numbers")
    return metric


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hiv-art-resistance-agent", description="HIV-Resistance Sentinel: Genotypic Mutation Interpretation & ART Optimization Agent")
    subparsers = parser.add_subparsers(dest="command")

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single case clinical audit")
    p_audit.add_argument("--case-id", "--task-id", dest="case_id", default="CASE-2026-001",
                         help="Case/task identifier (default: CASE-2026-001)")
    p_audit.add_argument("--primary", type=float, default=26.2)
    p_audit.add_argument("--secondary", type=float, default=12.5)
    p_audit.add_argument("--stat", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="*", default=["status"])

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC-SHA256 audit trail integrity")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        case = ClinicalCasePayload(
            case_id=args.case_id,
            patient_synthetic_id="SYNTH-PT-881",
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_flag=args.status,
            is_stat=args.stat,
        )
        dossier = coordinator.process_case(case)
        print("=" * 80)
        print(f"  HIV-RESISTANCE SENTINEL: GENOTYPIC MUTATION INTERPRETATION & ART OPTIMIZATION AGENT")
        print("  Illustrative threshold test only; not a clinical guideline or HIVdb analysis.")
        print(f"  Case: {dossier['case_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['urgency']}] from {a['sub_agent']}:")
            print(f"  Title: {a['title']}")
            print(f"  Finding: {a['clinical_finding']}")
            print(f"  Action: {a['actionable_recommendation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        query = " ".join(args.query) if args.query else "status"
        ans = coordinator.query_supervisory_chat(query)
        print(f"\n[HIVResistanceCoordinator]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        # Import audit logger from agents package for HMAC-SHA256 verification
        try:
            from agents.base import AuditLogger
            verified = AuditLogger.verify_integrity()
            trail = AuditLogger.get_trail()
            print(f"Audit Trail Integrity: {'VERIFIED' if verified else 'COMPROMISED'}")
            print(f"Total Audit Blocks: {len(trail)}")
            return 0 if verified else 1
        except ImportError:
            print("Audit system not available. No audit trail to verify.")
            return 1

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = list(dict.fromkeys(fieldnames + ["overall_status", "total_alerts", "stat_critical_alerts", "consensus_summary"]))
        out_rows = []
        for r in rows:
            case = ClinicalCasePayload(
                case_id=r.get("case_id", "CASE-01"),
                patient_synthetic_id=r.get("patient_synthetic_id", "SYNTH-01"),
                primary_metric=parse_finite_metric(r.get("metric_primary") or r.get("primary_metric") or 15.0),
                secondary_metric=parse_finite_metric(r.get("metric_secondary") or r.get("secondary_metric") or 5.0),
                status_flag=r.get("status_flag", r.get("status_text", "NORMAL")),
                is_stat=parse_csv_boolean(r.get("is_stat") if r.get("is_stat") not in (None, "") else r.get("critical_flag", False)),
            )
            dossier = coordinator.process_case(case)
            row_dict = dict(r)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["stat_critical_alerts"] = dossier["stat_critical_alerts"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Batch processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app is None:
                print("FastAPI / pydantic not installed. Install the api extra.")
                return 1
            print(f"Starting demonstration metric API on http://{args.host}:{args.port}")
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    # No command specified - print help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
