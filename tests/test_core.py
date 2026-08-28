"""Entry-into-force arithmetic, checked against acts read by hand.

The dates on the right were read from the final article of each amending act on 23.08.2026.
If this table and the parser ever disagree, one of them is wrong about the law, so the table
is a test rather than a comment.
"""
import datetime

import pytest

from stillaw import core
from tests.conftest import FIXTURES

CLAUSES = [
    # clause, promulgation date, expected entry into force
    ("po upływie 14 dni od dnia ogłoszenia.", "2026-01-12", "2026-01-27"),      # DU/2026/25
    ("z dniem 1 stycznia 2026 r.", "2025-10-21", "2026-01-01"),                 # DU/2025/1423
    ("po upływie 3 miesięcy od dnia ogłoszenia", "2026-04-07", "2026-07-08"),   # DU/2026/473
    ("po upływie 14 dni od dnia ogłoszenia", "2025-11-28", "2025-12-13"),       # DU/2025/1661
    ("po upływie 3 miesięcy od dnia ogłoszenia.", "2026-08-04", "2026-11-05"),  # DU/2026/1046
    ("po upływie 6 miesięcy od dnia ogłoszenia.", "2025-06-23", "2025-12-24"),  # DU/2025/807
    ("po upływie miesiąca od dnia ogłoszenia.", "2026-03-02", "2026-04-03"),    # DU/2026/252
    ("z dniem 1 października 2026 r.", "2026-06-25", "2026-10-01"),             # DU/2026/846
    ("pierwszego dnia miesiąca następującego po upływie 6 miesięcy od dnia ogłoszenia",
     "2026-06-30", "2027-01-01"),                                              # DU/2026/875
    ("po upływie 3 miesięcy od dnia ogłoszenia.", "2026-06-23", "2026-09-24"),  # DU/2026/825
    ("z dniem 1 stycznia 2027 r.", "2026-08-18", "2027-01-01"),                 # DU/2026/1098
    ("po upływie 14 dni od dnia ogłoszenia.", "2026-06-19", "2026-07-04"),      # DU/2026/815
    ("z dniem następującym po dniu ogłoszenia", "2026-04-07", "2026-04-08"),
    ("z dniem ogłoszenia", "2026-04-07", "2026-04-07"),
    ("po upływie roku od dnia ogłoszenia", "2025-01-15", "2026-01-16"),
    # Compound period, confirmed by the ELI entryIntoForce field for Dz.U. 2026 poz. 187.
    ("po upływie 2 lat i 3 miesięcy od dnia ogłoszenia", "2026-02-18", "2028-05-19"),
    ("po upływie 1 roku i 6 miesięcy od dnia ogłoszenia", "2025-01-10", "2026-07-11"),
]
# Clauses the parser must NOT resolve: a guess here moves an act between states.
UNRECOGNISED = [
    ("w terminie określonym w przepisach wykonawczych", "2026-01-01"),
    ("z dniem wejścia w życie ustawy o osobistych kontach inwestycyjnych", "2026-01-01"),
]
MONTH_EDGES = [
    (datetime.date(2026, 1, 31), 1, datetime.date(2026, 2, 28)),
    (datetime.date(2024, 1, 31), 1, datetime.date(2024, 2, 29)),
    (datetime.date(2026, 12, 15), 1, datetime.date(2027, 1, 15)),
    (datetime.date(2026, 3, 2), 12, datetime.date(2027, 3, 2)),
]
ARTICLE_LISTS = [
    ("art. 1 pkt 6 lit. b i pkt 17, art. 9–12 oraz art. 17", {1, 9, 10, 11, 12, 17}),
    ("art. 41 pkt 2", {41}),
    ("art. 3 i art. 5", {3, 5}),
]
CHAPTER_LISTS = [
    ("rozdziałów 3–5, 8 i 9", {3, 4, 5, 8, 9}),
    ("rozdziału 2", {2}),
    ("rozdziałach 1 i 4", {1, 4}),
    ("art. 8–18 oraz rozdziałów 3–5, 8 i 9", {3, 4, 5, 8, 9}),
]
# Real clause from Dz.U. 2026 poz. 644, the one that first fooled the parser: three groups
# of exceptions, and the article carrying the Commercial Companies Code changes (art. 6) is
# in the third, deferred to 2030.
CLAUSE_644 = (
    "po upływie 14 dni od dnia ogłoszenia, z wyjątkiem: 1) art. 9 pkt 1 i pkt 2 w zakresie "
    "art. 92a, art. 92e i art. 92f, które wchodzą w życie z dniem 10 lipca 2026 r.; "
    "2) przepisów: a) art. 1 pkt 3, b) art. 2, c) art. 7: – pkt 1, 4 i 5, e) art. 18 "
    "– które wchodzą w życie z dniem 10 stycznia 2028 r.; 3) przepisów: a) art. 3–6, "
    "b) art. 7: – pkt 2 i 3, c) art. 8, h) art. 13–17 – które wchodzą w życie z dniem "
    "10 stycznia 2030 r.")
