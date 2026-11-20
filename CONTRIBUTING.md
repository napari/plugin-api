# Contributing to plugin-api

Thank you for your interest in contributing to plugin-api! This guide will help you get started with development and contributions.

## Overview

plugin-api is the REST API used by napari to query plugins. It aggregates
metadata about napari plugins registered on PyPI and conda-forge, and serves
it as a static site from Cloudflare.

The repository has two parts:

- **Python scripts** (`scripts/`) that fetch and validate plugin data, and
  build it into a static site.
- **A small Cloudflare Worker** (`worker/`) that answers the few requests a
  static file cannot. See [worker/README.md](worker/README.md).

The generated data lives in its own repository,
[napari/plugin-api-data](https://github.com/napari/plugin-api-data).

## Development setup

### Prerequisites
- Python 3.13+
- Node.js 22+ (only to run the Worker locally)
- Git

### Getting started

1. Fork and clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/plugin-api.git
cd plugin-api
```

2. Install the Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

3. Get the data. The generated JSON lives in
   [napari/plugin-api-data](https://github.com/napari/plugin-api-data). Clone
   it into `public/`, where every script expects it. `--depth 1` fetches only
   the latest snapshot; leave it out for the full history since 2022 (~230 MB):

```bash
git clone --depth 1 https://github.com/napari/plugin-api-data public
```

4. Build and serve the API locally

```bash
python scripts/build_site.py     # writes site/
cd worker
npm ci
npx wrangler dev                 # http://localhost:8787
```

## Development tasks

### Running Tests

Before submitting changes, ensure all tests pass:

```bash
# Validate the data and test the site build
pytest tests/

# Run Python linting and formatting
ruff check .        # Check for linting issues
ruff format .       # Format code

# Test the Worker
cd worker && npm test

# Compare a deployment with the live API
python scripts/check_parity.py --candidate http://localhost:8787
```

### Executing scripts

For testing data collection locally:

```bash
# Find packages by classifier (requires Google Cloud credentials)
python scripts/bigquery.py

# Fetch manifests for plugins
python scripts/fetch_manifests.py

# Re-index and validate all plugin data
python scripts/reindex.py
```

### Making changes

#### API endpoints

Every endpoint is a file written by `scripts/build_site.py`. To add or change
an endpoint, change that script. Only behaviour that cannot be a file (name
normalization, unknown plugins, `/api/conda`, the `api.napari-hub.org` host)
belongs in `worker/src/index.js`.

#### Data processing scripts

Core scripts in `scripts/`:
- `bigquery.py` - Queries BigQuery for napari plugins
- `fetch_manifests.py` - Downloads plugin manifests
- `reindex.py` - Validates and aggregates plugin data
- `build_site.py` - Writes every API path as a static file
- `check_parity.py` - Compares two deployments of the API

## How this repo works

1. [The update action](.github/workflows/update.yml) is triggered by:
    - a cron job every 2 hours
    - a pull request (validation and a preview only)
    - a `workflow_dispatch` triggered manually from the [actions page](https://github.com/napari/plugin-api/actions/workflows/update.yml)
2. When triggered, the update action
    1. checks out napari/plugin-api-data into `public/`
    2. finds plugins with BigQuery and fetches their manifests
    3. runs [`scripts/reindex.py`](scripts/reindex.py), which validates the manifests and builds the indices
    4. validates the result with `tests/test_output.py`
    5. commits the data to napari/plugin-api-data
    6. builds the site with [`scripts/build_site.py`](scripts/build_site.py)
    7. deploys it to Cloudflare (<https://api.napari.org>)

`npe2api.vercel.app`, the hostname older napari releases use, redirects to
`api.napari.org` from [napari/npe2api](https://github.com/napari/npe2api).

### Endpoints

 - <https://api.napari.org/api/plugins>
     - map of {plugin_names -> version}
 - <https://api.napari.org/api/extended_summary>
     - all basic plugin info needed to populate the plugin browser in napari
     - summary endpoint has been removed. Use extended_summary instead.
 - [https://api.napari.org/api/manifest/{plugin-name}](https://api.napari.org/api/manifest/napari-animation)
     - the full manifest for a given plugin
 - <https://api.napari.org/api/conda-map>
     - map of {pypi_name -> conda_channel/package_name}
     - `/api/conda` is the deprecated name, kept for released napari versions
 - [https://api.napari.org/api/pypi/{plugin-name}](https://api.napari.org/api/pypi/napari-animation)
     - PyPI info for a plugin.
 - [https://api.napari.org/api/conda/{plugin-name}](https://api.napari.org/api/conda/napari-animation)
     - conda info for a plugin. *name is pypi_name, not conda-name*
 - [https://api.napari.org/api/shields/{plugin-name}](https://api.napari.org/api/shields/napari-animation)
     - a [shields.io endpoint](https://shields.io/badges/endpoint-badge) badge
 - <https://api.napari.org/errors.json>
     - errors encountered during the last fetch
 - <https://api.napari.org/api/readers>
     - lookup of filename pattern to reader

## Questions and issues

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- For questions, use the issue tracker or ask us on Zulip

## Additional resources

- [napari plugin documentation](https://napari.org/plugins/)
- [npe2 documentation](https://github.com/napari/npe2)

Thank you for contributing to plugin-api!
