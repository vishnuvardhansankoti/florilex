# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Florilex is a microfrontend container for independent tutorial series (AIML, Go, ...), composed at the edge by a single Cloudflare Worker, free tier throughout. It's a pnpm workspace monorepo:

```
florilex/
  apps/
    aiml/     Astro site, base "/aiml", its own content collection + deploy
    go/       Astro site, base "/go", same shape, totally separate content
  packages/
    tutorial-kit/   shared components (Callout, Formula, DiagramFigure,
                     WorkTask, Solution) + the CSS design-token system
  container/        the Cloudflare Worker that IS the container app
```

Each app under `apps/*` builds to fully static HTML/CSS/JS and deploys as its **own** Cloudflare Pages project, getting a free `*.pages.dev` URL — no custom domain, no shared build, no shared blast radius between series.

The `container` Worker is the single public entry point. On every request it looks at the first path segment (`/aiml/...` or `/go/...`), proxies the request to that series' Pages origin, and — for HTML responses only — injects one shared nav bar via `HTMLRewriter` so the independently deployed sites feel like one app (`container/src/index.ts`, `nav.ts`). Non-HTML responses (JS, CSS, images) pass straight through untouched. `/` with no series prefix serves a small hub page (`container/src/hub.ts`) linking to each series.

Because each Astro app is built with `base` set to its own mount path (`/aiml`, `/go` in `astro.config.mjs`), every internal link and asset URL it generates is already correctly prefixed — the Worker never rewrites HTML content or asset paths, only prepends the nav.

## Commands

There is no test suite, linter, or formatter configured in this repo (no root tsconfig, no ESLint/Prettier config). TypeScript type-checking happens implicitly through `astro build` / `astro dev` and `wrangler`.

```bash
pnpm install

# Local dev (each on its own Astro dev server)
pnpm dev:aiml       # http://localhost:4321/aiml/...
pnpm dev:go         # http://localhost:4321/go/...  (different port if run together)
pnpm dev:container  # wrangler dev — proxies to whatever AIML_ORIGIN/GO_ORIGIN point at

# Build
pnpm build:aiml
pnpm build:go
pnpm build           # builds all apps/* in the workspace

# Deploy (all free tier)
pnpm deploy:aiml       # wrangler pages deploy dist --project-name=aiml-tutorials
pnpm deploy:go         # wrangler pages deploy dist --project-name=go-tutorials
pnpm deploy:container  # wrangler deploy
```

For the container Worker to do anything useful locally, point `AIML_ORIGIN` / `GO_ORIGIN` in `container/wrangler.toml` at your local `astro dev` ports (or at already-deployed Pages URLs) before running `pnpm dev:container`.

Deploying an app requires a Cloudflare Pages project already connected to this repo with the matching root directory (`apps/aiml` or `apps/go`), build command `pnpm build`, output `dist`. After creating those, update `container/wrangler.toml`'s `AIML_ORIGIN`/`GO_ORIGIN` to the real `.pages.dev` URLs before deploying the container.

## Content architecture (apps/aiml, apps/go)

Each series app is an Astro content-collection site:

- `src/content/config.ts` — defines the `lessons` collection schema (Zod): `title`, `subtitle?`, `phase`, `phaseTitle`, `order`, `lessonNumber`, `hook?`, `hookCredit?`, `sourceUrl?`.
- `src/content/lessons/phases/<NN-phase-name>/<NN-lesson-name>.mdx` — one MDX file per lesson, frontmatter matching the schema above, body built from `@florilex/tutorial-kit` components.
- `src/pages/phases/[...slug].astro` — the single dynamic route; `getStaticPaths()` maps every entry in the `lessons` collection to a static page at build time.
- `src/pages/index.astro` — series landing page; groups lessons by `phase` for a table of contents.
- `src/layouts/LessonLayout.astro` — per-lesson chrome (title, phase/lesson eyebrow, optional "hook" pull-quote, footer attribution via `sourceUrl`). Imports `@florilex/tutorial-kit/tokens.css` and the app's own `src/styles/theme.css` (per-series accent override).
- `src/styles/theme.css` — per-app visual identity layered on top of the shared token system.

`@florilex/tutorial-kit` (packages/tutorial-kit) is the shared dependency both apps consume via `workspace:*`:

- `src/tokens.css` — the shared CSS design-token system both apps' `theme.css` build on.
- `src/components/*.astro` — `Callout`, `Formula`, `DiagramFigure`, `WorkTask`, `Solution`, consumed by MDX lesson content as `@florilex/tutorial-kit/components/<Name>.astro`.
- `src/stripTags.ts` — strips inline HTML from frontmatter titles (which may carry markup like `<em>` for on-page accenting) for contexts that need plain text (`<title>`, nav links, list labels).

Frontmatter fields like `title` and `subtitle` intentionally carry raw inline HTML and are rendered with `set:html` in layouts — always run them through `stripTags` first for any plain-text context.

## Adding a new tutorial series

1. Copy `apps/go` to `apps/<series>`, change `base` in its `astro.config.mjs`.
2. Give it its own `theme.css` accent override if it wants distinct branding.
3. Add a new Cloudflare Pages project pointed at `apps/<series>`.
4. Add the series to `SERIES`/`ORIGIN_FOR` in `container/src/index.ts`, its origin var in `container/wrangler.toml`, and a link in `container/src/hub.ts`.

No existing series is touched by any of this — each app's build, content, and deploy are fully independent.
