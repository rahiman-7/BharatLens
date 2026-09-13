import { apiClient } from './client';
import type { PaginatedResponse } from './types';

export interface StoryArticleSummary {
  id: number;
  title: string;
  description?: string;
  canonical_url: string;
  image_url?: string;
  author?: string;
  region: string;
  state?: string;
  published_at: string;
  source_name: string;
  category_name: string;
  category_slug: string;
  read_time_minutes?: number;
}

export interface StoryGroupResponse {
  id: number;
  representative_article?: StoryArticleSummary;
  article_count: number;
  sources: string[];
  created_at: string;
  updated_at: string;
}

export interface StoryGroupDetailResponse {
  id: number;
  representative_article?: StoryArticleSummary;
  article_count: number;
  sources: string[];
  articles: StoryArticleSummary[];
  created_at: string;
  updated_at: string;
}

export async function getStories(
  page: number = 1,
  limit: number = 10,
  minArticles: number = 1
): Promise<PaginatedResponse<StoryGroupResponse>> {
  const query = `?page=${page}&limit=${limit}&min_articles=${minArticles}`;
  return apiClient<PaginatedResponse<StoryGroupResponse>>(`/stories${query}`);
}

export async function getStory(
  storyId: number | string
): Promise<StoryGroupDetailResponse> {
  return apiClient<StoryGroupDetailResponse>(`/stories/${encodeURIComponent(String(storyId))}`);
}

export async function getRelatedCoverage(
  articleId: number | string
): Promise<StoryArticleSummary[]> {
  return apiClient<StoryArticleSummary[]>(`/news/${encodeURIComponent(String(articleId))}/related`);
}
