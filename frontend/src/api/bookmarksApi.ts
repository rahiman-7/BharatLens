import { apiClient } from './client';
import type { ApiArticle, PaginatedResponse } from './types';

export interface BookmarkStatus {
  is_bookmarked: boolean;
  article_id: number;
}

export async function addBookmarkApi(articleId: number): Promise<BookmarkStatus> {
  return apiClient<BookmarkStatus>(`/bookmarks/${articleId}`, {
    method: 'POST',
  });
}

export async function removeBookmarkApi(articleId: number): Promise<BookmarkStatus> {
  return apiClient<BookmarkStatus>(`/bookmarks/${articleId}`, {
    method: 'DELETE',
  });
}

export async function getBookmarkStatusApi(articleId: number): Promise<BookmarkStatus> {
  return apiClient<BookmarkStatus>(`/bookmarks/${articleId}`);
}

export async function getBookmarksApi(
  page: number = 1,
  limit: number = 20
): Promise<PaginatedResponse<ApiArticle>> {
  return apiClient<PaginatedResponse<ApiArticle>>(`/bookmarks?page=${page}&limit=${limit}`);
}
