import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

// This app is always served under /system-design on the Firebase Hosting
// site — see apps/aiml/astro.config.mjs for why `base` is the only thing
// that needs to change per series, and for what `site` below is for.
export default defineConfig({
  site: "https://florilex.web.app",
  base: "/system-design",
  output: "static",
  integrations: [mdx()],
});
