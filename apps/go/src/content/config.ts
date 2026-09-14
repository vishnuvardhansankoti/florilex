import { defineCollection, z } from "astro:content";

const lessons = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    summary: z.string(),
    phase: z.string(),
    phaseTitle: z.string(),
    order: z.number(),
    lessonNumber: z.number(),
    hook: z.string().optional(),
    hookCredit: z.string().optional(),
    sourceUrl: z.string().url().optional(),
  }),
});

export const collections = { lessons };