EXCEPTIONS = [
    # clause, promulgation, article of the amending act, expected entry into force
    (CLAUSE_644, "2026-05-14", 6, "2030-01-10"),    # third group, range art. 3-6
    (CLAUSE_644, "2026-05-14", 9, "2026-07-10"),    # first group
    (CLAUSE_644, "2026-05-14", 2, "2028-01-10"),    # second group
    (CLAUSE_644, "2026-05-14", 15, "2030-01-10"),   # range art. 13-17
    (CLAUSE_644, "2026-05-14", 5, "2030-01-10"),
    (CLAUSE_644, "2026-05-14", 20, "2026-05-29"),   # not in any exception: base date
    ("po upływie 14 dni od dnia ogłoszenia, z wyjątkiem art. 41 pkt 2, który wchodzi w życie "
     "z dniem 29 listopada 2025 r.", "2025-11-28", 40, "2025-12-13"),
    ("po upływie 3 miesięcy od dnia ogłoszenia, z wyjątkiem art. 1 pkt 6 lit. b i pkt 17, "
     "art. 9–12 oraz art. 17, które wchodzą w życie z dniem następującym po dniu ogłoszenia.",
     "2026-04-07", 3, "2026-07-08"),
    ("po upływie 3 miesięcy od dnia ogłoszenia, z wyjątkiem art. 1 pkt 6 lit. b i pkt 17, "
     "art. 9–12 oraz art. 17, które wchodzą w życie z dniem następującym po dniu ogłoszenia.",
     "2026-04-07", 11, "2026-04-08"),
]
# The same acts read end to end from the extracted Dziennik Ustaw texts rather than from a
# clause typed into this file. This is the test that catches a clause the extractor
# truncates: art. 6 of Dz.U. 2026 poz. 644 sits in the third group of exceptions, 2600
# characters into the provision.
FROM_TEXTS = [
    ("DU/2026/644", "2026-05-14", "Kodeks spółek handlowych", 6, "2030-01-10"),
    ("DU/2026/25", "2026-01-12", "Kodeks pracy", 1, "2026-01-27"),
    ("DU/2025/1661", "2025-11-28", "Kodeks pracy", 40, "2025-12-13"),
    ("DU/2025/807", "2025-06-23", "Kodeks pracy", 1, "2025-12-24"),
    ("DU/2026/473", "2026-04-07", "o systemie ubezpieczeń społecznych", 5, "2026-07-08"),
    ("DU/2026/473", "2026-04-07", "Kodeks pracy", 3, "2026-07-08"),
    ("DU/2026/252", "2026-03-02", "o krajowym systemie cyberbezpieczeństwa", 1, "2026-04-03"),
    ("DU/2026/846", "2026-06-25", "Ordynacja podatkowa", 1, "2026-10-01"),
    ("DU/2026/875", "2026-06-30", "Ordynacja podatkowa", 6, "2027-01-01"),
    # Chapter-level exception: art. 115 and art. 124 of the AI act sit in chapter 9, which the
    # final article defers by three months, so its amendments to the Code of Civil Procedure
    # and to the cybersecurity act are not in force on the base date.
    ("DU/2026/1003", "2026-07-27", "Kodeks postępowania cywilnego", 115, "2026-10-28"),
    ("DU/2026/1003", "2026-07-27", "o krajowym systemie cyberbezpieczeństwa", 124, "2026-10-28"),
]


@pytest.mark.parametrize("clause, promulgated, expected", CLAUSES)
def test_clause_resolves(clause, promulgated, expected):
    assert core.resolve_date(clause, promulgated)[0] == expected


@pytest.mark.parametrize("clause, promulgated", UNRECOGNISED)
def test_unrecognised_clause_is_not_guessed(clause, promulgated):
    assert core.resolve_date(clause, promulgated) == (None, core.UNRECOGNISED)


@pytest.mark.parametrize("start, months, expected", MONTH_EDGES)
def test_add_months_clamps_to_month_end(start, months, expected):
    assert core.add_months(start, months) == expected


@pytest.mark.parametrize("text, expected", ARTICLE_LISTS)
def test_articles_in_list(text, expected):
    assert core.articles_in_list(text) == expected


@pytest.mark.parametrize("text, expected", CHAPTER_LISTS)
def test_chapters_in_list(text, expected):
    assert core.chapters_in_list(text) == expected


@pytest.mark.parametrize("clause, promulgated, article, expected", EXCEPTIONS)
def test_exception_groups(clause, promulgated, article, expected):
    """The clause and the article number are the whole input; no text, no network."""
    result = None
    start = core.EXCEPTION_START.search(clause)
    if start:
        for group in core.GROUP.finditer(clause[start.end():]):
            if article in core.articles_in_list(group.group(1)):
                result = core.resolve_date(group.group(2), promulgated)[0]
                break
    if result is None:
        result = core.resolve_date(clause, promulgated)[0]
    assert result == expected


@pytest.mark.parametrize("act, promulgated, statute, article, expected", FROM_TEXTS)
def test_entry_into_force_from_text(act, promulgated, statute, article, expected):
    text = (FIXTURES / "texts" / (act.replace("/", "_") + ".txt")).read_text(encoding="utf-8")
    result = core.entry_into_force(text, act, promulgated, statute)
    assert (result["amending_article"], result["in_force"]) == (article, expected), result["how"]


def test_amendment_without_date_is_undetermined():
    """An amendment whose date cannot be established must NOT yield "current". The same
    mistake was caught in the UK reader: no date counted as no change, silent false calm."""
    assert core.classify([None], "2026-08-24")[0] == "undetermined"


def test_no_amendments_is_current():
    """The opposite case, so the fix above does not turn into panic."""
    assert core.classify([], "2026-08-24") == ("current", None, None)
