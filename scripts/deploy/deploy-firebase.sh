#!/usr/bin/env bash
# Builds the deployed apps and assembles them into ./site, then deploys that
# directory to Firebase Hosting as a single static site:
#   site/index.html          <- hub/index.html (landing page linking to each series)
#   site/aiml/...            <- apps/aiml/dist (already emits /aiml/-prefixed links)
#   site/dsa/...             <- apps/dsa/dist  (already emits /dsa/-prefixed links)
#   site/system-design/...   <- apps/system-design/dist (already emits /system-design/-prefixed links)
#
# apps/go is intentionally excluded here — it's still a draft with no real
# lessons, so it stays in the repo and buildable via `pnpm build:go` /
# `pnpm dev:go`, but isn't deployed or linked from the hub until it's ready.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

pnpm --filter @florilex/aiml --filter @florilex/dsa --filter @florilex/system-design build

rm -rf site
mkdir -p site
cp -r hub/. site/
mkdir -p site/aiml site/dsa site/system-design
cp -r apps/aiml/dist/. site/aiml/
cp -r apps/dsa/dist/. site/dsa/
cp -r apps/system-design/dist/. site/system-design/

if [ -n "${FIREBASE_PROJECT_ID:-}" ]; then
  npx firebase-tools deploy --only hosting --project "$FIREBASE_PROJECT_ID" --non-interactive
else
  npx firebase-tools deploy --only hosting --non-interactive
fi
