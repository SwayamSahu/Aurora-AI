import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  addComment,
  createPost,
  deleteComment,
  deletePost,
  getCategoryCounts,
  getComments,
  getFeatured,
  getMyPosts,
  getPost,
  listPosts,
  toggleLike,
  updatePost,
  type BlogPostInput,
} from "@/lib/blog/api";

const PAGE_SIZE = 12;

export function usePostsInfinite(category: string, query: string, sort = "recent") {
  return useInfiniteQuery({
    queryKey: ["blog-posts", category, query, sort],
    queryFn: ({ pageParam }) =>
      listPosts({ category, q: query, sort, limit: PAGE_SIZE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (last) => last.next_offset,
  });
}

export function useFeaturedPosts() {
  return useQuery({ queryKey: ["blog-featured"], queryFn: getFeatured });
}

export function useCategoryCounts() {
  return useQuery({ queryKey: ["blog-categories"], queryFn: getCategoryCounts });
}

export function useMyPosts() {
  return useQuery({ queryKey: ["blog-my-posts"], queryFn: getMyPosts });
}

export function usePost(slug: string) {
  return useQuery({
    queryKey: ["blog-post", slug],
    queryFn: () => getPost(slug),
    enabled: !!slug,
  });
}

export function useComments(slug: string) {
  return useQuery({
    queryKey: ["blog-comments", slug],
    queryFn: () => getComments(slug),
    enabled: !!slug,
  });
}

export function useCreatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: BlogPostInput) => createPost(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["blog-posts"] });
      qc.invalidateQueries({ queryKey: ["blog-my-posts"] });
      qc.invalidateQueries({ queryKey: ["blog-featured"] });
      qc.invalidateQueries({ queryKey: ["blog-categories"] });
    },
  });
}

export function useUpdatePost(slug?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<BlogPostInput> }) =>
      updatePost(id, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["blog-posts"] });
      qc.invalidateQueries({ queryKey: ["blog-my-posts"] });
      if (slug) qc.invalidateQueries({ queryKey: ["blog-post", slug] });
    },
  });
}

export function useDeletePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deletePost(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["blog-posts"] });
      qc.invalidateQueries({ queryKey: ["blog-my-posts"] });
    },
  });
}

export function useToggleLike(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ postId, liked }: { postId: string; liked: boolean }) =>
      toggleLike(postId, liked),
    onSuccess: (updated) => {
      qc.setQueryData(["blog-post", slug], updated);
    },
  });
}

export function useAddComment(slug: string, postId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => addComment(postId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["blog-comments", slug] });
    },
  });
}

export function useDeleteComment(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (commentId: string) => deleteComment(commentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["blog-comments", slug] });
    },
  });
}
