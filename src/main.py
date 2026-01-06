#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from src.phase1_url_discovery import run_phase1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Run without network actions")
    ap.add_argument("--phase1-only", action="store_true", help="Run only Phase1 URL discovery")
    ap.add_argument("--csv", default="data/company_names.csv")
    ap.add_argument("--out", default="data/out")
    ap.add_argument("--max-companies", type=int, default=50)
    ap.add_argument("--sleep-min", type=float, default=0.2)
    ap.add_argument("--sleep-max", type=float, default=0.6)
    ap.add_argument("--num", type=int, default=5, help="Results per query")
    args = ap.parse_args()

    if args.dry_run:
        print("[dry-run] Phase1 URL discovery -> data/out/<company_slug>/01-02 files")
        print("[dry-run] Phase2 context analysis (not implemented)")
        print("[dry-run] Phase3 outreach drafting (not implemented)")
        print("[dry-run] Phase4 form automation (not implemented)")
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
        print("Phase2-4 are not implemented yet. Stopping after Phase1.")


if __name__ == "__main__":
    main()
