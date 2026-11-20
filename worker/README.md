# npe2api on Cloudflare

The API is a static site (built by `scripts/build_site.py` from the `data`
branch) plus this small Worker, deployed with
[Workers static assets](https://developers.cloudflare.com/workers/static-assets/).
Requests that match a file are served without running any code. Only a miss
runs `src/index.js`; see the comment at its top for the four cases it handles.

## Work on it locally

```bash
git worktree add public data          # once: the generated data
python scripts/build_site.py          # writes site/
cd worker
npm ci
npm test                              # unit tests, no Cloudflare needed
npx wrangler dev                      # http://localhost:8787
python ../scripts/check_parity.py --candidate http://localhost:8787
```

## One-time setup

1. In the napari Cloudflare account, create an API token from the
   "Edit Cloudflare Workers" template.
2. Add two repository secrets on GitHub: `CLOUDFLARE_API_TOKEN` and
   `CLOUDFLARE_ACCOUNT_ID` (the account ID is on the Workers overview page).
3. Run the "Update Plugin Index" workflow by hand. It deploys to
   `npe2api.<account>.workers.dev`.
4. Check parity against the live API:
   `python scripts/check_parity.py --candidate https://npe2api.<account>.workers.dev`

## Switching the hostnames over

1. Uncomment `routes` in `wrangler.jsonc` for `api.napari.org` and
   `api.napari-hub.org` (their DNS zones must be on the Cloudflare account),
   and deploy. Cloudflare creates the DNS records and certificates.
2. Run the parity check against `https://api.napari.org` from outside.
3. Replace the Vercel project with redirects only: see `vercel-redirect/`.
