"""Poland: is this consolidated text still the law?

The ELI record of a consolidated text lists the amendments promulgated after it, but not
when they enter into force for OUR statute. That date has to be read from the final article
of each amending act, exceptions included, which is what core.py does. This module does the
fetching around it and turns the dates into one answer.

Two dates for the same amendment are always reported: the one this parser reads for the
article that amends our statute, and the one ELI carries in `entryIntoForce` for the act as
a whole. They differ legitimately when the amending article is deferred by an exception
(art. 6 of Dz.U. 2026 poz. 644 enters into force in 2030, the act in 2026). A disagreement
without an exception in play means an error on our side, and is flagged as such.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import __version__, core, eli

# A cross-section of Polish statutes a business or technology lawyer actually opens. Wide
# enough that a survey over it says something about the state of consolidated texts in
# general. 89 titles.
DOMAIN = [
    "Prawo przedsiębiorców", "Kodeks spółek handlowych", "Kodeks postępowania cywilnego",
    "Kodeks cywilny", "Kodeks pracy", "Kodeks karny", "Kodeks postępowania karnego",
    "Kodeks postępowania administracyjnego", "Kodeks wykroczeń", "Kodeks rodzinny i opiekuńczy",
    "Ordynacja podatkowa", "o podatku od towarów i usług", "o podatku dochodowym od osób fizycznych",
    "o podatku dochodowym od osób prawnych", "o rachunkowości", "o systemie ubezpieczeń społecznych",
    "o świadczeniach opieki zdrowotnej finansowanych ze środków publicznych",
    "o ochronie danych osobowych", "o prawach konsumenta", "o zwalczaniu nieuczciwej konkurencji",
    "o prawie autorskim i prawach pokrewnych", "Prawo własności przemysłowej",
    "Prawo zamówień publicznych", "o krajowym systemie cyberbezpieczeństwa",
    "o świadczeniu usług drogą elektroniczną", "Prawo telekomunikacyjne",
    "o dostępności cyfrowej stron internetowych", "o ochronie konkurencji i konsumentów",
    "Prawo bankowe", "o kredycie konsumenckim", "o obrocie instrumentami finansowymi",
    "o przeciwdziałaniu praniu pieniędzy oraz finansowaniu terroryzmu",
    "o działalności leczniczej", "Prawo farmaceutyczne", "o wyrobach medycznych",
    "o zawodach lekarza i lekarza dentysty", "Prawo budowlane", "o planowaniu i zagospodarowaniu przestrzennym",
    "Prawo ochrony środowiska", "o odpadach", "Kodeks postępowania w sprawach o wykroczenia",
    "o Krajowym Rejestrze Sądowym", "o postępowaniu egzekucyjnym w administracji",
    "o finansach publicznych", "Prawo o szkolnictwie wyższym i nauce",
    "o transporcie drogowym", "Prawo o ruchu drogowym", "o ubezpieczeniach obowiązkowych",
    "Prawo energetyczne", "o odnawialnych źródłach energii", "o gospodarce nieruchomościami",
    "o własności lokali", "o ochronie praw lokatorów", "Prawo spółdzielcze",
    "o fundacjach", "Prawo o stowarzyszeniach", "o działalności pożytku publicznego i o wolontariacie",
    "o podatku akcyzowym", "o podatkach i opłatach lokalnych", "o podatku od czynności cywilnoprawnych",
    "o zryczałtowanym podatku dochodowym od niektórych przychodów osiąganych przez osoby fizyczne",
    "o Krajowej Administracji Skarbowej", "o rachunkowości budżetowej",
    "o emeryturach i rentach z Funduszu Ubezpieczeń Społecznych",
    "o świadczeniach pieniężnych z ubezpieczenia społecznego w razie choroby i macierzyństwa",
    "o promocji zatrudnienia i instytucjach rynku pracy", "o zatrudnianiu pracowników tymczasowych",
    "o związkach zawodowych", "o rozwiązywaniu sporów zbiorowych",
    "o Państwowej Inspekcji Pracy", "o ochronie roszczeń pracowniczych",
    "o dokumentach publicznych", "o informatyzacji działalności podmiotów realizujących zadania publiczne",
    "o doręczeniach elektronicznych", "o dostępie do informacji publicznej",
    "o ponownym wykorzystywaniu informacji sektora publicznego",
    "Prawo o aktach stanu cywilnego", "o ewidencji ludności",
    "o Sądzie Najwyższym", "Prawo o ustroju sądów powszechnych", "o kosztach sądowych w sprawach cywilnych",
    "o radcach prawnych", "Prawo o adwokaturze", "o notariacie", "o komornikach sądowych",
    "o biegłych rewidentach", "o obligacjach", "o funduszach inwestycyjnych",
    "o usługach płatniczych", "o kredycie hipotecznym",
]

CONSOLIDATED = "jednolitego tekstu"
# Keys the ELI record uses for cross-references. Polish, as the API returns them.
REF_AMENDMENTS_AFTER = "Nowelizacje po tekście jednolitym"
REF_AMENDING_ACTS = "Akty zmieniające"
REF_CONSOLIDATED_OF = "Tekst jednolity dla aktu"
REF_CONSOLIDATED_TEXTS = "Inf. o tekście jednolitym"
_ELI_ID = re.compile(r"DU/\d{4}/\d+$")


def cache_dir() -> Path:
    """Where extracted amending-act texts live: STILLAW_CACHE, else ~/.cache/stillaw."""
    return Path(os.environ.get("STILLAW_CACHE") or Path.home() / ".cache" / "stillaw")


def amendment_text(act_eli: str) -> str:
    """The amending act as plain text, extracted once from the Dziennik Ustaw PDF.

    Amending acts have no HTML text in ELI (textHTML is false for them), so the PDF is the
    only source, and pdftotext with -layout is what the clause regexes were tuned on.
    """
    stem = cache_dir() / act_eli.replace("/", "_")
    txt = stem.with_suffix(".txt")
    if txt.exists():
        return txt.read_text(encoding="utf-8", errors="replace")
    if shutil.which("pdftotext") is None:
        raise RuntimeError("pdftotext (poppler) is required to read amending acts; "
                           "install it or point STILLAW_CACHE at extracted texts")
    stem.parent.mkdir(parents=True, exist_ok=True)
    pdf = stem.with_suffix(".pdf")
    eli.download(eli.pdf_url(act_eli), pdf)
    subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), str(txt)],
                   check=True, capture_output=True)
    pdf.unlink(missing_ok=True)
    return txt.read_text(encoding="utf-8", errors="replace")


def latest_consolidated_text(name: str) -> dict | None:
    """The newest consolidated text of a statute named in words, as ELI reports it."""
    hits = eli.search_title(f"{CONSOLIDATED} ustawy {name}")
    tail = name.lower().split()[-1]
    candidates = [h for h in hits
                  if CONSOLIDATED in (h.get("title") or "")
                  and tail in (h.get("title") or "").lower()
                  and (h.get("ELI") or "").startswith("DU/")]
    if not candidates:
        return None
    return max(candidates, key=lambda h: h.get("promulgation") or "")


def resolve(reference: str) -> tuple[dict, list[str]]:
    """The ELI record the question is about, plus the steps taken to get there.

    A citation of the original act (Dz.U. 1997 nr 98 poz. 602 for the road traffic act) is
    redirected to its newest consolidated text, because that is the document people read.
    A title is looked up. A citation of a consolidated text, or of an act that has none, is
    taken as is.
    """
    steps: list[str] = []
    act_eli = eli.parse_reference(reference)
    if act_eli is None:
        hit = latest_consolidated_text(reference)
        if hit is None:
            raise LookupError(f"no consolidated text found for title {reference!r}")
        act_eli = hit["ELI"]
        steps.append(f"title lookup: {act_eli}")
    record = eli.act(act_eli)
    refs = record.get("references") or {}
    newer = [r.get("id") for r in refs.get(REF_CONSOLIDATED_TEXTS) or [] if _ELI_ID.match(r.get("id") or "")]
    if newer:
        target = max(newer, key=eli.position_key)
        steps.append(f"original act, redirected to newest consolidated text {target}")
        record = eli.act(target)
    return record, steps


def amendments_after(record: dict) -> list[dict]:
    """Amendments promulgated after this text, each with the ELI's own view of its dates.

    The list on the consolidated text's record carries the enactment date, not the
    promulgation date the vacatio legis is counted from, so every amendment is fetched.
    Records without that list (older texts, acts published directly) fall back to the
    underlying act's full amendment list filtered by promulgation date.
    """
    refs = record.get("references") or {}
    since = (record.get("promulgation") or "")[:10]
    if REF_AMENDMENTS_AFTER in refs:
        ids = [r.get("id") for r in refs[REF_AMENDMENTS_AFTER] or []]
    else:
        source = refs.get(REF_CONSOLIDATED_OF)
        if source:
            original = (source[0] if isinstance(source, list) else source).get("id", "")
            refs = eli.act(original).get("references") or {}
        ids = [r.get("id") for r in refs.get(REF_AMENDING_ACTS) or []
               if (r.get("id") or "").split("/")[1:2] >= [since[:4]]]
    out = []
    for act_id in ids:
        if not _ELI_ID.match(act_id or ""):
            continue
        detail = eli.act(act_id)
        promulgated = (detail.get("promulgation") or "")[:10]
        if not promulgated or promulgated <= since:
            continue
        out.append({"eli": act_id, "title": detail.get("title") or "", "promulgated": promulgated,
                    "eli_entry_into_force": detail.get("entryIntoForce") or None,
                    "eli_exceptions": " ".join((detail.get("comments") or "").split())[:300]})
        time.sleep(0.2)
    return sorted(out, key=lambda a: a["promulgated"])


def date_amendment(amendment: dict, statute: str) -> dict:
    """One amendment, dated for our statute, with the ELI date alongside as a control."""
    try:
        text = amendment_text(amendment["eli"])
        read = core.entry_into_force(text, amendment["eli"], amendment["promulgated"], statute)
    except Exception as exc:  # noqa: BLE001
        read = {"amending_article": None, "in_force": None, "basis": None,
                "how": f"error: {str(exc)[:120]}"}
    official = amendment["eli_entry_into_force"]
    out = {**amendment, "amending_article": read["amending_article"], "in_force": read["in_force"],
           "basis": read["basis"], "how": read["how"]}
    for key in ("partial_exception", "partial_exception_date"):
        if key in read:
            out[key] = read[key]
    if official and not out["in_force"]:
        # A Constitutional Court judgment has no clause to parse, but ELI carries the date
        # from which the provision loses force. Taken, with the source named.
        out["in_force"] = official
        out["how"] = f"{out['how']}; date taken from the ELI entryIntoForce field"
    if official and out["in_force"] and official != out["in_force"] and "partial_exception" not in out:
        out["disagreement"] = (f"parser: {out['in_force']}, ELI: {official}"
                               + (" (ours is for the article amending this statute, "
                                  "ELI's for the act as a whole)" if "exception" in out["how"] else ""))
    out["links"] = {"record": eli.record_url(amendment["eli"]), "text_pdf": eli.pdf_url(amendment["eli"])}
    return out


def check(reference: str, as_of: str | None = None) -> dict:
    """The product: one reference in, one status out, every step of the way shown."""
    as_of = as_of or time.strftime("%Y-%m-%d")
    record, steps = resolve(reference)
    act_eli = record["ELI"]
    statute = core.statute_name(record.get("title") or "")
    amendments = [date_amendment(a, statute) for a in amendments_after(record)]
    status, since, next_change = core.classify([a["in_force"] for a in amendments], as_of)
    in_force = [a for a in amendments if a["in_force"] and a["in_force"] <= as_of]
    first = min(in_force, key=lambda a: a["in_force"]) if in_force else None
    result = {
        "stillaw": __version__,
        "query": reference,
        "as_of": as_of,
        "eli": act_eli,
        "address": record.get("displayAddress") or eli.display_address(act_eli),
        "title": record.get("title") or "",
        "statute": statute,
        "text_published": (record.get("promulgation") or "")[:10] or None,
        "consolidated_text": CONSOLIDATED in (record.get("title") or ""),
        "status": status,
        "since": since,
        "superseded_by": ({"eli": first["eli"], "title": first["title"]} if first else None),
        "next_change": next_change,
        "amendments": amendments,
        "undetermined": [a["eli"] for a in amendments if not a["in_force"]],
        "resolution": steps,
        "links": {"record": eli.record_url(act_eli), "text_pdf": eli.pdf_url(act_eli)},
    }
    result["sha256"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return result


def survey(names: list[str] | None = None, as_of: str | None = None) -> list[dict]:
    """The same question asked of many statutes, sorted by how badly the text is out of date.

    This is how the number in the README was produced: 57 of 89 consolidated texts in DOMAIN
    were no longer the law in force on 24.08.2026. Around ten ELI requests per statute.
    """
    out = []
    for name in names or DOMAIN:
        try:
            result = check(name, as_of)
        except Exception as exc:  # noqa: BLE001
            out.append({"statute": name, "status": "error", "error": str(exc)[:120]})
            continue
        out.append({"statute": name, "eli": result["eli"], "text_published": result["text_published"],
                    "status": result["status"], "since": result["since"],
                    "next_change": result["next_change"],
                    "in_force": sum(1 for a in result["amendments"]
                                    if a["in_force"] and a["in_force"] <= result["as_of"]),
                    "ahead": sum(1 for a in result["amendments"]
                                 if a["in_force"] and a["in_force"] > result["as_of"]),
                    "undetermined": len(result["undetermined"])})
    return sorted(out, key=lambda r: (-r.get("in_force", 0), r["statute"]))
