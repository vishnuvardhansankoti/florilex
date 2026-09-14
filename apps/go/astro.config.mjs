import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

// This app is always mounted under /go by the container Worker — see
// apps/aiml/astro.config.mjs for why `base` is the only thing that needs
// to change per series, and for what `site` below is for.
export default defineConfig({
  site: "https://florilex-container.workers.dev",
  base: "/go",
  output: "static",
  integrations: [mdx()],
});
