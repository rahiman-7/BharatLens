export interface ApiSource {
  id: number;
  name: string;
  domain: string;
  logo_url?: string | null;
  country: string;
}

export interface ApiCategory {
  id: number;
  name: string;
  slug: string;
  display_order: number;
}

export interface ApiArticle {
  id: number;
  title: string;
  description: string;
  canonical_url: string;
  source_id: number;
  category_id: number;
  region: 'INDIA' | 'INTERNATIONAL';
  state?: string | null;
  language_code?: string;
  image_url?: string | null;
  author?: string | null;
  published_at: string;
  fetched_at: string;
  created_at: string;
  source?: ApiSource | null;
  category?: ApiCategory | null;
}

export interface PaginatedResponse<T> {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  items: T[];
}

export interface CategoriesResponse {
  total: number;
  categories: ApiCategory[];
}

export interface StatesResponse {
  total: number;
  states: string[];
}

export interface ApiStateLanguageInfo {
  code: string;
  name_en: string;
  name_native: string;
  gnews_lang_code: string;
}

export interface ApiStateMetadata {
  slug: string;
  name: string;
  type: 'STATE' | 'UT';
  default_language: string;
  supported_languages: ApiStateLanguageInfo[];
}

export interface StatesMetadataResponse {
  total: number;
  states: ApiStateMetadata[];
}

export interface HealthResponse {
  status: string;
  service: string;
  tagline: string;
  database: string;
  version: string;
}

