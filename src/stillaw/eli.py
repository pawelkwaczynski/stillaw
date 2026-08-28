"""Client for the ELI API of the Polish Dziennik Ustaw (api.sejm.gov.pl).

No key, no rate limit documented, JSON records per act. Fetching goes through urllib and
falls back to curl: on macOS Python often does not trust the certificate chain the API
serves while curl, reading the system keychain, gets a 200. Rather than weaken verification
the fallback lets curl do the trusting. A silent skip would be the worst outcome, because
an act would look current only because nothing was checked.
"""
import json
import re
import ssl
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from . import __version__

API = "https://api.sejm.gov.pl/eli/acts"
USER_AGENT = f"stillaw/{__version__}"

# "Dz.U. 2024 poz. 1251", "Dz. U. z 2024 r. poz. 1251", "Dz.U.2024.1251", "DU/2024/1251"
_REFERENCE = re.compile(
    r"(?:Dz\.?\s*U\.?|DU)\s*/?\s*(?:z\s+)?(\d{4})\s*(?:r\.?)?\s*(?:poz\.?|/|\.)\s*(\d+)",
    re.I)


def fetch_bytes(url: str, timeout: int = 60, retries: int = 3, accept: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except ssl.SSLError as exc:
            # The trust store will not fix itself between attempts; curl knows better.
            last = exc
            break
        except Exception as exc:  # noqa: BLE001
            last = exc
            if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                break
            time.sleep(1.5 * (attempt + 1))
    command = ["curl", "-sS", "-L", "--max-time", str(timeout), "-A", USER_AGENT]
    if accept:
        command += ["-H", f"Accept: {accept}"]
    result = subprocess.run(command + [url], capture_output=True)
    if result.returncode == 0 and result.stdout:
        return result.stdout
    raise RuntimeError(f"{url}: urllib={last}; curl={result.stderr.decode()[:200]}")


def get_json(url: str, timeout: int = 40) -> dict:
    return json.loads(fetch_bytes(url, timeout=timeout))


def download(url: str, target: Path, timeout: int = 120) -> Path:
    target.write_bytes(fetch_bytes(url, timeout=timeout))
    return target


def record_url(eli: str) -> str:
    return f"{API}/{eli}"


def pdf_url(eli: str) -> str:
    return f"{API}/{eli}/text.pdf"


def act(eli: str) -> dict:
    """The ELI record of one act: title, dates, status, and cross-references."""
    return get_json(record_url(eli))


def search_title(title: str, limit: int = 30) -> list[dict]:
    query = urllib.parse.quote(title)
    return get_json(f"{API}/search?title={query}&limit={limit}").get("items") or []


def parse_reference(text: str) -> str | None:
    """An ELI identifier ("DU/2024/1251") from a Dziennik Ustaw citation, or None when the
    text is not a citation and has to be treated as a title."""
    m = _REFERENCE.search(text.strip())
    if not m:
        return None
    return f"DU/{int(m.group(1))}/{int(m.group(2))}"


def display_address(eli: str) -> str:
    """"DU/2024/1251" as the journal prints it: "Dz.U. 2024 poz. 1251"."""
    publisher, year, position = eli.split("/")
    prefix = {"DU": "Dz.U.", "MP": "M.P."}.get(publisher, publisher)
    return f"{prefix} {year} poz. {position}"


def position_key(eli: str) -> tuple[int, int]:
    """Sort key so the newest consolidated text of a statute wins."""
    _, year, position = eli.split("/")
    return int(year), int(position)
