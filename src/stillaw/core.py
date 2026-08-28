"""Three states of legal currency, resolved from the Dziennik Ustaw itself.

Most tools treat currency as a boolean: the consolidated text is either up to date or
superseded. The boolean loses the case that matters most in practice. An amendment that
has been promulgated but is still in its vacatio legis has changed nothing: the consolidated
text is still the law, and a system that warns "this text is out of date" is right about the
document and wrong about the law.

So the state is one of four:

  current        no amendment was promulgated after the consolidated text
  superseded     at least one amendment is already in force
  vacatio_legis  amendments exist, none of them is in force yet
  undetermined   an amendment exists whose date could not be established

Resolving the third state means reading the final article of every amending act and doing
the date arithmetic the act prescribes ("po uplywie 14 dni od dnia ogloszenia", "pierwszego
dnia miesiaca nastepujacego po uplywie 6 miesiecy"), including the exception clauses that
give a different date to selected articles. Where the wording is not one this parser
recognises, the amendment is reported as undetermined rather than guessed: a wrong date here
silently moves an act between states, which is the one error nobody downstream can catch.

This module is pure: text in, dates out. Fetching lives in eli.py and pl.py.
"""
import calendar
import datetime
import re

MONTHS = {"stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, "maja": 5, "czerwca": 6,
          "lipca": 7, "sierpnia": 8, "wrzesnia": 9, "września": 9, "pazdziernika": 10,
          "października": 10, "listopada": 11, "grudnia": 12}
WORD_NUMBERS = {"miesiaca": 1, "miesiąca": 1, "dwoch": 2, "dwóch": 2, "trzech": 3,
                "czterech": 4, "pieciu": 5, "pięciu": 5, "szesciu": 6, "sześciu": 6,
                "roku": 12, "dwunastu": 12}
# The clause that decides everything. Kept verbatim in the output so a human can check it.
ENTRY_CLAUSE = re.compile(r"(?:Ustawa|Rozporządzenie)\s+wchodzi\s+w\s+życie", re.I)
# The clause ends where the act does, not at the first full stop: an exception list is full
# of "z dniem 10 lipca 2026 r.;" and cutting there hides every group but the first, which is
# how art. 6 of Dz.U. 2026 poz. 644 came out as May 2026 instead of January 2030.
CLAUSE_END = re.compile(r"Prezydent\s+Rzeczypospolitej|Marszałek\s+Sejmu|"
                        r"^\s*Art\.\s*\d+[a-z]?\.", re.M | re.I)
# Footnotes and page furniture sit inside the clause in the extracted text and carry article
# numbers of their own.
NOISE = re.compile(r"\d+\)\s*Zmian[ay][^.]{0,200}?\.|Dziennik\s+Ustaw\s*[–-]\s*\d+\s*[–-]\s*"
                   r"Poz\.\s*\d+", re.I)
# An exception clause can carry several groups, each with its own date:
#   "z wyjatkiem: 1) art. 9 ..., ktore wchodza w zycie z dniem 10 lipca 2026 r.;
#                 2) przepisow: a) art. 1 pkt 3 ... - ktore wchodza w zycie 10 stycznia 2028 r.;
#                 3) przepisow: a) art. 3-6 ... - ktore wchodza w zycie 10 stycznia 2030 r."
# Reading only the first group is how this parser first dated the Commercial Companies Code
# amendment to May 2026 when the article carrying those changes enters into force in 2030.
EXCEPTION_START = re.compile(r"z\s+wyjątkiem\b", re.I)
GROUP = re.compile(r"(.*?)(?:który|które|ktore)\s+(?:wchodzi|wchodzą|wchodza)\s+"
                   r"w\s+życie(.{0,120}?)(?:;|\.\s|$)", re.S | re.I)
