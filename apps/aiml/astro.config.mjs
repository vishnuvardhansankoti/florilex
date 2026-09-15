import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

// This app is always served under /aiml on the Firebase Hosting site, so
// every internal link and asset path Astro generates must already carry
// that prefix — set once here, nowhere else to worry about it.
export default defineConfig({
  // Needed for rss.xml to emit absolute item links. Update to the real
  // Firebase Hosting URL once the project exists (see README's
  // "Deploying" section) — the RSS feed is the only thing that reads
  // this, since `base` already handles every in-app link/asset.
  site: "https://florilex.web.app",
  base: "/aiml",
  output: "static",
  integrations: [mdx()],
});
