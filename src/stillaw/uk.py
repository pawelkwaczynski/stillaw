"""United Kingdom: the same three states, read from legislation.gov.uk data.

Comparative, not a product feature yet. In Poland the entry-into-force date has to be parsed
out of the final article of the amending act. The UK publishes the same information AS DATA:
every act has a version date (RestrictStartDate) and a list of changes enacted but not yet
applied to the text (UnappliedEffects), which is the literal counterpart of vacatio legis.

Each unapplied effect carries <ukm:InForce Applied=".." Prospective=".." Date=".."/>. The
date can be EMPTY, and that is not missing data but a distinct legal state: the change is
enacted and its commencement day has not been appointed. Poland has no such state, because
a vacatio legis always has a date; in the UK commencement is often left to a minister.
"""
import re
import time

from . import eli

DATA_URL = "https://www.legislation.gov.uk/{}/data.xml"
_EFFECT = re.compile(r"<ukm:UnappliedEffect\b.*?</ukm:UnappliedEffect>|<ukm:UnappliedEffect\b[^>]*/>", re.S)


def check(act_id: str, as_of: str | None = None) -> dict:
    """`act_id` as legislation.gov.uk writes it, e.g. "ukpga/2018/12"."""
    as_of = as_of or time.strftime("%Y-%m-%d")
    xml = eli.fetch_bytes(DATA_URL.format(act_id), timeout=40, accept="application/xml").decode("utf-8", "replace")
    version = re.search(r'RestrictStartDate="(\d{4}-\d{2}-\d{2})"', xml)
    title = re.search(r"<dc:title>(.*?)</dc:title>", xml, re.S)
    dated, undated = [], 0
    for block in _EFFECT.findall(xml):
        if 'Applied="true"' in block:
            continue
        # The date sits in different attributes of the same element; requiring EffectiveDate
        # gave zero pending changes for the Companies Act 2006, which has a page of them.
        date = re.search(r'<ukm:InForce[^>]*?Date="(\d{4}-\d{2}-\d{2})"', block)
        if date:
            dated.append(date.group(1))
        else:
            undated += 1
    ahead = sorted(d for d in dated if d > as_of)
    in_force = sorted(d for d in dated if d <= as_of)
    if in_force:
        status = "superseded"
    elif ahead:
        status = "vacatio_legis"
    elif undated:
        status = "undetermined"
    else:
        status = "current"
    return {"act": act_id, "title": (title.group(1).strip()[:120] if title else ""),
            "version_of": version.group(1) if version else None, "as_of": as_of,
            "status": status, "since": in_force[0] if in_force else None,
            "next_change": ahead[0] if ahead else None,
            "unapplied_effects": len(dated) + undated, "without_date": undated,
            "links": {"data": DATA_URL.format(act_id)}}