# "art. 7: - pkt 1, 4 i 5" defers only part of an article, which this parser does not model.
PARTIAL = re.compile(r"art\.\s*NUMBER\s*:?\s*(?:–|-|—)?\s*pkt", re.I)
ARTICLE_LIST = re.compile(r"art\.\s*(\d+)(?:\s*[-–—]\s*(\d+))?", re.I)
# An exception can defer whole chapters instead of listing articles: "z wyjatkiem art. 125
# ust. 4 ... oraz rozdzialow 3-5, 8 i 9". The AI act's amendment to the Code of Civil
# Procedure sits in art. 115, which is in chapter 9, so reading only the article numbers
# dated it three months early.
CHAPTER_LIST = re.compile(r"rozdzia[łl]\w*\s+((?:\d+(?:\s*[-–—]\s*\d+)?[,\s]*(?:i|oraz)?\s*)+)",
                          re.I)
CHAPTER_HEADING = re.compile(r"^\s*Rozdzia[łl]\s+(\d+)", re.I | re.M)
ARTICLE_HEADING = re.compile(r"^\s*Art\.\s*(\d+)[a-z]?\.", re.M)
# "W ustawie z dnia 16 wrzesnia 2011 r. o szczegolnych rozwiazaniach ... (Dz. U. ...)": the
# name of the act being amended ends where its Dz.U. citation begins. Matching the target
# name anywhere in the opening picks up blocks that amend a different act and merely cite
# ours in the chain of previous amendments.
AMENDED_ACT_OPENING = re.compile(r"W\s+ustawie\s+(.{0,220}?)\(Dz\.\s*U\.", re.S | re.I)
# "...w sprawie ogloszenia jednolitego tekstu ustawy - Kodeks pracy" -> "Kodeks pracy"
CONSOLIDATED_TITLE = re.compile(r"jednolitego\s+tekstu\s+(?:ustawy|rozporządzenia)?\s*[-–—]?\s*(.+)$",
                                re.I | re.S)
TITLE_TAIL = re.compile(r"\s*(?:\(.*|z\s+dnia\s+\d.*)$", re.S)
CONSTITUTIONAL_COURT = re.compile(r"Wyrok\s+Trybunału\s+Konstytucyjnego", re.I)

UNRECOGNISED = "unrecognised clause"


def add_months(d: datetime.date, n: int) -> datetime.date:
    """Calendar months, clamped: 31 January plus one month is the last day of February."""
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    return datetime.date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _count(token: str) -> int | None:
    return int(token) if token.isdigit() else WORD_NUMBERS.get(token.lower())


