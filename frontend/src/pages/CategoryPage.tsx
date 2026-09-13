import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCategoryNews } from '../api/news';
import { transformApiArticles } from '../utils/adapters';
import { CATEGORIES } from '../data/mockNews';
import { HeroStory } from '../components/news/HeroStory';
import { NewsCard } from '../components/news/NewsCard';
import { CompactNewsItem } from '../components/news/CompactNewsItem';
import { HeroSkeleton, GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import type { CategorySlug } from '../types';
import { Compass, ArrowLeft } from 'lucide-react';

export const CategoryPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();

  const category = CATEGORIES.find((c) => c.slug === slug) || {
    name: slug ? slug.charAt(0).toUpperCase() + slug.slice(1).replace('-', ' ') : 'Category',
    slug: (slug || 'politics') as CategorySlug,
    description: 'Latest articles and developments in this field.',
  };

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['news', 'category', slug],
    queryFn: () => getCategoryNews(slug || 'politics', { limit: 30 }),
    enabled: !!slug,
  });

  const categoryArticles = React.useMemo(() => {
    return data?.items ? transformApiArticles(data.items) : [];
  }, [data]);

  const featuredStory = categoryArticles[0];
  const supportingStories = categoryArticles.slice(1, 4);
  const feedStories = categoryArticles.slice(4);

  return (
    <div className="space-y-12 sm:space-y-14">
      {/* Category Header */}
      <div className="bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-6 sm:p-8 lg:p-10 shadow-xs">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron mb-3">
          <Link to="/" className="hover:underline flex items-center gap-1 text-editorial-muted dark:text-gray-400">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Frontpage
          </Link>
          <span>/</span>
          <span>Taxonomy</span>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-black text-editorial-ink dark:text-white">
              {category.name}
            </h1>
            <p className="text-sm sm:text-base text-editorial-muted dark:text-gray-400 font-serif mt-1 max-w-2xl">
              {category.description}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-paper-800 px-5 py-3 rounded-xl border border-gray-100 dark:border-paper-700 text-xs self-start md:self-auto">
            <span className="text-editorial-muted dark:text-gray-400 block font-medium">Repository Status</span>
            <span className="font-serif font-bold text-lg text-editorial-ink dark:text-white">
              {data?.total ?? 0} {data?.total === 1 ? 'Article' : 'Articles'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Articles Stream */}
      {isLoading ? (
        <div className="space-y-10">
          <HeroSkeleton />
          <GridSkeleton count={3} />
        </div>
      ) : isError ? (
        <ErrorMessage
          title={`Unable to load ${category.name}`}
          message={error instanceof Error ? error.message : 'Category could not be loaded.'}
          onRetry={() => refetch()}
        />
      ) : categoryArticles.length === 0 ? (
        <EmptyState
          icon={<Compass className="w-10 h-10" />}
          title={`No articles currently stored under ${category.name}`}
          message="Our repository does not currently have active articles for this category. New stories will be indexed as they are collected."
          actionText="Return to Frontpage"
          onAction={() => window.location.assign('/')}
        />
      ) : (
        <div className="space-y-12 sm:space-y-14">
          {/* Level 1: Featured Lead Story */}
          {featuredStory && (
            <div>
              <div className="text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron mb-3">
                Lead Story in {category.name}
              </div>
              <HeroStory article={featuredStory} />
            </div>
          )}

          {/* Level 2: Supporting Stories (Wide 3-column or 2-column grid) */}
          {supportingStories.length > 0 && (
            <div className="pt-8 border-t border-gray-200 dark:border-paper-800">
              <h3 className="font-serif font-bold text-2xl text-editorial-ink dark:text-white mb-6">
                Supporting Coverage
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
                {supportingStories.map((article) => (
                  <NewsCard key={article.id} article={article} />
                ))}
              </div>
            </div>
          )}

          {/* Level 3: Compact Vertical Feed */}
          {feedStories.length > 0 && (
            <div className="pt-8 border-t border-gray-200 dark:border-paper-800">
              <h3 className="font-serif font-bold text-2xl text-editorial-ink dark:text-white mb-5">
                Earlier Reports in {category.name}
              </h3>
              <div className="bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-6 lg:p-8 shadow-xs divide-y divide-gray-100 dark:divide-paper-800">
                {feedStories.map((article) => (
                  <CompactNewsItem key={article.id} article={article} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
