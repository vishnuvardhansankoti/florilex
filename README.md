# florilex

A microfrontend host for independent tutorial series (AIML, Go, ...),
built as fully static sites and served together from one Firebase
Hosting site — free tier throughout.

## How it fits together

```
florilex/
  apps/
    aiml/     Astro site, base "/aiml", its own content collection
    go/       Astro site, base "/go", same shape, totally separate content
    dsa/      Astro site, base "/dsa", same shape, totally separate content
  packages/
    tutorial-kit/   shared components (Callout, Formula, DiagramFigure,
                     WorkTask, Solution, Nav) + the CSS design-token system
  hub/              static landing page ("/") linking to each series
  scripts/
    deploy/         deploy-firebase.sh — build + assemble + firebase deploy
    lesson-pipeline/  URL -> LLM -> new lesson .mdx (see scripts/lesson-pipeline/README.md)
```

Each app under `apps/*` builds to fully static HTML/CSS/JS. Because each
is built with `base` set to its own mount path (`/aiml`, `/go`), every
internal link and asset URL it generates is already correctly prefixed.

`scripts/deploy/deploy-firebase.sh` builds both apps and assembles them into one
`site/` directory alongside the static hub page, then deploys that single
directory to Firebase Hosting:

```
site/index.html   <- hub/index.html    (served at /)
site/aiml/...     <- apps/aiml/dist    (served at /aiml/...)
site/go/...       <- apps/go/dist      (served at /go/...)
```

No server-side proxying or rewriting is needed — it's one static
deployment. The shared nav bar linking between series is a `Nav.astro`
component from `@florilex/tutorial-kit`, rendered at build time into each
app's pages.

## Local development

```bash
pnpm install

pnpm dev:aiml       # http://localhost:4321/aiml/...
pnpm dev:go         # http://localhost:4321/go/...  (different port if run together)
```

## Deploying (free tier — Firebase Hosting Spark plan)

1. **Create a Firebase project** (console.firebase.google.com) with
   Hosting enabled. No Cloud Functions needed — this is a static site.

2. **Set the project id**:
   - `.firebaserc` → `projects.default`
   - each app's `astro.config.mjs` (`apps/aiml`, `apps/go`, `apps/dsa`) →
     `site` (used for absolute RSS links), set to `https://<project-id>.web.app`

3. **Log in to Firebase CLI** (first time only): `npx firebase-tools login`

4. **Deploy**:
   ```bash
   pnpm deploy
   ```
   This builds every app, assembles `site/`, and runs
   `firebase deploy --only hosting`. You get one free
   `<project-id>.web.app` URL — `/aiml/...`, `/go/...`, and `/dsa/...`
   all work from it.

### CI (GitHub Actions)

`.github/workflows/deploy-firebase.yml` runs the same script on every
push to `main` that touches `apps/**`, `packages/**`, or `hub/**`. It
needs two repo secrets:
- `FIREBASE_SERVICE_ACCOUNT` — a Firebase service account JSON key with
  Hosting deploy permission
- `FIREBASE_PROJECT_ID` — your Firebase project id

## Adding a new series later

1. Copy `apps/go` to `apps/<series>`, change `base` in its `astro.config.mjs`.
2. Give it its own `theme.css` accent override if it wants distinct branding.
3. Add a link to it in `hub/index.html` and in
   `packages/tutorial-kit/src/components/Nav.astro`.
4. Add a copy step for it in `scripts/deploy/deploy-firebase.sh`.

No existing series is touched by any of this.
