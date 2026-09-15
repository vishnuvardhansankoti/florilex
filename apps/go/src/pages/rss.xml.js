import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import { stripTags } from "@florilex/tutorial-kit/stripTags";

export async function GET(context) {
  const lessons = (await getCollection("lessons"))
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf())
    .slice(0, 2);

  return rss({
    title: "Go from Scratch",
    description: "Detailed, from-scratch tutorials on the Go language and its runtime.",
    site: context.site,
    items: lessons.map((lesson) => ({
      title: stripTags(lesson.data.title),
      description: lesson.data.summary,
      link: `/go/phases/${lesson.slug.replace(/^phases\//, "")}`,
      pubDate: lesson.data.pubDate,
      categories: [lesson.data.phaseTitle],
    })),
  });
}
