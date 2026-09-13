export type Region = 'INDIA' | 'INTERNATIONAL';

export type CategorySlug = 
  | 'politics'
  | 'sports'
  | 'technology'
  | 'business'
  | 'movies-entertainment'
  | 'education'
  | 'science'
  | 'health'
  | 'lifestyle'
  | 'crime'
  | 'environment';

export interface CategoryInfo {
  name: string;
  slug: CategorySlug;
  description: string;
  count?: number;
}

export interface Source {
  id: string;
  name: string;
  url: string;
  country: 'IN' | 'GLOBAL';
}

export interface Article {
  id: string;
  title: string;
  description: string;
  content?: string;
  canonical_url: string;
  source: Source;
  category: CategorySlug;
  categoryName: string;
  region: Region;
  state?: string | null;
  language_code?: string;
  image_url: string;
  author?: string;
  published_at: string; // ISO String
  published_date: string; // YYYY-MM-DD
  read_time_minutes: number;
  is_featured?: boolean;
  is_breaking?: boolean;
  tags: string[];
}

export interface ArchiveFilterParams {
  date: string; // YYYY-MM-DD
  region?: 'ALL' | Region;
  category?: 'ALL' | CategorySlug;
  state?: 'ALL' | string;
  language?: 'ALL' | string;
}

export interface SearchFilterParams {
  query: string;
  region?: 'ALL' | Region;
  category?: 'ALL' | CategorySlug;
  state?: 'ALL' | string;
  language?: 'ALL' | string;
  dateFrom?: string;
  dateTo?: string;
  source?: 'ALL' | string;
}

export interface StateLanguageInfo {
  code: string;
  name_en: string;
  name_native: string;
  gnews_lang_code: string;
}

export interface StateMetadata {
  slug: string;
  name: string;
  type: 'STATE' | 'UT';
  default_language: string;
  supported_languages: StateLanguageInfo[];
}

