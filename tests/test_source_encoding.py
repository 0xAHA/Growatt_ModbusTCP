"""Nothing we ship may carry a byte-order mark, a stray control character, or mojibake.

CLAUDE.md rule 7 has said this for a long time, and it has been enforced by remembering to
check. That has failed repeatedly:

- `Set-Content -Encoding utf8` writes a BOM in PowerShell 5.1, which stopped `manifest.json`
  parsing and would have prevented the integration loading at all.
- Em-dashes have been mangled into the Windows-1252 reading of their UTF-8 bytes in three
  separate files. `docs/` is published to GitHub Pages, so that is not a cosmetic problem
  in an editor - it is visible mojibake to every reader of the documentation site.
- A regex written through a shell heredoc had its two word boundaries turned into literal
  backspace characters, so `re.search(r"...")` was matching a byte that never occurs and
  the assertion around it passed vacuously for the whole life of the test.

The last one is why this file exists rather than another line in the guide. The damage was
invisible in every view anyone would normally use: the test passed, the diff looked correct,
and the source rendered correctly in an editor. Only `od -c` showed it. A rule that can only
be enforced by inspecting bytes by hand is not enforced.

None of these are about which characters are allowed. Non-ASCII in source is fine - the
encoding is the problem, never the character.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent

SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml"}

SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", "site", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "Protocols",
}

# Tab, newline and carriage return are the only control characters with any business in a
# text file. Everything below 0x20 outside those is a mistake that survived an editor.
ALLOWED_CONTROL = {0x09, 0x0A, 0x0D}

# The signatures of UTF-8 bytes read back as Windows-1252. An em-dash mangled this way
# becomes "a-with-circumflex, euro, quote"; the first two bytes below open almost every
# such sequence, so they catch curly quotes, degree signs and accented names too.
MOJIBAKE = (
    b"\xc3\xa2\xe2\x82\xac",  # "a~EUR" - the head of a mangled em-dash or curly quote
    b"\xc3\x82\xc2",          # "A^" followed by a C1 byte - mangled non-breaking space
)


def _tracked_files() -> list[Path]:
    found = []
    for path in REPO.rglob("*"):
        if path.suffix not in SUFFIXES or not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(REPO).parts):
            continue
        found.append(path)
    return sorted(found)


def _ids(paths: list[Path]) -> list[str]:
    return [str(p.relative_to(REPO)).replace("\\", "/") for p in paths]


FILES = _tracked_files()

# Two files quote these byte sequences in order to describe them - this one in MOJIBAKE
# above, and CLAUDE.md rule 7, which lists them inside backticks as what to grep for. Both
# are exempt from the mojibake check only; the BOM and control-character checks still apply
# to them, and nothing else is exempt from anything.
DOCUMENTS_THE_SIGNATURES = {
    Path(__file__).resolve(),
    (REPO / "CLAUDE.md").resolve(),
}


def test_the_sweep_actually_found_the_source_tree():
    """Rule 4: absence of evidence needs the evidence to have been possible. If the walk
    silently matched nothing, every test below would pass by finding no files to check."""
    assert len(FILES) > 100, f"only {len(FILES)} files swept - the walk is not reaching the tree"
    names = set(_ids(FILES))
    assert "custom_components/growatt_modbus/manifest.json" in names
    assert "custom_components/growatt_modbus/const.py" in names
    assert "docs/index.md" in names


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_no_byte_order_mark(path: Path):
    """A BOM breaks JSON parsing outright and renders as a stray glyph in Markdown."""
    assert not path.read_bytes().startswith(b"\xef\xbb\xbf"), (
        "starts with a UTF-8 BOM - most likely written by PowerShell rather than an editor"
    )


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_no_stray_control_characters(path: Path):
    """The backspace case above. These are invisible in an editor and in a diff."""
    raw = path.read_bytes()
    for index, byte in enumerate(raw):
        if byte < 0x20 and byte not in ALLOWED_CONTROL:
            line = raw[:index].count(b"\n") + 1
            pytest.fail(
                f"control byte {byte:#04x} at line {line}. If this came from a shell "
                f"heredoc, the escape was interpreted on the way in - write the file with "
                f"an editing tool instead."
            )


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_is_valid_utf8_and_free_of_mojibake(path: Path):
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as err:
        pytest.fail(f"not valid UTF-8: {err}")

    if path.resolve() in DOCUMENTS_THE_SIGNATURES:
        return
    for signature in MOJIBAKE:
        assert signature not in raw, (
            f"contains {signature!r} - UTF-8 that has been read as Windows-1252 and "
            f"rewritten. Recover the text from git rather than retyping the characters."
        )
