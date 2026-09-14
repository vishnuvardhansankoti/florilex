export type SeriesId = "aiml" | "go";

/**
 * Shared chrome injected into every proxied HTML page so the two
 * independently-built series feel like one site. Deliberately
 * theme-neutral (doesn't reuse either series' accent) since it wraps
 * both — each series still owns everything below the nav.
 */
export function renderNav(active: SeriesId | null): string {
  const link = (id: SeriesId, label: string) =>
    `<a class="florilex-nav-link${active === id ? " florilex-nav-link--active" : ""}" href="/${id}/">${label}</a>`;

  return `
<style>
  .florilex-nav {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 0.75rem 1.5rem;
    background: #0c1013;
    border-bottom: 1px solid #2a3237;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.82rem;
    letter-spacing: 0.02em;
  }
  .florilex-nav-brand {
    color: #e7ebed;
    font-weight: 600;
    margin-right: 0.5rem;
    text-decoration: none;
  }
  .florilex-nav-link {
    color: #a7b1b7;
    text-decoration: none;
    padding: 0.25rem 0;
    border-bottom: 2px solid transparent;
  }
  .florilex-nav-link:hover { color: #e7ebed; }
  .florilex-nav-link--active { color: #e7ebed; border-bottom-color: currentColor; }
</style>
<nav class="florilex-nav">
  <a class="florilex-nav-brand" href="/">Florilex</a>
  ${link("aiml", "AIML")}
  ${link("go", "Go")}
</nav>`.trim();
}
