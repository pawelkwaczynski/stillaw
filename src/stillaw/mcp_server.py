"""Optional MCP server exposing one tool, `stillaw_check`.

Needs the `mcp` package (`pip install stillaw[mcp]`); the import is deferred so the rest
of the package works without it. Run with `python -m stillaw.mcp_server` (stdio transport).
"""
import sys

from . import pl

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


def build():
    server = FastMCP("stillaw")

    @server.tool()
    def stillaw_check(reference: str, as_of: str | None = None) -> dict:
        """Is this Polish act still the law? `reference` is a Dziennik Ustaw citation
        ("Dz.U. 2024 poz. 1251"), an ELI id ("DU/2024/1251") or a statute title; `as_of` an
        ISO date (default today). Returns status current | superseded | vacatio_legis |
        undetermined with every amendment, its entry-into-force date and the clause it was
        read from."""
        return pl.check(reference, as_of)

    return server


def main() -> int:
    if FastMCP is None:
        print("stillaw: the mcp package is not installed; pip install 'stillaw[mcp]'", file=sys.stderr)
        return 1
    build().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
