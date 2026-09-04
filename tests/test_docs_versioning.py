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
    """Parseable semver, optionally with a beta suffix.

    This used to require plain `X.Y.Z`, on the grounds that "the badge renders it
    verbatim". That reason no longer holds: the badge is `shields.io/github/v/release/`,
    which reads the latest GitHub *release* and never looks at the manifest.

    What does still depend on this field is HACS, which compares it to decide whether an
    update is available. `1.10.0-b1` is valid semver - a pre-release sorts below the
    release it precedes, so a beta tester is correctly offered `1.10.0` when it lands.

    Betas carry `-b1`, `-b2` and so on; stable releases drop the suffix. Before that,
    every beta consumed a patch number, so the version climbed several times a week and
    said nothing about whether a release had been tested.
    """
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+(-b\d+)?", version), (
        f"manifest version {version!r} is neither X.Y.Z nor X.Y.Z-bN"
    )


# The installations badge reads $.<domain>.total out of Home Assistant's analytics feed.
# The domain is typed into the badge URL, so it is a second copy of manifest.json's
# `domain` field — and if the two ever diverge the badge does not error, it just renders
# an empty value on the front page of the documentation site.
ANALYTICS_BADGE = re.compile(
    r"analytics\.home-assistant\.io%2Fcustom_integrations\.json&query=%24\.(\w+)\.total"
)


@pytest.mark.parametrize("path", BADGE_FILES, ids=lambda p: p.name)
def test_installations_badge_queries_the_manifest_domain(path):
    match = ANALYTICS_BADGE.search(path.read_text(encoding="utf-8"))
    assert match, f"{path.name} has no installations badge"

    domain = json.loads(MANIFEST.read_text(encoding="utf-8"))["domain"]
    assert match.group(1) == domain, (
        f"{path.name} installations badge queries $.{match.group(1)}.total but the "
        f"manifest domain is {domain!r}. shields.io renders a blank badge rather than "
        f"failing, so this drift is invisible on the rendered page."
    )
