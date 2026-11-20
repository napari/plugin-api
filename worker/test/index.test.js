// Unit tests for the Worker, run with `node --test` (no Cloudflare needed).
// A fake ASSETS binding serves a handful of files from memory.

import assert from "node:assert/strict";
import { test } from "node:test";

import worker, { normalizeName } from "../src/index.js";

const FILES = {
  "/api/conda-map": { "napari-foo": "conda-forge/napari-foo" },
  "/api/manifest/napari-foo": { name: "napari-foo" },
  "/api/pypi/napari-foo": ["1.0"],
  "/api/shields/napari-foo": { message: "napari-foo", color: "#0074B8" },
  "/api/shields/_unavailable": { message: "unavailable", color: "#82001A" },
};

const env = {
  ASSETS: {
    async fetch(url) {
      const body = FILES[new URL(url).pathname];
      return body === undefined
        ? new Response("not found", { status: 404 })
        : Response.json(body);
    },
  },
};

function get(url) {
  return worker.fetch(new Request(url), env);
}

test("normalizeName", () => {
  assert.equal(normalizeName("Napari_Foo"), "napari-foo");
  assert.equal(normalizeName("napari..foo"), "napari-foo");
});

test("/api/conda serves the conda map with deprecation headers", async () => {
  const response = await get("https://api.napari.org/api/conda");
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), FILES["/api/conda-map"]);
  assert.equal(response.headers.get("Deprecation"), "true");
});

test("non-normalized slugs resolve", async () => {
  const response = await get("https://api.napari.org/api/manifest/Napari_Foo");
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { name: "napari-foo" });
  assert.match(response.headers.get("Content-Type"), /application\/json/);
});

test("unknown plugin is a JSON 404", async () => {
  const response = await get("https://api.napari.org/api/pypi/not-a-plugin");
  assert.equal(response.status, 404);
  assert.match((await response.json()).error, /not-a-plugin/);
});

test("shield message echoes the requested name", async () => {
  const response = await get("https://api.napari.org/api/shields/Napari_Foo");
  assert.equal(response.status, 200);
  const badge = await response.json();
  assert.equal(badge.message, "Napari_Foo");
  assert.equal(badge.color, "#0074B8");
});

test("unknown shield is the unavailable badge, not an error", async () => {
  const response = await get("https://api.napari.org/api/shields/not-a-plugin");
  assert.equal(response.status, 200);
  assert.equal((await response.json()).message, "unavailable");
});

test("api.napari-hub.org/<path> means /api/<path>", async () => {
  const response = await get("https://api.napari-hub.org/shields/napari-foo");
  assert.equal(response.status, 200);
  assert.equal((await response.json()).message, "napari-foo");
});

test("api.napari-hub.org also normalizes", async () => {
  const response = await get("https://api.napari-hub.org/manifest/Napari_Foo");
  assert.equal(response.status, 200);
});

test("only GET and HEAD", async () => {
  const response = await worker.fetch(
    new Request("https://api.napari.org/api/plugins", { method: "POST" }),
    env,
  );
  assert.equal(response.status, 405);
});
