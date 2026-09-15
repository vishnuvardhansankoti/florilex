# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Florilex is a microfrontend host for independent tutorial series (AIML, Go, ...), built as fully static sites and served together from a single Firebase Hosting site, free tier throughout. It's a pnpm workspace monorepo:

```
florilex/
  apps/
    aiml/     Astro site, base "/aiml", its own content collection + deploy
    go/       Astro site, base "/go", same shape, totally separate content
  packages/
    tutorial-kit/   shared components (Callout, Formula, DiagramFigure,
                     WorkTask, Solution, Nav) + the CSS design-token system
  hub/              static landing page ("/") linking to each series
  scripts/          deploy-firebase.sh — build + assemble + firebase deploy
```

Each app under `apps/*` builds to fully static HTML/CSS/JS (`astro build`, `output: "static"`). Because each is built with `base` set to its own mount path (`/aiml`, `/go` in `astro.config.mjs`), every internal link and asset URL it generates is already prefixed with that path. `scripts/deploy-firebase.sh` assembles all of them into one `site/` directory before deploying:

```
site/index.html   <- hub/index.html          (served at /)
site/aiml/...     <- apps/aiml/dist          (served at /aiml/...)
site/go/...       <- apps/go/dist            (served at /go/...)
```

Since `base` already makes every generated link/asset path-correct, no runtime rewriting or proxying is needed — the whole thing is one static Firebase Hosting deployment. The shared nav bar (linking between series) is a `Nav.astro` component from `@florilex/tutorial-kit`, rendered at build time into each app's layout/index pages — not injected at request time.

## Commands

There is no test suite, linter, or formatter configured in this repo (no root tsconfig, no ESLint/Prettier config). TypeScript type-checking happens implicitly through `astro build` / `astro dev`.

```bash
pnpm install

# Local dev (each on its own Astro dev server)
pnpm dev:aiml       # http://localhost:4321/aiml/...
pnpm dev:go         # http://localhost:4321/go/...  (different port if run together)

# Build
pnpm build:aiml
pnpm build:go
pnpm build           # builds all apps/* in the workspace

# Deploy (free tier — Firebase Hosting Spark plan)
pnpm deploy          # scripts/deploy-firebase.sh: build, assemble site/, firebase deploy
```

Deploying requires a Firebase project (Spark/free plan is sufficient — this is a static site, no Cloud Functions involved) with Hosting enabled. Set the project id in `.firebaserc` (`projects.default`), and update the `site` URL in both apps' `astro.config.mjs` to the real Firebase Hosting URL (`https://<project-id>.web.app`) once created. `scripts/deploy-firebase.sh` also honors a `FIREBASE_PROJECT_ID` env var if you want to override the `.firebaserc` default (used by CI). Firebase CLI auth: `firebase login` locally, or a service account JSON via `GOOGLE_APPLICATION_CREDENTIALS` in CI (see `.github/workflows/deploy-firebase.yml`).

## Content architecture (apps/aiml, apps/go)

Each series app is an Astro content-collection site:

- `src/content/config.ts` — defines the `lessons` collection schema (Zod): `title`, `subtitle?`, `phase`, `phaseTitle`, `order`, `lessonNumber`, `hook?`, `hookCredit?`, `sourceUrl?`.
- `src/content/lessons/phases/<NN-phase-name>/<NN-lesson-name>.mdx` — one MDX file per lesson, frontmatter matching the schema above, body built from `@florilex/tutorial-kit` components.
- `src/pages/phases/[...slug].astro` — the single dynamic route; `getStaticPaths()` maps every entry in the `lessons` collection to a static page at build time.
- `src/pages/index.astro` — series landing page; groups lessons by `phase` for a table of contents.
- `src/layouts/LessonLayout.astro` — per-lesson chrome (shared cross-series `Nav`, title, phase/lesson eyebrow, optional "hook" pull-quote, footer attribution via `sourceUrl`). Imports `@florilex/tutorial-kit/tokens.css` and the app's own `src/styles/theme.css` (per-series accent override).
- `src/styles/theme.css` — per-app visual identity layered on top of the shared token system.

`@florilex/tutorial-kit` (packages/tutorial-kit) is the shared dependency both apps consume via `workspace:*`:

- `src/tokens.css` — the shared CSS design-token system both apps' `theme.css` build on.
- `src/components/*.astro` — `Callout`, `Formula`, `DiagramFigure`, `WorkTask`, `Solution` (consumed by MDX lesson content as `@florilex/tutorial-kit/components/<Name>.astro`), and `Nav` (the cross-series nav bar, rendered directly into each app's layout/index pages with an `active` prop).
- `src/stripTags.ts` — strips inline HTML from frontmatter titles (which may carry markup like `<em>` for on-page accenting) for contexts that need plain text (`<title>`, nav links, list labels).

Frontmatter fields like `title` and `subtitle` intentionally carry raw inline HTML and are rendered with `set:html` in layouts — always run them through `stripTags` first for any plain-text context.

## Adding a new tutorial series

1. Copy `apps/go` to `apps/<series>`, change `base` in its `astro.config.mjs`.
2. Give it its own `theme.css` accent override if it wants distinct branding.
3. Add a link to it in `hub/index.html`, and a link/id to `Nav.astro` in `packages/tutorial-kit/src/components/Nav.astro`.
4. Add `site/aiml/...` -> `site/<series>/...` copy step to `scripts/deploy-firebase.sh`.

No existing series is touched by any of this — each app's build and content are fully independent; they're only combined at the final "assemble `site/`" deploy step.
