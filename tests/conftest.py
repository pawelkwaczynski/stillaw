import pathlib

import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def offline(monkeypatch):
    """Serve ELI records from tests/fixtures/eli and amending-act texts from
    tests/fixtures/texts, so the check runs without network or pdftotext."""
    from stillaw import eli

    def fake_fetch(url, timeout=60, retries=3, accept=None):
        if url.startswith(eli.API + "/"):
            path = FIXTURES / "eli" / (url[len(eli.API) + 1:].replace("/", "_") + ".json")
            if path.exists():
                return path.read_bytes()
        raise RuntimeError(f"offline: no fixture for {url}")

    monkeypatch.setattr(eli, "fetch_bytes", fake_fetch)
    monkeypatch.setenv("STILLAW_CACHE", str(FIXTURES / "texts"))
    return FIXTURES
