import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import { stripTags } from "@florilex/tutorial-kit/stripTags";

export async function GET(context) {
  const lessons = (await getCollection("lessons"))
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf())
    .slice(0, 2);

  return rss({
    title: "AI Engineering from Scratch",
    description: "Detailed, from-scratch tutorials on the math and code underneath modern AI systems.",
    site: context.site,
    items: lessons.map((lesson) => ({
      title: stripTags(lesson.data.title),
      description: lesson.data.summary,
      link: `/aiml/phases/${lesson.slug.replace(/^phases\//, "")}`,
      pubDate: lesson.data.pubDate,
      categories: [lesson.data.phaseTitle],
    })),
  });
}
