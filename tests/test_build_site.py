"""Tests for scripts/build_site.py, using a tiny fake public/ folder."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "build_site.py"
spec = importlib.util.spec_from_file_location("build_site", SCRIPT)
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)


@pytest.fixture
def site(tmp_path):
    public = tmp_path / "public"
    files = {
        "index.json": {"napari-foo": "1.0"},
        "extended_summary.json": [{"name": "napari-foo"}],
        "conda.json": {"napari-foo": "conda-forge/napari-foo"},
        "readers.json": {},
        "classifiers.json": {},
        "errors.json": {},
        "manifest/napari-foo.json": {"name": "napari-foo"},
        "pypi/napari-foo.json": ["1.0"],
        "conda/napari-foo.json": {"name": "napari-foo"},
        "github/Napari_Foo.json": {},
    }
    for rel, data in files.items():
        path = public / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    out = tmp_path / "site"
    build_site.build_site(public, out)
    return out


@pytest.mark.parametrize(
    "path",
    [
        # public/ is served at the root, as Next.js did
        "index.json",
        "extended_summary.json",
        "conda/napari-foo.json",
        "github/Napari_Foo.json",
        # the /api routes
        "api/plugins",
        "api/extended_summary",
        "api/conda-map",
        "api/readers",
        "api/manifest/napari-foo",
        "api/pypi/napari-foo",
        "api/conda/napari-foo",
        "api/shields/napari-foo",
        "api/shields/_unavailable",
        "_headers",
        "index.html",
    ],
)
def test_route_is_a_file(site, path):
    assert (site / path).is_file()


def test_api_aliases_match_public(site):
    assert (site / "api/plugins").read_text() == (site / "index.json").read_text()


def test_shield_for_known_plugin(site):
    badge = json.loads((site / "api/shields/napari-foo").read_text())
    assert badge["message"] == "napari-foo"
    assert badge["color"] == "#0074B8"
    assert badge["logoSvg"].startswith("<svg")


def test_unknown_shield():
    assert build_site.shield(None)["message"] == "unavailable"


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Napari_Foo", "napari-foo"), ("napari..foo", "napari-foo"), ("a-b", "a-b")],
)
def test_normalize_name(name, expected):
    assert build_site.normalize_name(name) == expected