def resolve_date(clause: str, promulgated: str) -> tuple[str | None, str]:
    """The date an entry-into-force clause resolves to, plus how it was read.

    A period counted "po uplywie N dni od dnia ogloszenia" starts the day after publication
    and the act enters into force the day after it ends, which is publication plus N plus one.
    Checked against four acts whose dates were read by hand: Dz.U. 2026 poz. 25 (12.01 plus
    14 dni gives 27.01), poz. 252 (02.03 plus miesiac gives 03.04), poz. 473 (07.04 plus
    3 miesiace gives 08.07), poz. 875 (30.06 plus 6 miesiecy, first day of the next month,
    gives 01.01.2027).
    """
    k = " ".join(clause.split())
    # The base rule is what stands BEFORE the exceptions. Reading the whole clause makes the
    # first exception date look like the base one, because an explicit date is matched first.
    cut = EXCEPTION_START.search(k)
    if cut:
        k = k[:cut.start()]
    pub = datetime.date.fromisoformat(promulgated)
    m = re.search(r"z\s+dniem\s+(\d{1,2})\s+(\w+)\s+(\d{4})", k, re.I)
    if m and m.group(2).lower() in MONTHS:
        return datetime.date(int(m.group(3)), MONTHS[m.group(2).lower()],
                             int(m.group(1))).isoformat(), "explicit date"
    if re.search(r"z\s+dniem\s+następującym\s+po\s+dniu\s+ogłoszenia", k, re.I):
        return (pub + datetime.timedelta(days=1)).isoformat(), "day after promulgation"
    if re.search(r"z\s+dniem\s+ogłoszenia", k, re.I):
        return pub.isoformat(), "on promulgation"
    m = re.search(r"pierwszego\s+dnia\s+miesiąca\s+następującego\s+po\s+upływie\s+"
                  r"(\d+|\w+)\s+miesi\w+", k, re.I)
    if m:
        n = _count(m.group(1))
        if n:
            end = add_months(pub, n)
            following = add_months(end.replace(day=1), 1)
            return following.isoformat(), f"first day of the month after {n} months"
    # Compound period: "po uplywie 2 lat i 3 miesiecy od dnia ogloszenia". Reading only the
    # first part gave a date a quarter early; the ELI entryIntoForce field caught it
    # (Dz.U. 2026 poz. 187).
    m = re.search(r"po\s+upływie\s+(\d+|\w+)\s+(?:lat\w*|roku)\s+i\s+(\d+|\w+)\s+miesi\w+", k, re.I)
    if m:
        years, months = _count(m.group(1)), _count(m.group(2))
        if years is not None and months is not None:
            date = add_months(pub, years * 12 + months) + datetime.timedelta(days=1)
            return date.isoformat(), f"after {years} years and {months} months"
    # "po uplywie miesiaca" and "po uplywie roku" carry no count: the unit is the count.
    m = re.search(r"po\s+upływie\s+(?:(\d+|\w+)\s+)?"
                  r"(dni|dnia|miesiąca|miesiaca|miesi\w+|roku|lat\w*)", k, re.I)
    if m:
        count = (m.group(1) or "").lower()
        unit = m.group(2).lower()
        if not count:
            n = 1 if unit.startswith(("miesiąc", "miesiac")) else (12 if unit == "roku" else None)
        else:
            n = _count(count)
        if n is not None:
            if unit.startswith(("dni", "dnia")):
                return (pub + datetime.timedelta(days=n + 1)).isoformat(), f"after {n} days"
            if unit.startswith("lat"):
                n *= 12
            date = add_months(pub, n) + datetime.timedelta(days=1)
            return date.isoformat(), f"after {n} months"
    return None, UNRECOGNISED


def articles_in_list(text: str) -> set[int]:
    """Article numbers of the AMENDING act named in an exception clause, ranges expanded."""
    out: set[int] = set()
    for m in ARTICLE_LIST.finditer(text):
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        out.update(range(start, end + 1))
    return out


def chapters_in_list(text: str) -> set[int]:
    """Chapter numbers an exception clause names, ranges expanded."""
    out: set[int] = set()
    for m in CHAPTER_LIST.finditer(text):
        for span in re.finditer(r"(\d+)(?:\s*[-–—]\s*(\d+))?", m.group(1)):
            start = int(span.group(1))
            end = int(span.group(2)) if span.group(2) else start
            out.update(range(start, end + 1))
    return out


def chapter_of_article(text: str, number: int) -> int | None:
    """Which chapter of the amending act an article belongs to, by position in the text."""
    headings = [(int(m.group(1)), m.start()) for m in CHAPTER_HEADING.finditer(text)]
    if not headings:
        return None
    target = next((m.start() for m in ARTICLE_HEADING.finditer(text)
                   if int(m.group(1)) == number), None)
    if target is None:
        return None
    current = None
    for chapter, position in headings:
        if position < target:
            current = chapter
        else:
            break
    return current


def amending_article_for(text: str, statute: str) -> int | None:
    """Which article of the amending act carries the changes to our statute.

    An exception clause is written in terms of the amending act's own articles, so
    "z wyjatkiem art. 9-12" can only be applied once we know whether our changes live
    in art. 1 or in art. 40.
    """
    for m in re.finditer(r"Art\.\s*(\d+)\.\s*W\s+ustawie", text):
        opening = AMENDED_ACT_OPENING.search(text[m.start():m.start() + 600])
        if opening and statute.lower() in " ".join(opening.group(1).split()).lower():
            return int(m.group(1))
    return None


def statute_name(title: str) -> str:
    """The statute name as an amending act would write it.

    "...w sprawie ogloszenia jednolitego tekstu ustawy - Kodeks pracy" gives "Kodeks pracy".
    A title that is not a consolidated text (the 2026 AI act was published directly) is
    returned with its date and citation stripped.
    """
    title = " ".join((title or "").split())
    m = CONSOLIDATED_TITLE.search(title)
    name = m.group(1) if m else title
    return TITLE_TAIL.sub("", name).strip(" .,-–—")


