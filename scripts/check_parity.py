#!/usr/bin/env python3
"""Check that a candidate deployment answers the v1 API like the current one.

Fetches the same routes from two base URLs and compares status codes and
JSON bodies. Run it before switching DNS, e.g. against a local Worker:

    python scripts/check_parity.py --candidate http://127.0.0.1:8787

Routes checked: every fixed route, and the per-plugin routes (manifest,
pypi, conda, shields) for a sample of plugins, both by their normalized
name and in a non-normalized spelling.

Two differences are expected and reported as such, not as failures:

- An unknown plugin is a 404 on the candidate; the Next.js routes returned 500.
- A slug that differs from the file name (e.g. /api/pypi/Napari_Foo) is a
  500 on the old routes for pypi and conda, and resolves on the candidate.

Uses only the standard library.
"""

import argparse
import json
import random
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

USER_AGENT = "npe2api-parity-check"

FIXED_ROUTES = [
    "/api/plugins",
    "/api/extended_summary",
    "/api/conda",
    "/api/conda-map",
    "/api/readers",
    "/index.json",
    "/extended_summary.json",
    "/conda.json",
    "/readers.json",
    "/classifiers.json",
    "/errors.json",
]

UNKNOWN = "not-a-real-plugin-xyz"


def fetch(url: str) -> tuple[int, object]:
    """Return (status, parsed JSON or raw text) for a GET request."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, body = error.code, error.read()
    try:
        return status, json.loads(body)
    except ValueError:
        return status, body.decode(errors="replace")[:200]


def variant(name: str) -> str:
    """A non-normalized spelling of a plugin name: Title_Case with underscores."""
    return name.replace("-", "_").title()


def routes_for(names: list[str], conda_names: set[str]) -> list[str]:
    routes = list(FIXED_ROUTES)
    for name in names:
        routes += [f"/api/manifest/{name}", f"/api/pypi/{name}"]
        routes += [f"/api/shields/{name}", f"/manifest/{name}.json"]
        routes += [f"/api/manifest/{variant(name)}", f"/api/shields/{variant(name)}"]
        if name in conda_names:
            routes += [f"/api/conda/{name}", f"/conda/{name}.json"]
    for kind in ("manifest", "pypi", "conda", "shields"):
        routes.append(f"/api/{kind}/{UNKNOWN}")
    return routes


def compare(route: str, base: str, candidate: str) -> tuple[str, str]:
    """Return (verdict, detail). Verdict is ok, expected or FAIL."""
    old_status, old_body = fetch(base + route)
    new_status, new_body = fetch(candidate + route)
    if old_status == new_status and old_body == new_body:
        return "ok", ""
    if old_status == 500 and new_status in (200, 404):
        return "expected", f"old route errored with 500; new answers {new_status}"
    if old_status != new_status:
        return "FAIL", f"status {old_status} -> {new_status}"
    return "FAIL", "body differs"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="https://api.napari.org")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--sample", type=int, default=40, help="plugins to check")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    _, index = fetch(args.base + "/api/plugins")
    _, conda_map = fetch(args.base + "/api/conda-map")
    names = sorted(index)
    random.Random(args.seed).shuffle(names)
    sample = sorted(names[: args.sample])
    routes = routes_for(sample, {k for k, v in conda_map.items() if v})

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(lambda r: (r, *compare(r, args.base, args.candidate)), routes)
        )

    counts = {"ok": 0, "expected": 0, "FAIL": 0}
    for route, verdict, detail in results:
        counts[verdict] += 1
        if verdict != "ok":
            print(f"{verdict:8} {route}  {detail}")
    print(
        f"\n{len(results)} routes: {counts['ok']} identical, "
        f"{counts['expected']} expected differences, {counts['FAIL']} failures"
    )
    sys.exit(1 if counts["FAIL"] else 0)


if __name__ == "__main__":
    main()
