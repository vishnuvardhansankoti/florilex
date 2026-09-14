# florilex

A microfrontend container for independent tutorial series (AIML, Go, ...),
composed at the edge by a single Cloudflare Worker — free tier throughout.

## How it fits together

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

Each app under `apps/*` builds to fully static HTML/CSS/JS and deploys as
its **own** Cloudflare Pages project, getting a free `*.pages.dev` URL —
no custom domain needed, no shared build, no shared blast radius.

The `container` Worker is the single public entry point. On every request
it looks at the first path segment (`/aiml/...` or `/go/...`), proxies the
request to that series' Pages origin, and — for HTML responses only —
injects one shared nav bar via `HTMLRewriter` so the two independently
deployed sites feel like one app. Non-HTML responses (JS, CSS, images)
pass straight through untouched. `/` with no series prefix serves a small
hub page linking to each series.

Because each Astro app is built with `base` set to its own mount path
(`/aiml`, `/go`), every internal link and asset URL it generates is
already correctly prefixed — the Worker never rewrites HTML content or
asset paths, only prepends the nav.

## Local development

```bash
pnpm install

pnpm dev:aiml       # http://localhost:4321/aiml/...
pnpm dev:go         # http://localhost:4321/go/...  (different port if run together)
pnpm dev:container  # wrangler dev — proxies to whatever AIML_ORIGIN/GO_ORIGIN point at
```

For the container to do anything useful locally, point `AIML_ORIGIN` /
`GO_ORIGIN` in `container/wrangler.toml` at your local `astro dev` ports
(or at already-deployed Pages URLs) before running `pnpm dev:container`.

## Deploying (all free tier)

1. **Each app → its own Cloudflare Pages project**, connected to this repo
   with a different "root directory":
   - `apps/aiml`, build command `pnpm build`, output `dist`
   - `apps/go`, build command `pnpm build`, output `dist`

   Cloudflare gives each project a free `<project-name>.pages.dev` URL —
   note these down.

2. **Update `container/wrangler.toml`** — set `AIML_ORIGIN` / `GO_ORIGIN`
   to the real `.pages.dev` URLs from step 1.

3. **Deploy the container Worker**:
   ```bash
   pnpm deploy:container
   ```
   Wrangler will give you a free `florilex-container.<your-subdomain>.workers.dev`
   URL — that's the one URL you share. `/aiml/...` and `/go/...` both work
   from it, composed at the edge.

## Adding a new series later

1. Copy `apps/go` to `apps/<series>`, change `base` in its `astro.config.mjs`.
2. Give it its own `theme.css` accent override if it wants distinct branding.
3. Add a new Cloudflare Pages project pointed at `apps/<series>`.
3. Add the series to `SERIES`/`ORIGIN_FOR` in `container/src/index.ts`,
   its origin var in `wrangler.toml`, and a link in `container/src/hub.ts`.

No existing series is touched by any of this.
