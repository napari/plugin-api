// The npe2api Worker.
//
// Cloudflare serves every file in site/ directly, without running this code
// (see scripts/build_site.py). This Worker only runs when a request matches
// no file. It handles the cases a static file cannot:
//
// 1. /api/conda: the conda map, at a path the api/conda/ folder occupies.
// 2. Slugs that are not normalized (/api/manifest/Napari_Foo): look up the
//    normalized name, as the old Next.js routes did.
// 3. Unknown plugins: a 404 with a JSON body (the old routes returned 500),
//    or the "unavailable" badge for /api/shields.
// 4. api.napari-hub.org/<path>, which has always meant /api/<path>.

const HUB_HOST = "api.napari-hub.org";

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
};

const CONDA_DEPRECATION_HEADERS = {
  Deprecation: "true",
  Link: '</api/conda-map>; rel="alternate"',
  "X-Deprecated-Message":
    "This endpoint is deprecated. Use /api/conda-map instead to avoid " +
    "conflicts with /api/conda/:plugin routes.",
};

const PER_PLUGIN_ROUTE = /^\/api\/(manifest|pypi|conda|shields)\/([^/]+)\/?$/;

/** Normalize a package name the way the API always has (PEP 503). */
export function normalizeName(name) {
  return name.replace(/[-_.]+/g, "-").toLowerCase();
}

export default {
  async fetch(request, env) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }
    const url = new URL(request.url);
    if (url.hostname === HUB_HOST && !url.pathname.startsWith("/api/")) {
      url.pathname = "/api" + url.pathname;
      const asset = await getAsset(env, url);
      if (asset) return asset;
    }
    return route(url, env);
  },
};

async function route(url, env) {
  const path = url.pathname;

  if (path === "/api/conda" || path === "/api/conda/") {
    const map = await getAsset(env, url, "/api/conda-map");
    if (!map) return notFound("The conda map is missing from this deploy");
    return withHeaders(map, CONDA_DEPRECATION_HEADERS);
  }

  const match = PER_PLUGIN_ROUTE.exec(path);
  if (match) {
    const [, kind, rawSlug] = match;
    const slug = decodeURIComponent(rawSlug);
    const found = await getAsset(env, url, `/api/${kind}/${normalizeName(slug)}`);
    if (kind === "shields") {
      return shield(env, url, found, slug);
    }
    if (found) return withHeaders(found, JSON_HEADERS);
    return notFound(`No ${kind} data for plugin '${slug}'`);
  }

  return notFound(`No route for ${path}`);
}

/** Fetch a file from site/, or return null if there is none. */
async function getAsset(env, url, path = url.pathname) {
  const assetUrl = new URL(path, url);
  const response = await env.ASSETS.fetch(assetUrl);
  return response.ok ? response : null;
}

/** A badge whose message is the plugin name exactly as it was requested. */
async function shield(env, url, found, slug) {
  if (!found) {
    const unavailable = await getAsset(env, url, "/api/shields/_unavailable");
    if (!unavailable) return notFound(`No plugin '${slug}'`);
    return withHeaders(unavailable, JSON_HEADERS);
  }
  const badge = await found.json();
  badge.message = slug;
  return Response.json(badge, { headers: JSON_HEADERS });
}

function withHeaders(response, headers) {
  const result = new Response(response.body, response);
  for (const [key, value] of Object.entries(headers)) {
    result.headers.set(key, value);
  }
  return result;
}

function notFound(message) {
  return Response.json({ error: message }, { status: 404, headers: JSON_HEADERS });
}
