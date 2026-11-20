#!/usr/bin/env bash
# Build plugin-api and plugin-api-data from napari/npe2api's history.
#
#   bash tools/rewrite-history.sh <out-dir> [npe2api-commit]
#
# napari/npe2api kept its code and its generated API data (public/) in one
# history: a ~40 MB data commit every two hours. This splits that history in
# two, with git-filter-repo (https://github.com/newren/git-filter-repo):
#
# - <out-dir>/plugin-api: every commit without public/. Commits that only
#   changed data become empty and are dropped.
# - <out-dir>/plugin-api-data: only public/, moved to the root. Commits that
#   didn't touch it are dropped.
#
# In both, bare "#123" in commit messages becomes "napari/npe2api#123", so the
# references keep pointing at npe2api's issues and PRs. Authors, dates and the
# rest of each message are unchanged.
#
# The result is deterministic: the same npe2api commit and git-filter-repo
# version give the same commit IDs. So running this again later, on a newer
# npe2api commit, reproduces every earlier commit and adds the new ones after
# them; pushing that result is a fast-forward. That is how plugin-api-data
# keeps up with npe2api until plugin-api's own update job takes over.
set -euo pipefail

out=${1:?usage: rewrite-history.sh <out-dir> [npe2api-commit]}
ref=${2:-}
mkdir -p "$out"
out=$(cd "$out" && pwd)

git clone --single-branch --branch main --no-tags https://github.com/napari/npe2api "$out/npe2api-source"
if [ -n "$ref" ]; then
  git -C "$out/npe2api-source" reset --hard "$ref"
fi
source_commit=$(git -C "$out/npe2api-source" rev-parse HEAD)
echo "source: napari/npe2api main $source_commit, $(git -C "$out/npe2api-source" rev-list --count HEAD) commits"

messages="$out/messages.txt"
printf '%s\n' 'regex:(?<![\w/&])#(\d+)==>napari/npe2api#\1' > "$messages"

split() {  # split <name> <filter-repo options...>
  local name=$1
  shift
  git clone --quiet --no-local "$out/npe2api-source" "$out/$name"
  (cd "$out/$name" && uvx git-filter-repo --force --quiet "$@" --replace-message "$messages")
  echo "$name: $(git -C "$out/$name" rev-list --count HEAD) commits, tip $(git -C "$out/$name" rev-parse HEAD)"
}

split plugin-api --invert-paths --path public/
split plugin-api-data --subdirectory-filter public/

rm -rf "$messages" "$out/npe2api-source"
