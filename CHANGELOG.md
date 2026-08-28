# Changelog

## 0.1.0 (2026-08-28)

First release. The as-of engine extracted from the omniai legal benchmark into a package
with one job.

- `stillaw check <reference> [--as-of DATE] [--json]`: status of a Polish consolidated
  text (`current`, `superseded`, `vacatio_legis`, `undetermined`) with every amendment,
  its entry-into-force date and the final-article clause it was read from.
- Entry-into-force parser for Polish amending acts: explicit dates, periods in days,
  months and years, "first day of the month after", compound periods, exception groups
  by article range and by chapter, partial exceptions, Constitutional Court judgments.
- ELI client for api.sejm.gov.pl, standard library only, curl fallback for TLS trust.
- Optional MCP server with one tool, `stillaw_check`.
- Comparative readers for legislation.gov.uk (UK) and boe.es (ES), library only.
- 64 tests, all offline.
