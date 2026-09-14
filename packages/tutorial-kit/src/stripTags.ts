const NAMED_ENTITIES: Record<string, string> = {
  amp: "&",
  lt: "<",
  gt: ">",
  quot: '"',
  apos: "'",
};

/**
 * Frontmatter titles carry inline HTML (e.g. `<em>` for the accent-colored
 * word in the on-page heading, `&amp;` for a literal ampersand). Anywhere
 * that title needs to render as plain text instead — <title>, nav links,
 * list labels, RSS items — strip it first. Entities are decoded too, since a
 * left-over `&amp;` would otherwise get re-escaped by the consuming context
 * (HTML or XML) into a visible `&amp;amp;`.
 */
export function stripTags(html: string): string {
  return html
    .replace(/<[^>]+>/g, "")
    .replace(/&(amp|lt|gt|quot|apos);/g, (_, name) => NAMED_ENTITIES[name]);
}