def entry_into_force(text: str, eli: str, promulgated: str, statute: str) -> dict:
    """When the changes to OUR statute, made by this amending act, start to apply.

    `text` is the amending act as extracted from the Dziennik Ustaw PDF; `promulgated` is
    its publication date (ISO); `statute` is the name the amending act uses for our act.
    """
    result = {"eli": eli, "promulgated": promulgated, "amending_article": None,
              "in_force": None, "basis": None, "how": "no entry-into-force clause"}
    # Not every act in the amendments list is an amending act. A Constitutional Court
    # judgment removes a provision without any vacatio legis clause to parse, and the date it
    # takes effect can be deferred in the judgment itself. Guessing would be worse than
    # saying that a human has to read this one.
    if CONSTITUTIONAL_COURT.search(text[:3000]):
        result.update({"basis": "Constitutional Court judgment, not an amending act",
                       "how": "judgment: provision loses force on the date in the ruling"})
        return result
    m = ENTRY_CLAUSE.search(text)
    if not m:
        return result
    tail = text[m.end():m.end() + 4000]
    end = CLAUSE_END.search(tail)
    clause = " ".join(NOISE.sub(" ", tail[:end.start()] if end else tail).split())
    result["basis"] = f"wchodzi w życie {clause}"[:300]
    result["amending_article"] = amending_article_for(text, statute)
    base, how = resolve_date(clause, promulgated)
    start = EXCEPTION_START.search(clause)
    if start:
        ours = result["amending_article"]
        if ours is None:
            result["how"] = ("exceptions present, but the article amending our statute "
                             "was not found: needs a human")
            return result
        our_chapter = chapter_of_article(text, ours)
        for group in GROUP.finditer(clause[start.end():]):
            covered = articles_in_list(group.group(1))
            chapters = chapters_in_list(group.group(1))
            via_chapter = our_chapter is not None and our_chapter in chapters
            if ours not in covered and not via_chapter:
                continue
            if via_chapter and ours not in covered:
                date2, how2 = resolve_date(group.group(2), promulgated)
                result.update({"in_force": date2, "how": f"exception via chapter {our_chapter}: {how2}"})
                return result
            partial = re.search(PARTIAL.pattern.replace("NUMBER", str(ours)), group.group(1), re.I)
            date2, how2 = resolve_date(group.group(2), promulgated)
            scope = " ".join(group.group(1).split()).lstrip(": ")
            if partial:
                # "z wyjatkiem art. 1 pkt 9" defers ONE instruction of our block, not the
                # block. The act-level answer is the base date; the deferred instruction is
                # recorded so a per-provision check can use it.
                result.update({"in_force": base,
                               "how": f"{how}; partial exception for art. {ours}: {scope[:120]}",
                               "partial_exception": scope[:300],
                               "partial_exception_date": date2})
            elif date2 is None:
                result["how"] = f"exception covers art. {ours} but its date is unrecognised: needs a human"
            else:
                result.update({"in_force": date2, "how": f"exception: {how2}"})
            return result
    result.update({"in_force": base, "how": how})
    return result


def classify(dates: list[str | None], as_of: str) -> tuple[str, str | None, str | None]:
    """Status of a consolidated text given the in-force dates of its amendments.

    Returns (status, since, next_change). `since` is the earliest amendment already in
    force; `next_change` the earliest one still ahead. An amendment with no date cannot be
    treated as no change: that would be silent false calm, because the text may already be
    superseded and we simply do not know. Such an act is `undetermined`, and a human reads it.
    """
    known = [d for d in dates if d]
    in_force = sorted(d for d in known if d <= as_of)
    ahead = sorted(d for d in known if d > as_of)
    next_change = ahead[0] if ahead else None
    if in_force:
        return "superseded", in_force[0], next_change
    if ahead:
        return "vacatio_legis", None, next_change
    if any(d is None for d in dates):
        return "undetermined", None, None
    return "current", None, None
