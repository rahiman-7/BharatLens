import { apiClient } from './client';
import type { ApiArticle, PaginatedResponse } from './types';

export interface NewsFilterParams {
  region?: 'INDIA' | 'INTERNATIONAL';
  category?: string;
  state?: string;
  language?: string;
  page?: number;
  limit?: number;
}

export interface ArchiveFilterParams {
  date?: string;
  region?: 'INDIA' | 'INTERNATIONAL';
  category?: string;
  state?: string;
  language?: string;
  page?: number;
  limit?: number;
}

export interface SearchFilterParams {
  q?: string;
  region?: 'INDIA' | 'INTERNATIONAL';
  category?: string;
  state?: string;
  language?: string;
  date?: string;
  page?: number;
  limit?: number;
}

function buildQueryString(params: Record<string, string | number | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '' && value !== 'ALL') {
      query.append(key, String(value));
    }
  }
  const str = query.toString();
  return str ? `?${str}` : '';
}

export async function getLatestNews(
  params?: NewsFilterParams
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({
    region: params?.region,
    category: params?.category,
    state: params?.state,
    language: params?.language,
    page: params?.page || 1,
    limit: params?.limit || 20,
  });
  return apiClient<PaginatedResponse<ApiArticle>>(`/news/latest${query}`);
}

export async function getIndiaNews(
  params?: Omit<NewsFilterParams, 'region'>
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({
    category: params?.category,
    state: params?.state,
    language: params?.language,
    page: params?.page || 1,
    limit: params?.limit || 20,
  });
  return apiClient<PaginatedResponse<ApiArticle>>(`/news/india${query}`);
}

export async function getStateNews(
  stateSlug: string,
  params?: { category?: string; language?: string; page?: number; limit?: number }
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({
    category: params?.category,
    language: params?.language,
    page: params?.page || 1,
    limit: params?.limit || 20,
  });
  return apiClient<PaginatedResponse<ApiArticle>>(`/news/state/${encodeURIComponent(stateSlug)}${query}`);
}

export async function getInternationalNews(
  params?: Omit<NewsFilterParams, 'region' | 'state'>
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({
    category: params?.category,
    language: params?.language,
    page: params?.page || 1,
    limit: params?.limit || 20,
  });
  return apiClient<PaginatedResponse<ApiArticle>>(`/news/international${query}`);
}

export async function getCategoryNews(
  slug: string,
  params?: Omit<NewsFilterParams, 'category'>
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({
    region: params?.region,
    state: params?.state,
    language: params?.language,
    page: params?.page || 1,
    limit: params?.limit || 20,
  });
  return apiClient<PaginatedResponse<ApiArticle>>(`/news/category/${encodeURIComponent(slug)}${query}`);
}

export async function getArticle(
  articleId: string | number
): Promise<ApiArticle> {
  return apiClient<ApiArticle>(`/news/${encodeURIComponent(String(articleId))}`);
}

export interface ArchiveDateInfo {
  date: string;
  article_count: number;
}

export async function getArchiveDates(limit: number = 30): Promise<ArchiveDateInfo[]> {
  return apiClient<ArchiveDateInfo[]>(`/archive/dates?limit=${limit}`);
}

export async function getArchiveNews(
  params: ArchiveFilterParams
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({
    date: params.date,
    region: params.region,
    category: params.category,
    state: params.state,
    language: params.language,
    page: params.page || 1,
    limit: params.limit || 20,
  });
  return apiClient<PaginatedResponse<ApiArticle>>(`/archive${query}`);
}

export async function getSearchNews(
  params: SearchFilterParams
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({
    q: params.q,
    region: params.region,
    category: params.category,
    state: params.state,
    language: params.language,
    date: params.date,
    page: params.page || 1,
    limit: params.limit || 20,
  });
  return apiClient<PaginatedResponse<ApiArticle>>(`/search${query}`);
}

export async function getForYouNews(
  page: number = 1,
  limit: number = 12
): Promise<PaginatedResponse<ApiArticle>> {
  const query = buildQueryString({ page, limit });
  return apiClient<PaginatedResponse<ApiArticle>>(`/news/for-you${query}`);
}


