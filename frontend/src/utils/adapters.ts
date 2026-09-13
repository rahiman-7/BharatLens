import type { ApiArticle } from '../api/types';
import type { Article, CategorySlug } from '../types';

const FALLBACK_CATEGORY_IMAGES: Record<string, string> = {
  politics: 'https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80',
  sports: 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=1200&q=80',
  technology: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80',
  business: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80',
  'movies-entertainment': 'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=1200&q=80',
  education: 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1200&q=80',
  science: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80',
  health: 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1200&q=80',
  lifestyle: 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1200&q=80',
  crime: 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80',
  environment: 'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80',
};

const DEFAULT_IMAGE = 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?auto=format&fit=crop&w=1200&q=80';

export function transformApiArticleToArticle(apiArticle: ApiArticle): Article {
  const categorySlug = (apiArticle.category?.slug || 'politics') as CategorySlug;
  const categoryName = apiArticle.category?.name || 'News';
  const wordCount = (apiArticle.description || '').split(/\s+/).filter(Boolean).length;
  const readTime = Math.max(1, Math.ceil(wordCount / 30));

  const publishedDate = apiArticle.published_at ? apiArticle.published_at.substring(0, 10) : '';

  return {
    id: String(apiArticle.id),
    title: apiArticle.title,
    description: apiArticle.description,
    canonical_url: apiArticle.canonical_url,
    source: {
      id: String(apiArticle.source?.id || apiArticle.source_id),
      name: apiArticle.source?.name || 'Source',
      url: apiArticle.source?.domain ? `https://${apiArticle.source.domain}` : apiArticle.canonical_url,
      country: apiArticle.source?.country === 'GLOBAL' ? 'GLOBAL' : 'IN',
    },
    category: categorySlug,
    categoryName: categoryName,
    region: apiArticle.region || 'INDIA',
    state: apiArticle.state || null,
    language_code: apiArticle.language_code || 'en',
    image_url: apiArticle.image_url || FALLBACK_CATEGORY_IMAGES[categorySlug] || DEFAULT_IMAGE,
    author: apiArticle.author || undefined,
    published_at: apiArticle.published_at,
    published_date: publishedDate,
    read_time_minutes: readTime,
    is_featured: false,
    is_breaking: false,
    tags: [categoryName],
  };
}

export function transformApiArticles(apiArticles: ApiArticle[]): Article[] {
  return apiArticles.map(transformApiArticleToArticle);
}
