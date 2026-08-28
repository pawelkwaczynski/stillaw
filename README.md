# Stillaw

Is this still the law?

Give it a Polish statute (a Dziennik Ustaw citation, an ELI id, or a title) and a date, and
it tells you whether the consolidated text is still the law in force on that date, which
amendment changed it, from when, and quotes the clause it read the date from. No language
model anywhere in the loop: everything is resolved from the ELI API of the Dziennik Ustaw
(api.sejm.gov.pl), deterministically, with a sha256 of the answer.

57 of 89 Polish consolidated statute texts checked on 24.08.2026 were no longer the law in
force. A text can be wrong and still be the newest one there is.

## Install

```
pip install stillaw
```

Python 3.11 or newer, standard library only. Two external binaries are used: `curl` as a
fallback when Python does not trust the API's certificate chain, and `pdftotext` (poppler)
to read amending acts, which the ELI serves as PDF only.

## Command line

```
stillaw check "Dz.U. 2024 poz. 1251" --as-of 2026-08-28
```

```
Dz.U. 2024 poz. 1251  Prawo o ruchu drogowym  (consolidated text published 2024-08-19)
status as of 2026-08-28: SUPERSEDED since 2025-07-25
superseded by: DU/2025/820  Ustawa z dnia 9 maja 2025 r. o zmianie ustawy o Służbie Więziennej oraz niektórych innych
amendments after the text: 7
  DU/2025/820    promulgated 2025-06-24  in force 2025-07-25  after 30 days
      Ustawa z dnia 9 maja 2025 r. o zmianie ustawy o Służbie Więziennej oraz niektórych innych ustaw
      basis: wchodzi w życie po upływie 30 dni od dnia ogłoszenia, z wyjątkiem art. 27, art. 28 i art. 30, które wchodzą w życie po upływie 14 dni od dnia ogłoszenia.
  DU/2025/1006   promulgated 2025-07-25  in force 2025-08-09  after 14 days
      Ustawa z dnia 25 czerwca 2025 r. o zmianie ustawy o informatyzacji działalności podmiotów realizując
      basis: wchodzi w życie po upływie 14 dni od dnia ogłoszenia, z wyjątkiem: 1) art. 3 pkt 2 lit. a i b oraz pkt 3, art. 4 pkt 2, 4 i 5 oraz art. 9, które wchodzą w życie
  DU/2025/1676   promulgated 2025-12-02  in force 2026-03-03  after 3 months; partial exception for art. 1: 1) art. 1 pkt 6 i 16 oraz art. 4 pkt 11 i 13,
      Ustawa z dnia 17 października 2025 r. o zmianie ustawy - Prawo o ruchu drogowym oraz niektórych inny
      basis: wchodzi w życie po upływie 3 miesięcy od dnia ogłoszenia, z wyjątkiem: 1) art. 1 pkt 6 i 16 oraz art. 4 pkt 11 i 13, które wchodzą w życie z dniem następującym
  DU/2025/1734   promulgated 2025-12-09  in force 2026-06-10  after 6 months; partial exception for art. 1: 1) art. 1 pkt 5, pkt 11, pkt 13 lit. b i pkt 15–17 oraz art. 3,
      Ustawa z dnia 7 listopada 2025 r. o zmianie ustawy - Prawo o ruchu drogowym
      basis: wchodzi w życie po upływie 6 miesięcy od dnia ogłoszenia, z wyjątkiem: 1) art. 1 pkt 5, pkt 11, pkt 13 lit. b i pkt 15–17 oraz art. 3, które wchodzą w życie po
  DU/2025/1843   promulgated 2025-12-23  in force 2026-06-24  after 6 months; partial exception for art. 1: 1) art. 1 pkt 7–9,
      Ustawa z dnia 21 listopada 2025 r. o zmianie ustawy - Prawo o ruchu drogowym oraz niektórych innych
      basis: wchodzi w życie po upływie 6 miesięcy od dnia ogłoszenia, z wyjątkiem: 1) art. 1 pkt 7–9, które wchodzą w życie z dniem 5 lipca 2026 r.; 2) art. 2, art. 4 i art
  DU/2025/1872   promulgated 2025-12-29  in force 2026-01-29  after 30 days; partial exception for art. 4: art. 4 pkt 1, 3 i 4 oraz art. 6,
      Ustawa z dnia 4 grudnia 2025 r. o zmianie niektórych ustaw w celu poprawy bezpieczeństwa ruchu drogo
      basis: wchodzi w życie po upływie 30 dni od dnia ogłoszenia, z wyjątkiem art. 4 pkt 1, 3 i 4 oraz art. 6, które wchodzą w życie po upływie 3 miesięcy od dnia ogłoszeni
  DU/2026/180    promulgated 2026-02-17  in force 2026-05-18  after 3 months
      Ustawa z dnia 23 stycznia 2026 r. o zmianie ustawy - Prawo o ruchu drogowym oraz niektórych innych u
      basis: wchodzi w życie po upływie 3 miesięcy od dnia ogłoszenia, z wyjątkiem: 1) art. 2 pkt 1 i 2, art. 4 pkt 1 lit. b–e i pkt 2–4, które wchodzą w życie z dniem 3 mar
record: https://api.sejm.gov.pl/eli/acts/DU/2024/1251
sha256: 37ff72320e8014d8932fbe9cd329be1fba39d1756fd41f25f0560ebf065acc49
```

