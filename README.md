# plugin-api

[![vercel](https://img.shields.io/github/deployments/napari/npe2api/production?label=vercel&logo=vercel&style=flat-square)](https://api.napari.org)

The REST API used by [napari-hub.org](https://napari-hub.org) to query plugins.

The endpoint for the API is: <https://api.napari.org>

## Endpoints

| Type             | Endpoint                                                             | Note                                             |
|------------------|----------------------------------------------------------------------|--------------------------------------------------|
| Plugin index     | [/api/plugins](https://api.napari.org/api/plugins)                   |                                                  |
| Summary info     | [/api/extended_summary](https://api.napari.org/api/extended_summary) |                                                  |
| PyPI information |                                                                      | For an individual plugin: /api/pypi/{pypi_name}  |
| Conda index      | [/api/conda](https://api.napari.org/api/conda)                       | For an individual plugin: /api/conda/{pypi_name} |
| Fetch errors     | [/errors.json](https://api.napari.org/errors.json)                   |                                                  |
| manifests        | For an individual manifest: /api/manifest/{plugin_name}              |                                                  |

## History

This repository continues [napari/npe2api](https://github.com/napari/npe2api),
which kept its code and its generated API data in one history. That history
was split in two with [git-filter-repo](https://github.com/newren/git-filter-repo)
by [tools/rewrite-history.sh](tools/rewrite-history.sh), from npe2api `main`
at `883af17feb` (2026-11-19):

- this repository: every commit without the generated data (`public/`).
  Commits that only updated data were dropped (62,585 → 80 commits);
- [napari/plugin-api-data](https://github.com/napari/plugin-api-data): the
  data alone, with all 62,515 snapshots since 2022.

In both, `#N` in commit messages was rewritten to `napari/npe2api#N`. Authors,
dates and messages are otherwise unchanged. Running the script on the same
npe2api commit gives the same commit IDs. npe2api stays available, archived.

## Contributing

If you are interested in contributing to this repo, see the [CONTRIBUTING.md](./CONTRIBUTING.md) page.

## Code of conduct

`npe2api` is maintained by the [napari](https://napari.org/) community. The `napari` community has a [Code of Conduct](https://napari.org/dev/community/code_of_conduct.html) that should be honored by everyone who participates in the `napari` community.
