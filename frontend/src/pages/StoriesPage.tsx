import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getStories } from '../api/storiesApi';
import { formatTimeAgo, formatFullDate, getCategoryBadgeClasses, getRegionBadgeClasses } from '../utils';
import type { CategorySlug, Region } from '../types';
import { GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { Layers, ArrowRight, Newspaper, ArrowLeft, ShieldCheck } from 'lucide-react';

export const StoriesPage: React.FC = () => {
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['stories-list', page],
    queryFn: () => getStories(page, 10, 1),
  });

  const stories = data?.items || [];

  return (
    <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-6xl">
      {/* Header Banner */}
      <div className="mb-8 pb-6 border-b border-stone-200 dark:border-stone-800 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-orange-600 dark:text-orange-400 mb-1.5">
            <Layers className="w-4 h-4" />
            <span>Multi-Source Coverage</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-serif font-bold text-stone-900 dark:text-stone-100 tracking-tight">
            Story Clusters
          </h1>
          <p className="mt-1 text-sm text-stone-600 dark:text-stone-400 font-serif">
            Major news events grouped across multiple publishers. Compare perspectives and see the complete picture.
          </p>
        </div>

        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-stone-600 dark:text-stone-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Frontpage</span>
        </Link>
      </div>

      {/* Content */}
      {isLoading ? (
        <GridSkeleton count={5} />
      ) : isError ? (
        <ErrorMessage
          message={error instanceof Error ? error.message : 'Failed to load story clusters.'}
          onRetry={() => refetch()}
        />
      ) : stories.length === 0 ? (
        <div className="py-20 text-center bg-stone-50 dark:bg-stone-900/40 rounded-2xl border border-dashed border-stone-300 dark:border-stone-800 max-w-lg mx-auto p-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-stone-200 dark:bg-stone-800 text-stone-400 mb-4">
            <Newspaper className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-serif font-bold text-stone-800 dark:text-stone-200">
            No Story Clusters Found
          </h2>
          <p className="mt-2 text-sm text-stone-500 dark:text-stone-400">
            As incoming news is processed by the background ingestion pipeline, matching stories will cluster here.
          </p>
          <Link
            to="/"
            className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-xl shadow-sm text-sm transition-colors"
          >
            <span>Explore All News</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {stories.map((story) => {
            const rep = story.representative_article;
            if (!rep) return null;

            return (
              <div
                key={story.id}
                className="group p-6 bg-white dark:bg-stone-900 rounded-2xl border border-stone-200 dark:border-stone-800 hover:border-orange-300 dark:hover:border-orange-800 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col md:flex-row justify-between gap-6"
              >
                <div className="flex-1 space-y-3">
                  {/* Badges & Timestamp */}
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded border ${getCategoryBadgeClasses(rep.category_slug as CategorySlug)}`}>
                      {rep.category_name}
                    </span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full border ${getRegionBadgeClasses(rep.region as Region)}`}>
                      {rep.region === 'INDIA' ? 'India' : 'Global'}
                    </span>
                    <span className="text-xs text-stone-400 dark:text-stone-500" title={formatFullDate(rep.published_at)}>
                      • {formatTimeAgo(rep.published_at)}
                    </span>
                  </div>

                  {/* Headline */}
                  <Link
                    to={`/stories/${story.id}`}
                    className="block text-xl sm:text-2xl font-serif font-bold text-stone-900 dark:text-stone-100 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors leading-snug"
                  >
                    {rep.title}
                  </Link>

                  {/* Summary */}
                  {rep.description && (
                    <p className="text-sm text-stone-600 dark:text-stone-400 font-serif line-clamp-2 leading-relaxed">
                      {rep.description}
                    </p>
                  )}

                  {/* Source coverage tags */}
                  <div className="pt-2 flex flex-wrap items-center gap-1.5">
                    <span className="text-xs font-semibold text-stone-500 dark:text-stone-400 mr-1 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-orange-600" />
                      Coverage:
                    </span>
                    {story.sources.map((src, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 border border-stone-200 dark:border-stone-700"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Right Action Callout */}
                <div className="flex md:flex-col items-center md:items-end justify-between md:justify-center gap-3 border-t md:border-t-0 md:border-l border-stone-100 dark:border-stone-800 pt-4 md:pt-0 md:pl-6 min-w-[170px]">
                  <div className="text-left md:text-right">
                    <span className="text-2xl font-serif font-bold text-orange-600 dark:text-orange-400 block">
                      {story.article_count}
                    </span>
                    <span className="text-xs text-stone-500 dark:text-stone-400">
                      {story.article_count === 1 ? 'Source reporting' : 'Sources reporting'}
                    </span>
                  </div>

                  <Link
                    to={`/stories/${story.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-stone-900 hover:bg-orange-600 dark:bg-stone-800 dark:hover:bg-orange-600 text-white font-medium rounded-xl text-xs transition-colors shadow-sm"
                  >
                    <span>View Perspectives</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-8 border-t border-stone-200 dark:border-stone-800">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-4 py-2 rounded-xl border border-stone-300 dark:border-stone-700 text-sm font-medium text-stone-700 dark:text-stone-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors cursor-pointer"
              >
                Previous
              </button>
              <span className="text-sm text-stone-500 dark:text-stone-400">
                Page {page} of {data.total_pages}
              </span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="px-4 py-2 rounded-xl border border-stone-300 dark:border-stone-700 text-sm font-medium text-stone-700 dark:text-stone-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors cursor-pointer"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </main>
  );
};
