"""Unified CLI entry point for the CRF pipeline."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from .pipeline import CRFPipeline
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)

def _resolve_output_dir(explicit: str = None) -> str:
    """Resolve output directory from explicit arg, env var, or error."""
    if explicit:
        return explicit
    env_dir = os.environ.get("CRF_OUTPUT_DIR")
    if env_dir:
        return env_dir
    print(
        "Error: No output directory specified.\n"
        "  Use -o/--output-dir <path>, or set CRF_OUTPUT_DIR environment variable.\n"
        "  Example: export CRF_OUTPUT_DIR=/path/to/output",
        file=sys.stderr,
    )
    sys.exit(1)


def _write_json_output(result, output_path):
    if output_path:
        Path(output_path).resolve().parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        logger.info("Saved to %s", output_path)
    else:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False, default=str)
        print()


def _default_config_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "config")


def handle_run(args):
    """Handle the 'run' subcommand — full extraction pipeline."""
    config_dir = args.config_dir or _default_config_dir()

    study_overrides = None
    if args.overrides:
        with open(args.overrides, encoding="utf-8") as f:
            study_overrides = json.load(f)

    pipeline = CRFPipeline(
        config_dir=config_dir,
        disease=args.disease,
        output_dir=_resolve_output_dir(args.output_dir),
        use_llm=args.use_llm,
        anthropic_api_key=args.api_key,
        study_overrides=study_overrides,
    )

    result = pipeline.run(
        input_dir=args.input_dir,
        skip_validation=args.skip_validation,
    )

    print(f"\nPipeline Result: {result.status}")
    print(f"  Documents processed: {result.records_processed}")
    print(f"  Records extracted:   {result.records_extracted}")
    print(f"  Mean confidence:     {result.mean_confidence:.2f}")
    print(f"  Low confidence:      {result.low_confidence_count}")
    print(f"  Elapsed time:        {result.elapsed_time:.1f}s")

    if result.outputs:
        print("\nOutputs:")
        for fmt, path in result.outputs.items():
            print(f"  {fmt}: {path}")

    if result.validation:
        print(f"\nValidation:")
        print(f"  Valid: {result.validation['valid']}/{result.validation['total']}")
        print(f"  Errors: {result.validation['errors']}")
        print(f"  Warnings: {result.validation['warnings']}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for err in result.errors[:10]:
            print(f"  - {err}")

    sys.exit(0 if result.status == "success" else 1)


def handle_parse_crf(args):
    """Handle the 'parse-crf' subcommand."""
    from .parsers.crf_parser import CRFParser

    parser = CRFParser(
        output_dir=args.output,
        excel_path=args.excel,
        fuzzy_threshold=args.fuzzy_threshold,
    )
    result = parser.parse(args.input_path)

    _write_json_output(result, args.output)


def handle_parse_protocol(args):
    """Handle the 'parse-protocol' subcommand."""
    from .parsers.protocol_parser import ProtocolParser

    parser = ProtocolParser()
    result = parser.parse(args.input_path)

    _write_json_output(result, args.output)


def handle_parse_data(args):
    """Handle the 'parse-data' subcommand."""
    from .parsers.data_parser import DataParser, PatientDataParser

    if args.patient_mode:
        parser = PatientDataParser()
    else:
        parser = DataParser()
    result = parser.parse(args.input_path)

    _write_json_output(result, args.output)


def handle_validate(args):
    """Handle the 'validate' subcommand."""
    import pandas as pd

    from .parsers.data_parser import DataParser
    from .validators.temporal_validator import TemporalValidator

    # Load data
    data_parser = DataParser()
    df = data_parser.get_dataframe(args.data_path)

    # Load optional specs
    protocol_spec = None
    if args.protocol:
        with open(args.protocol, encoding="utf-8") as f:
            protocol_spec = json.load(f)

    crf_spec = None
    if args.crf_spec:
        with open(args.crf_spec, encoding="utf-8") as f:
            crf_spec = json.load(f)

    custom_rules = None
    if args.rules:
        with open(args.rules, encoding="utf-8") as f:
            custom_rules = json.load(f)

    # Run temporal validation
    temporal_validator = TemporalValidator(protocol_spec=protocol_spec)
    issues = temporal_validator.validate(df)

    # Build result
    result = {
        "validation_date": str(pd.Timestamp.now()),
        "data_file": args.data_path,
        "total_records": len(df),
        "total_issues": len(issues),
        "errors": sum(1 for i in issues if i.severity.value == "error"),
        "warnings": sum(1 for i in issues if i.severity.value == "warning"),
        "issues": [
            {
                "record_id": i.record_id,
                "field": i.field,
                "severity": i.severity.value,
                "message": i.message,
                "rule_id": i.rule_id,
                "actual_value": str(i.actual_value) if i.actual_value else None,
                "expected_value": str(i.expected_value) if i.expected_value else None,
            }
            for i in issues
        ],
        "status": "PASSED" if not any(i.severity.value == "error" for i in issues) else "FAILED",
    }

    _write_json_output(result, args.output)


def handle_run_analysis(args):
    """Handle the 'run-analysis' subcommand — full transform + R analysis pipeline."""
    from .orchestrator import AnalysisOrchestrator

    config_dir = args.config_dir or _default_config_dir()

    # Resolve output directory (CSA_OUTPUT_DIR for R scripts)
    output_dir = args.output_dir or os.environ.get("CSA_OUTPUT_DIR")
    if not output_dir:
        print(
            "Error: No output directory specified.\n"
            "  Use -o/--output-dir <path>, or set CSA_OUTPUT_DIR environment variable.\n"
            "  Example: export CSA_OUTPUT_DIR=/path/to/output",
            file=sys.stderr,
        )
        sys.exit(2)

    # Parse optional script filter
    script_filter = None
    if args.scripts:
        script_filter = [s.strip() for s in args.scripts.split(",")]

    # Collect optional study metadata
    study_args = {
        k: v for k, v in {
            "study_name":  getattr(args, "study_name",  None),
            "protocol_id": getattr(args, "protocol_id", None),
            "trial_phase": getattr(args, "trial_phase", None),
            "sponsor":     getattr(args, "sponsor",     None),
            "data_cutoff": getattr(args, "data_cutoff", None),
        }.items() if v is not None
    }

    orchestrator = AnalysisOrchestrator(
        config_dir=config_dir,
        disease=args.disease,
        output_dir=output_dir,
        scripts_dir=args.scripts_dir,
        script_filter=script_filter,
        study_args=study_args or None,
    )

    result = orchestrator.run_full(
        data_path=args.data_file,
        skip_validation=args.skip_validation,
        journal=args.journal,
        generate_pdf=args.pdf,
        generate_html=args.html,
        generate_csr=not args.no_csr,
    )

    # Print summary
    print(f"\nAnalysis Result: {result.status}")
    print(f"  Disease:          {result.disease}")
    print(f"  Transformed CSV:  {result.transformed_csv}")
    print(f"  Scripts run:      {result.successful_scripts}/{result.total_scripts} succeeded")
    print(f"  Elapsed time:     {result.elapsed_time:.1f}s")

    # Step details
    for step_name, step_data in result.steps.items():
        status = step_data.get("status", "unknown")
        elapsed = step_data.get("elapsed_time", 0)
        print(f"\n  [{step_name}] {status} ({elapsed:.1f}s)")
        if step_name == "r_scripts":
            print(f"    Successful: {step_data.get('successful', 0)}")
            print(f"    Failed:     {step_data.get('failed', 0)}")

    if result.output_files:
        print(f"\nOutput files ({len(result.output_files)}):")
        for f in result.output_files:
            size = os.path.getsize(f) if os.path.exists(f) else 0
            print(f"  {f} ({size:,} bytes)")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for err in result.errors[:10]:
            print(f"  - {err}")

    # Exit code: 0=success, 1=partial, 2=pipeline failure
    if result.status == "success":
        sys.exit(0)
    elif result.status == "partial":
        sys.exit(1)
    else:
        sys.exit(2)


# ── Scientific skills CLI handlers ───────────────────────────────────────────

def handle_hypothesis(args):
    """Generate null/alternative/exploratory hypotheses for a disease and endpoint."""
    from .skills import CSASkillContext, HypothesisGenerator

    output_dir = Path(args.output_dir or os.environ.get("CSA_OUTPUT_DIR", "."))
    study_name = args.study_name or args.disease
    ctx = CSASkillContext.load(study_name, output_dir)
    ctx.disease = args.disease

    hyps = HypothesisGenerator(context=ctx).generate(
        disease=args.disease,
        treatment=args.treatment or "the study treatment",
        endpoint=args.endpoint or "",
        comparator=args.comparator or "standard of care",
    )
    ctx.save(output_dir)

    print(f"\nHypotheses for {args.disease.upper()} — {args.endpoint or 'primary endpoint'}:")
    for i, h in enumerate(hyps, 1):
        print(f"\n  {i}. {h}")


def handle_analyze_plan(args):
    """Generate statistical analysis plan and assumption warnings."""
    from .skills import CSASkillContext, StatisticalAnalyst, CriticalThinker

    output_dir = Path(args.output_dir or os.environ.get("CSA_OUTPUT_DIR", "."))
    study_name = args.study_name or args.disease
    ctx = CSASkillContext.load(study_name, output_dir)
    ctx.disease = args.disease

    n = args.n or 0
    if not n and getattr(args, "data", None):
        try:
            from .parsers.data_parser import DataParser
            df = DataParser().get_dataframe(args.data)
            n = len(df)
            print(f"  Auto-detected n={n} from {args.data}")
        except Exception:
            pass
    StatisticalAnalyst(context=ctx).analyze(
        disease=args.disease,
        primary_endpoint=args.endpoint or "",
        study_type=args.study_type or "retrospective",
        n=n,
    )
    CriticalThinker(context=ctx).check_assumptions(
        disease=args.disease,
        study_type=args.study_type or "retrospective",
        n=n,
    )
    ctx.save(output_dir)

    plan = ctx.statistical_plan
    print(f"\nStatistical Analysis Plan — {args.disease.upper()}")
    print(f"  Study type:    {plan.get('study_type')}")
    print(f"  Endpoint:      {plan.get('primary_endpoint')}")
    print(f"  Guideline:     {plan.get('reporting_guideline')}")
    print(f"\n  Methods:")
    for m in plan.get("methods", []):
        print(f"    - {m}")
    if ctx.assumption_warnings:
        print(f"\n  Assumption Warnings ({len(ctx.assumption_warnings)}):")
        for w in ctx.assumption_warnings:
            print(f"    ! {w[:120]}")


def handle_interpret_results(args):
    """Read R output files and extract key_statistics into sidecar JSON."""
    from .skills import CSASkillContext, ROutputInterpreter, ELNGuidelineMapper

    output_dir = Path(args.output_dir or os.environ.get("CSA_OUTPUT_DIR", "."))
    study_name = args.study_name or args.disease
    ctx = CSASkillContext.load(study_name, output_dir)
    ctx.disease = args.disease

    ROutputInterpreter(context=ctx).interpret(output_dir)
    ELNGuidelineMapper(context=ctx).map(output_dir)
    ctx.save(output_dir)

    print(f"\nExtracted key_statistics ({len(ctx.key_statistics)} keys):")
    for k, v in sorted(ctx.key_statistics.items()):
        val = v.get("value") if isinstance(v, dict) else v
        unit = v.get("unit", "") if isinstance(v, dict) else ""
        print(f"  {k}: {val} {unit or ''}".rstrip())

    if ctx.eln_annotations:
        print(f"\nELN/NIH Annotations ({len(ctx.eln_annotations)}):")
        for k, ann in sorted(ctx.eln_annotations.items()):
            print(f"  {k}: {ann[:80]}")


def handle_draft_methods(args):
    """Generate Methods section prose from the stored statistical plan."""
    from .skills import CSASkillContext, StatisticalAnalyst, ScientificWriter

    output_dir = Path(args.output_dir or os.environ.get("CSA_OUTPUT_DIR", "."))
    study_name = args.study_name or args.disease
    ctx = CSASkillContext.load(study_name, output_dir)
    ctx.disease = args.disease

    if not ctx.statistical_plan:
        StatisticalAnalyst(context=ctx).analyze(disease=args.disease)

    prose = ScientificWriter(context=ctx).draft_methods()
    ctx.save(output_dir)

    print(f"\nMethods Section ({len(prose)} chars):\n")
    print(prose)


def handle_review_assumptions(args):
    """Flag statistical assumption risks before running R scripts."""
    from .skills import CSASkillContext, CriticalThinker

    output_dir = Path(args.output_dir or os.environ.get("CSA_OUTPUT_DIR", "."))
    study_name = args.study_name or args.disease
    ctx = CSASkillContext.load(study_name, output_dir)
    ctx.disease = args.disease

    warnings = CriticalThinker(context=ctx).check_assumptions(
        disease=args.disease,
        study_type=args.study_type or "retrospective",
        n=args.n or 0,
    )
    ctx.save(output_dir)

    print(f"\nAssumption Review — {args.disease.upper()} ({len(warnings)} warnings):")
    for i, w in enumerate(warnings, 1):
        print(f"\n  {i}. {w}")


def main():
    parser = argparse.ArgumentParser(
        prog="crf_pipeline",
        description="CRF data extraction and validation pipeline for hematological clinical trials",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- run: Full extraction pipeline ---
    run_cmd = subparsers.add_parser("run", help="Run full extraction pipeline")
    run_cmd.add_argument("input_dir", help="Input directory with CRF documents")
    run_cmd.add_argument(
        "-d", "--disease",
        choices=["aml", "cml", "mds", "hct"],
        default="aml",
        help="Disease type (default: aml)",
    )
    run_cmd.add_argument("-o", "--output-dir", default=None)
    run_cmd.add_argument("-c", "--config-dir", default=None)
    run_cmd.add_argument("--use-llm", action="store_true")
    run_cmd.add_argument("--api-key", default=None)
    run_cmd.add_argument("--skip-validation", action="store_true")
    run_cmd.add_argument("--overrides", default=None, help="Path to JSON overrides")

    # --- parse-crf: Extract variable definitions from CRF document ---
    crf_cmd = subparsers.add_parser(
        "parse-crf",
        help="Extract variable definitions from CRF document",
    )
    crf_cmd.add_argument("input_path", help="CRF document (.docx or .pdf)")
    crf_cmd.add_argument("-o", "--output", help="Output JSON path")
    crf_cmd.add_argument("--excel", help="Optional Excel file for column mapping")
    crf_cmd.add_argument("--fuzzy-threshold", type=int, default=60)

    # --- parse-protocol: Parse clinical trial protocol ---
    proto_cmd = subparsers.add_parser(
        "parse-protocol",
        help="Parse clinical trial protocol document",
    )
    proto_cmd.add_argument("input_path", help="Protocol document (.docx or .pdf)")
    proto_cmd.add_argument("-o", "--output", help="Output JSON path")

    # --- parse-data: Parse patient data file ---
    data_cmd = subparsers.add_parser(
        "parse-data",
        help="Parse patient data file for structure analysis",
    )
    data_cmd.add_argument("input_path", help="Data file (.xlsx, .csv, .sav, .json)")
    data_cmd.add_argument("-o", "--output", help="Output JSON path")
    data_cmd.add_argument(
        "--patient-mode",
        action="store_true",
        help="Enable patient ID column detection",
    )

    # --- validate: Validate data against specs ---
    val_cmd = subparsers.add_parser(
        "validate",
        help="Validate patient data against protocol/CRF specs",
    )
    val_cmd.add_argument("data_path", help="Patient data file")
    val_cmd.add_argument("--protocol", help="Protocol spec JSON (from parse-protocol)")
    val_cmd.add_argument("--crf-spec", help="CRF spec JSON (from parse-crf)")
    val_cmd.add_argument("--rules", help="Custom validation rules JSON")
    val_cmd.add_argument("-o", "--output", help="Output report path")
    val_cmd.add_argument(
        "--format",
        choices=["json", "html", "md"],
        default="json",
        help="Output format (default: json)",
    )

    # --- run-analysis: Full transform + R analysis pipeline ---
    analysis_cmd = subparsers.add_parser(
        "run-analysis",
        help="Transform data and run R analysis scripts end-to-end",
    )
    analysis_cmd.add_argument("data_file", help="Patient data file (.csv, .xlsx, .sav)")
    analysis_cmd.add_argument(
        "-d", "--disease",
        choices=["aml", "cml", "mds", "hct"],
        default="aml",
        help="Disease type (default: aml)",
    )
    analysis_cmd.add_argument("-o", "--output-dir", default=None,
                              help="Output directory (or CSA_OUTPUT_DIR env var)")
    analysis_cmd.add_argument("-c", "--config-dir", default=None)
    analysis_cmd.add_argument("--scripts-dir", default=None,
                              help="Directory containing R scripts (default: scripts/)")
    analysis_cmd.add_argument("--skip-validation", action="store_true",
                              help="Skip data validation step")
    analysis_cmd.add_argument("--scripts", default=None,
                              help="Comma-separated list of R scripts to run (default: all for disease)")
    analysis_cmd.add_argument("--journal", default=None,
                              choices=["nejm", "lancet", "blood", "jco"],
                              help="Apply journal-specific table formatting")
    analysis_cmd.add_argument("--pdf", action="store_true",
                              help="Generate PDF versions of tables and figures")
    analysis_cmd.add_argument("--html", action="store_true",
                              help="Generate interactive HTML dashboard")
    analysis_cmd.add_argument("--no-csr", action="store_true",
                              help="Skip mini-CSR report generation")
    # Study-level metadata for hpw_manifest.json / StatisticalBridge
    analysis_cmd.add_argument("--study-name", default=None,
                              help="Study name (e.g. 'SAPPHIRE-G')")
    analysis_cmd.add_argument("--protocol-id", default=None,
                              help="Protocol identifier (e.g. 'SGPG-2024-001')")
    analysis_cmd.add_argument("--trial-phase", default=None,
                              choices=["Phase 1", "Phase 1b", "Phase 2", "Phase 3", "Phase 4"],
                              help="Trial phase")
    analysis_cmd.add_argument("--sponsor", default=None,
                              help="Sponsor name")
    analysis_cmd.add_argument("--data-cutoff", default=None,
                              help="Data cutoff date (YYYY-MM-DD)")

    # ── Scientific skills subcommands ─────────────────────────────────────────

    _disease_choices = ["aml", "cml", "mds", "hct"]
    _study_type_choices = ["retrospective", "rct", "phase1", "cohort"]

    # hypothesis
    hyp_cmd = subparsers.add_parser(
        "hypothesis",
        help="Generate null/alternative/exploratory hypotheses for a disease",
    )
    hyp_cmd.add_argument("-d", "--disease", choices=_disease_choices, required=True)
    hyp_cmd.add_argument("--endpoint", default="", help="Primary endpoint (e.g. 'OS', 'CR rate')")
    hyp_cmd.add_argument("--treatment", default="", help="Treatment name")
    hyp_cmd.add_argument("--comparator", default="", help="Comparator arm")
    hyp_cmd.add_argument("-o", "--output-dir", default=None)
    hyp_cmd.add_argument("--study-name", default=None)

    # analyze-plan
    plan_cmd = subparsers.add_parser(
        "analyze-plan",
        help="Generate statistical analysis plan and assumption warnings",
    )
    plan_cmd.add_argument("-d", "--disease", choices=_disease_choices, required=True)
    plan_cmd.add_argument("--study-type", choices=_study_type_choices, default="retrospective")
    plan_cmd.add_argument("--endpoint", default="", help="Primary endpoint")
    plan_cmd.add_argument("--n", type=int, default=0, help="Estimated sample size")
    plan_cmd.add_argument("--data", default=None, metavar="PATH",
                          help="Patient data file (.csv/.xlsx/.sav) for sample size auto-detection")
    plan_cmd.add_argument("-o", "--output-dir", default=None)
    plan_cmd.add_argument("--study-name", default=None)

    # interpret-results
    interp_cmd = subparsers.add_parser(
        "interpret-results",
        help="Read R output files and extract key_statistics into sidecar JSON",
    )
    interp_cmd.add_argument("-d", "--disease", choices=_disease_choices, required=True)
    interp_cmd.add_argument("-o", "--output-dir", default=None,
                            help="Output directory with R results (or CSA_OUTPUT_DIR)")
    interp_cmd.add_argument("--study-name", default=None)

    # draft-methods
    meth_cmd = subparsers.add_parser(
        "draft-methods",
        help="Generate Methods section prose from stored statistical plan",
    )
    meth_cmd.add_argument("-d", "--disease", choices=_disease_choices, required=True)
    meth_cmd.add_argument("-o", "--output-dir", default=None)
    meth_cmd.add_argument("--study-name", default=None)

    # review-assumptions
    rev_cmd = subparsers.add_parser(
        "review-assumptions",
        help="Flag statistical assumption risks before running R scripts",
    )
    rev_cmd.add_argument("-d", "--disease", choices=_disease_choices, required=True)
    rev_cmd.add_argument("--study-type", choices=_study_type_choices, default="retrospective")
    rev_cmd.add_argument("--n", type=int, default=0, help="Sample size")
    rev_cmd.add_argument("-o", "--output-dir", default=None)
    rev_cmd.add_argument("--study-name", default=None)

    args = parser.parse_args()

    setup_logging(args.log_level)

    handlers = {
        "run": handle_run,
        "parse-crf": handle_parse_crf,
        "parse-protocol": handle_parse_protocol,
        "parse-data": handle_parse_data,
        "validate": handle_validate,
        "run-analysis": handle_run_analysis,
        # Scientific skills
        "hypothesis":        handle_hypothesis,
        "analyze-plan":      handle_analyze_plan,
        "interpret-results": handle_interpret_results,
        "draft-methods":     handle_draft_methods,
        "review-assumptions":handle_review_assumptions,
    }

    handlers[args.command](args)


if __name__ == "__main__":
    main()
