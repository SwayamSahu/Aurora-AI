/**
 * Blog ("The Journal") — single source of truth for chrome copy and the
 * category catalog. Category `id` values are the exact strings stored in
 * the backend's `category` column — edit here to add/rename a category.
 */

export interface BlogCategory {
  id: string;
  label: string;
  /** lucide-react icon name, resolved by landingIcon(). */
  icon: string;
}

export const BLOG_CATEGORIES: BlogCategory[] = [
  { id: "tutorials", label: "Tutorials", icon: "BookOpen" },
  { id: "prompts", label: "Prompts", icon: "PenLine" },
  { id: "workflows", label: "Workflows", icon: "Workflow" },
  { id: "video", label: "Video", icon: "Video" },
  { id: "news", label: "News", icon: "Newspaper" },
  { id: "showcase", label: "Showcase", icon: "Trophy" },
];

export function categoryLabel(id: string): string {
  return BLOG_CATEGORIES.find((c) => c.id === id)?.label ?? id;
}

export const blogHero = {
  eyebrow: "Write · Share · Inspire",
  titleLead: "The",
  titleAccent: "Journal",
  subtitle:
    "Tutorials, prompts and creative guides from the people building on Aurora.",
  searchPlaceholder: "Search guides, tutorials, prompts…",
};

export const blogCopy = {
  featuredHeading: "Featured",
  categoriesHeading: "Browse by Category",
  allPostsHeading: "All Posts",
  writeCta: "Write a post",
  emptyState: "No posts yet — be the first to write one.",
};
