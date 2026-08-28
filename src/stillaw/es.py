"""Spain: the same question asked of the BOE, which answers with metadata instead of prose.

The BOE keeps a consolidated text as a sequence of <version ... fecha_vigencia="YYYYMMDD">
blocks, so the three-way split comes out of comparing dates, without a single language
heuristic. A version dated in the future is literally vacatio legis: published, not yet in
force. No such version does not mean "current for certain", only "current as of the last
consolidation", so that date is reported too.

The API wants Accept: application/xml; with application/json it answers 400.
"""
import re
import time

from . import eli

API_URL = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{}"


def _iso(d: str | None) -> str | None:
    return f"{d[0:4]}-{d[4:6]}-{d[6:8]}" if d else None


def check(act_id: str, as_of: str | None = None) -> dict:
    """`act_id` as the BOE writes it, e.g. "BOE-A-2015-10565"."""
    as_of = as_of or time.strftime("%Y-%m-%d")
    xml = eli.fetch_bytes(API_URL.format(act_id), timeout=40, accept="application/xml").decode("utf-8", "replace")
    title = re.search(r"<titulo>(.*?)</titulo>", xml, re.S)
    consolidated = re.search(r"<fecha_actualizacion>(\d{8})", xml)
    dates = sorted({d for d in re.findall(r'fecha_vigencia="(\d{8})"', xml)})
    compact = as_of.replace("-", "")
    ahead = [d for d in dates if d > compact]
    return {"act": act_id, "title": (title.group(1).strip()[:120] if title else ""),
            "version_of": _iso(dates[-1] if dates else None), "as_of": as_of,
            "status": "vacatio_legis" if ahead else "current",
            "note": None if ahead else "current as of the last BOE consolidation",
            "next_change": _iso(ahead[0]) if ahead else None, "versions": len(dates),
            "consolidated_on": _iso(consolidated.group(1) if consolidated else None),
            "links": {"data": API_URL.format(act_id)}}
