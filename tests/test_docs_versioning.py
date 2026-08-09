"""Version badges must read from the manifest, not be typed in.

A hardcoded badge is correct on the day it is written and wrong from the next release
onwards. Nothing catches it: the docs build succeeds, the tests pass, the page renders —
it just quietly advertises the wrong version to everyone who visits.

The documentation site badge sat at 0.9.8 while the integration shipped 1.5.0, which is
five minor versions of drift with no signal at any point.

shields.io can read `version` straight out of `manifest.json`, so the badge is always
right and there is nothing to remember at release time. This test stops a static one
being reintroduced.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
MANIFEST = REPO / "custom_components" / "growatt_modbus" / "manifest.json"

# Files that carry version badges. Release notes are excluded: they are a historical
# record, so version numbers in them are supposed to stay fixed.
BADGE_FILES = [
    REPO / "README.md",
    REPO / "docs" / "index.md",
]

STATIC_BADGE = re.compile(r"img\.shields\.io/badge/Version-\d")


@pytest.mark.parametrize("path", BADGE_FILES, ids=lambda p: p.name)
def test_version_badge_is_not_hardcoded(path):
    assert path.exists(), f"{path} is missing"
    hits = STATIC_BADGE.findall(path.read_text(encoding="utf-8"))
    assert not hits, (
        f"{path.name} has a hardcoded version badge. Use the dynamic shields.io badge "
        f"that reads manifest.json instead, so it cannot go stale."
    )


@pytest.mark.parametrize("path", BADGE_FILES, ids=lambda p: p.name)
def test_version_badge_tracks_the_latest_release(path):
    """It reads the latest GitHub release, not the manifest.

    Those differ during a pre-release: the manifest is bumped when the pre-release is cut,
    but the badge should keep showing the newest *stable* version, because that is what a
    visitor can install. shields.io skips pre-releases by default, which is exactly the
    behaviour the old hand-maintained badge was imitating.
    """
    text = path.read_text(encoding="utf-8")
    assert "shields.io/github/v/release/" in text, (
        f"{path.name} has no release-tracking version badge"
    )


def test_manifest_version_is_readable():
    """The badge is only as good as the field it points at."""
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), (
        f"manifest version {version!r} is not plain semver; the badge renders it verbatim"
    )
