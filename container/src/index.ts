import { renderNav, type SeriesId } from "./nav";
import { renderHub } from "./hub";

export interface Env {
  AIML_ORIGIN: string;
  GO_ORIGIN: string;
}

const ORIGIN_FOR: Record<SeriesId, keyof Env> = {
  aiml: "AIML_ORIGIN",
  go: "GO_ORIGIN",
};

function seriesFromPath(pathname: string): SeriesId | null {
  const [, first] = pathname.split("/");
  return first === "aiml" || first === "go" ? first : null;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const series = seriesFromPath(url.pathname);

    if (!series) {
      return renderHub();
    }

    const origin = env[ORIGIN_FOR[series]];
    const upstreamUrl = origin + url.pathname + url.search;

    const upstreamResponse = await fetch(upstreamUrl, {
      method: request.method,
      headers: request.headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    });

    const contentType = upstreamResponse.headers.get("content-type") ?? "";
    if (!contentType.includes("text/html")) {
      // JS/CSS/images/etc. pass straight through untouched.
      return upstreamResponse;
    }

    return new HTMLRewriter()
      .on("body", {
        element(el) {
          el.prepend(renderNav(series), { html: true });
        },
      })
      .transform(upstreamResponse);
  },
};
