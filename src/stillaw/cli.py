"""Command line: `stillaw check <reference> [--as-of DATE] [--json]`."""
import argparse
import datetime
import json
import sys

from . import __version__, pl


def _date(value: str) -> str:
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not an ISO date (YYYY-MM-DD)") from exc


def render(result: dict) -> str:
    lines = [f"{result['address']}  {result['statute']}"
             + (f"  (consolidated text published {result['text_published']})"
                if result["consolidated_text"] else f"  (published {result['text_published']})"),
             f"status as of {result['as_of']}: {result['status'].upper()}"
             + (f" since {result['since']}" if result["since"] else "")]
    if result["superseded_by"]:
        lines.append(f"superseded by: {result['superseded_by']['eli']}  {result['superseded_by']['title'][:90]}")
    if result["next_change"]:
        lines.append(f"next change: {result['next_change']}")
    amendments = result["amendments"]
    lines.append(f"amendments after the text: {len(amendments)}")
    for a in amendments:
        lines.append(f"  {a['eli']:14s} promulgated {a['promulgated']}  in force {a['in_force'] or 'UNKNOWN':10s}"
                     f"  {a['how']}")
        lines.append(f"      {a['title'][:100]}")
        if a["basis"]:
            lines.append(f"      basis: {a['basis'][:160]}")
        if a.get("disagreement"):
            lines.append(f"      ELI disagrees: {a['disagreement']}")
    if result["undetermined"]:
        lines.append(f"needs a human: {', '.join(result['undetermined'])}")
    for step in result["resolution"]:
        lines.append(f"resolution: {step}")
    lines.append(f"record: {result['links']['record']}")
    lines.append(f"sha256: {result['sha256']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stillaw", description="Is this still the law?")
    parser.add_argument("--version", action="version", version=f"stillaw {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="status of one Polish act")
    check.add_argument("reference", help='"Dz.U. 2024 poz. 1251", "DU/2024/1251" or a statute title')
    check.add_argument("--as-of", type=_date, default=None, help="date to evaluate at (default: today)")
    check.add_argument("--json", action="store_true", help="machine-readable output")
    survey = sub.add_parser("survey", help="status of many statutes (many ELI requests)")
    survey.add_argument("--statute", action="append", default=[], help="title; repeatable; default: built-in list")
    survey.add_argument("--as-of", type=_date, default=None)
    survey.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "check":
        try:
            result = pl.check(args.reference, args.as_of)
        except (LookupError, RuntimeError) as exc:
            print(f"stillaw: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=1) if args.json else render(result))
        return 0
    rows = pl.survey(args.statute or None, args.as_of)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    for r in rows:
        if r["status"] == "error":
            print(f"{r['statute'][:44]:46s} ERROR {r['error']}")
            continue
        print(f"{r['statute'][:44]:46s} {r['eli']:14s} text {r['text_published']}  {r['status']:13s} "
              f"in force {r['in_force']}, ahead {r['ahead']}, undetermined {r['undetermined']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
