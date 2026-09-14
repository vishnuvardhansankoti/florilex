import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

// This app is always mounted under /aiml by the container Worker, so every
// internal link and asset path Astro generates must already carry that
// prefix — set once here, nowhere else to worry about it.
export default defineConfig({
  // Needed for rss.xml to emit absolute item links. Update to the real
  // florilex-container.<subdomain>.workers.dev URL once deployed (see
  // README's "Deploying" step 3) — the RSS feed is the only thing that
  // reads this, since `base` already handles every in-app link/asset.
  site: "https://florilex-container.workers.dev",
  base: "/aiml",
  output: "static",
  integrations: [mdx()],
});
