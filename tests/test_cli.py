"""One real act end to end, offline: Dz.U. 2024 poz. 1796 (consumer rights act) and its
single amendment Dz.U. 2025 poz. 1172, whose art. 7 and art. 10 are deferred by an exception
to three months after promulgation while the act as a whole enters into force on 1 March
2026. One fixture, three states depending on the date asked about."""
import json

import pytest

from stillaw import cli, eli


def run(capsys, *argv):
    code = cli.main(list(argv))
    return code, capsys.readouterr().out


def test_json_superseded(offline, capsys):
    code, out = run(capsys, "check", "Dz.U. 2024 poz. 1796", "--as-of", "2026-08-28", "--json")
    assert code == 0
    result = json.loads(out)
    assert result["eli"] == "DU/2024/1796"
    assert result["statute"] == "o prawach konsumenta"
    assert result["status"] == "superseded"
    assert result["since"] == "2025-11-27"
    assert result["superseded_by"]["eli"] == "DU/2025/1172"
    amendment = result["amendments"][0]
    assert amendment["in_force"] == "2025-11-27"
    assert amendment["eli_entry_into_force"] == "2026-03-01"
    assert "exception" in amendment["how"]
    assert amendment["basis"].startswith("wchodzi w życie z dniem 1 marca 2026 r., z wyjątkiem")
    assert "disagreement" in amendment
    assert len(result["sha256"]) == 64


def test_vacatio_legis_before_the_date(offline, capsys):
    code, out = run(capsys, "check", "DU/2024/1796", "--as-of", "2025-11-01", "--json")
    result = json.loads(out)
    assert (result["status"], result["next_change"]) == ("vacatio_legis", "2025-11-27")


def test_current_before_promulgation(offline, capsys):
    """Asked about a day before the amendment was promulgated the answer is still
    vacatio legis: the check is about the text as it stands today, and the amendment
    exists. Only its in-force date moves relative to as-of."""
    code, out = run(capsys, "check", "DU/2024/1796", "--as-of", "2025-01-01", "--json")
    assert json.loads(out)["status"] == "vacatio_legis"


def test_human_output(offline, capsys):
    code, out = run(capsys, "check", "Dz. U. z 2024 r. poz. 1796", "--as-of", "2026-08-28")
    assert code == 0
    assert "SUPERSEDED since 2025-11-27" in out
    assert "sha256:" in out


def test_sha256_is_stable(offline, capsys):
    _, first = run(capsys, "check", "DU/2024/1796", "--as-of", "2026-08-28", "--json")
    _, second = run(capsys, "check", "DU/2024/1796", "--as-of", "2026-08-28", "--json")
    assert json.loads(first)["sha256"] == json.loads(second)["sha256"]


@pytest.mark.parametrize("text, expected", [
    ("Dz.U. 2024 poz. 1251", "DU/2024/1251"),
    ("Dz. U. z 2024 r. poz. 1251", "DU/2024/1251"),
    ("Dz.U.2024.1251", "DU/2024/1251"),
    ("DU/2024/1251", "DU/2024/1251"),
    ("du/2024/1251", "DU/2024/1251"),
    ("Prawo o ruchu drogowym", None),
])
def test_parse_reference(text, expected):
    assert eli.parse_reference(text) == expected


def test_bad_date_is_rejected(capsys):
    with pytest.raises(SystemExit):
        cli.main(["check", "DU/2024/1796", "--as-of", "28.08.2026"])
