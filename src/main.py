#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from src.phase1_url_discovery import run_phase1
from src.phase2_context_analysis import run_phase2
from src.phase3_outreach_draft import run_phase3
from src.phase4_form_automation import run_phase4


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Run without network actions")
    ap.add_argument("--phase1-only", action="store_true", help="Run only Phase1 URL discovery")
    ap.add_argument("--phase2-only", action="store_true", help="Run only Phase2 context analysis")
    ap.add_argument("--phase3-only", action="store_true", help="Run only Phase3 outreach drafting")
    ap.add_argument("--phase4-only", action="store_true", help="Run only Phase4 form automation")
    ap.add_argument("--csv", default="data/company_names.csv")
    ap.add_argument("--out", default="data/out")
    ap.add_argument("--max-companies", type=int, default=50)
    ap.add_argument("--sleep-min", type=float, default=0.2)
    ap.add_argument("--sleep-max", type=float, default=0.6)
    ap.add_argument("--num", type=int, default=5, help="Results per query")
    args = ap.parse_args()

    phase_only_flags = [
        args.phase1_only,
        args.phase2_only,
        args.phase3_only,
        args.phase4_only,
    ]
    if sum(1 for flag in phase_only_flags if flag) > 1:
        raise SystemExit("Specify only one of --phase1-only/--phase2-only/--phase3-only/--phase4-only")

    if args.dry_run:
        if args.phase2_only:
            print("[dry-run] Phase2 context analysis -> 03-04 files")
            return
        if args.phase3_only:
            print("[dry-run] Phase3 outreach drafting -> 05 file")
            return
        if args.phase4_only:
            print("[dry-run] Phase4 form automation -> 06-08 files")
            return
        print("[dry-run] Phase1 URL discovery -> data/out/<company_slug>/01-02 files")
        if args.phase1_only:
            return
        print("[dry-run] Phase2 context analysis -> 03-04 files")
        print("[dry-run] Phase3 outreach drafting -> 05 file")
        print("[dry-run] Phase4 form automation -> 06-08 files")
        return

    if args.phase2_only:
        run_phase2(out_dir=args.out, max_companies=args.max_companies)
        return
    if args.phase3_only:
        run_phase3(out_dir=args.out, max_companies=args.max_companies)
        return
    if args.phase4_only:
        run_phase4(out_dir=args.out, max_companies=args.max_companies)
        return

    run_phase1(
        csv_path=args.csv,
        out_dir=args.out,
        max_companies=args.max_companies,
        sleep_min=args.sleep_min,
        sleep_max=args.sleep_max,
        num=args.num,
    )

    if not args.phase1_only:
        run_phase2(out_dir=args.out, max_companies=args.max_companies)
        run_phase3(out_dir=args.out, max_companies=args.max_companies)
        run_phase4(out_dir=args.out, max_companies=args.max_companies)


if __name__ == "__main__":
    main()