The same with `--json` gives every field above as data: the amendment list with
`promulgated`, `in_force`, `basis` (the clause, verbatim), `how` (which rule resolved it),
`amending_article` (which article of the amending act touches this statute), the ELI's own
`eli_entry_into_force` for the act as a whole, a `disagreement` note when the two differ
without an exception explaining it, and links to the ELI record and PDF of every act.

A text with nothing after it:

```
stillaw check DU/2025/1691 --as-of 2026-08-28 --json
```

```json
{
 "stillaw": "0.1.0",
 "query": "DU/2025/1691",
 "as_of": "2026-08-28",
 "eli": "DU/2025/1691",
 "address": "Dz.U. 2025 poz. 1691",
 "title": "Obwieszczenie Marszałka Sejmu Rzeczypospolitej Polskiej z dnia 7 listopada 2025 r. w sprawie ogłoszenia jednolitego tekstu ustawy - Kodeks postępowania administracyjnego",
 "statute": "Kodeks postępowania administracyjnego",
 "text_published": "2025-12-03",
 "consolidated_text": true,
 "status": "current",
 "since": null,
 "superseded_by": null,
 "next_change": null,
 "amendments": [],
 "undetermined": [],
 "resolution": [],
 "links": {
  "record": "https://api.sejm.gov.pl/eli/acts/DU/2025/1691",
  "text_pdf": "https://api.sejm.gov.pl/eli/acts/DU/2025/1691/text.pdf"
 },
 "sha256": "b56e33a17e763a3f4ad4bf987f607b71de70184094bb6dd652248ad13cade14d"
}
```

Accepted references: `Dz.U. 2024 poz. 1251`, `Dz. U. z 2024 r. poz. 1251`, `DU/2024/1251`,
or a title such as `Kodeks pracy` (the newest consolidated text is looked up). A citation of
the original act is redirected to its newest consolidated text.

`stillaw survey` runs the check over a built-in list of 89 statutes a business or
technology lawyer opens. It makes several hundred requests; use it deliberately.

## Python

```python
from stillaw import pl
result = pl.check("Dz.U. 2024 poz. 1251", as_of="2026-08-28")
result["status"], result["since"], result["superseded_by"]["eli"]
```

## MCP

```
pip install "stillaw[mcp]"
python -m stillaw.mcp_server
```

One tool, `stillaw_check(reference, as_of=None)`, returning the same dict as the CLI's
`--json`. Claude Desktop configuration:

```json
{"mcpServers": {"stillaw": {"command": "python", "args": ["-m", "stillaw.mcp_server"]}}}
```

## What it knows and what it doesn't

The status is one of four, and the fourth is the honest one:

- `current`: no amendment was promulgated after the consolidated text.
- `superseded`: at least one amendment is already in force on the as-of date.
- `vacatio_legis`: amendments exist, none is in force yet. The text is still the law.
- `undetermined`: an amendment exists whose date could not be established. This is never
  reported as `current`, because the text may already be superseded and we simply do not
  know. A human reads that act; its id is listed under `undetermined`.

What it reads: the final article of each amending act ("Ustawa wchodzi w życie ..."),
including exception groups that defer whole articles or chapters of the amending act to
another date. It knows which article of the amending act touches your statute, so the
date it reports is the one for your statute, not for the act as a whole. The ELI's own
`entryIntoForce` field is fetched alongside as an independent control.

What it does not do:

- It works at the level of the act, not the provision. An exception that defers a single
  point of an article ("art. 1 pkt 9") is recorded as `partial_exception`, but the status
  follows the base date. Whether the specific paragraph you care about has changed is a
  question this version does not answer.
- A clause it does not recognise is not guessed. Dates set by another act ("z dniem
  wejścia w życie ustawy o ..."), by regulation, or by a Constitutional Court judgment are
  reported as undetermined, with the ELI date used where the ELI has one.
- It covers the Dziennik Ustaw (statutes and regulations). Monitor Polski, EU law and
  local law are out of scope.
- It says nothing about whether the amendment matters. A one-word change and a rewrite
  both make the text superseded.
- Readers for legislation.gov.uk (`stillaw.uk`) and boe.es (`stillaw.es`) exist as
  library functions for comparison. Both jurisdictions publish the in-force data the
  Polish parser has to reconstruct from prose. They are not wired into the CLI yet.

## License

MIT. Copyright 2026 Paweł Kwaczyński.
