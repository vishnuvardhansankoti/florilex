#!/usr/bin/env bash
# Builds every app and assembles them into ./site, then deploys that
# directory to Firebase Hosting as a single static site:
#   site/index.html   <- hub/index.html (landing page linking to each series)
#   site/aiml/...     <- apps/aiml/dist (already emits /aiml/-prefixed links)
#   site/go/...       <- apps/go/dist   (already emits /go/-prefixed links)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

pnpm build

rm -rf site
mkdir -p site
cp -r hub/. site/
mkdir -p site/aiml site/go
cp -r apps/aiml/dist/. site/aiml/
cp -r apps/go/dist/. site/go/

if [ -n "${FIREBASE_PROJECT_ID:-}" ]; then
  npx firebase-tools deploy --only hosting --project "$FIREBASE_PROJECT_ID" --non-interactive
else
  npx firebase-tools deploy --only hosting --non-interactive
fi
