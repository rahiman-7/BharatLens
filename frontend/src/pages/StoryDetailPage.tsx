import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getStory } from '../api/storiesApi';
import { formatTimeAgo, formatFullDate, getCategoryBadgeClasses, getRegionBadgeClasses } from '../utils';
import type { CategorySlug, Region } from '../types';
import { Layers, ArrowLeft, ExternalLink, ShieldCheck, Clock, ArrowUpRight, Newspaper } from 'lucide-react';

export const StoryDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: story, isLoading, isError, error } = useQuery({
    queryKey: ['story-detail', id],
    queryFn: () => getStory(id || ''),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-pulse py-8">
        <div className="h-6 w-32 bg-stone-200 dark:bg-stone-800 rounded" />
        <div className="h-10 w-full bg-stone-200 dark:bg-stone-800 rounded" />
        <div className="h-6 w-3/4 bg-stone-200 dark:bg-stone-800 rounded" />
        <div className="h-48 w-full bg-stone-200 dark:bg-stone-800 rounded-2xl" />
        <div className="space-y-4 pt-4">
          <div className="h-28 bg-stone-200 dark:bg-stone-800 rounded-xl" />
          <div className="h-28 bg-stone-200 dark:bg-stone-800 rounded-xl" />
        </div>
      </div>
    );
  }

  if (isError || !story) {
    return (
      <div className="max-w-xl mx-auto text-center py-20 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-8 shadow-xs">
        <h2 className="text-2xl font-serif font-bold text-stone-900 dark:text-stone-100">
          Story Cluster Not Found
        </h2>
        <p className="text-sm text-stone-600 dark:text-stone-400 mt-2 font-serif">
          {error instanceof Error ? error.message : 'The requested story group could not be found.'}
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="px-5 py-2.5 bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 text-xs font-semibold rounded-xl hover:bg-stone-200 transition-colors cursor-pointer"
          >
            Go Back
          </button>
          <Link
            to="/stories"
            className="px-5 py-2.5 bg-orange-600 text-white text-xs font-semibold rounded-xl hover:bg-orange-700 transition-colors"
          >
            View All Stories
          </Link>
        </div>
      </div>
    );
  }

  const rep = story.representative_article;

  return (
    <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-4xl">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between gap-4 mb-6 pb-4 border-b border-stone-200 dark:border-stone-800 text-xs">
        <Link
          to="/stories"
          className="inline-flex items-center gap-1.5 text-stone-600 dark:text-stone-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>All Story Clusters</span>
        </Link>

        <span className="text-stone-400 dark:text-stone-500 font-mono text-[11px]">
          Story Cluster #{story.id}
        </span>
      </div>

      {/* Hero Representative Story Card */}
      {rep && (
        <div className="p-6 sm:p-8 bg-white dark:bg-stone-900 rounded-2xl border border-stone-200 dark:border-stone-800 shadow-xs mb-10 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-orange-600 dark:text-orange-400">
              <Layers className="w-3.5 h-3.5" />
              Lead Representative Story
            </span>
            <span className="text-stone-300 dark:text-stone-700">•</span>
            <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded border ${getCategoryBadgeClasses(rep.category_slug as CategorySlug)}`}>
              {rep.category_name}
            </span>
            <span className={`text-[11px] px-2 py-0.5 rounded-full border ${getRegionBadgeClasses(rep.region as Region)}`}>
              {rep.region === 'INDIA' ? 'India' : 'Global'}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-black text-stone-900 dark:text-stone-100 leading-tight">
            {rep.title}
          </h1>

          {rep.description && (
            <p className="text-base text-stone-600 dark:text-stone-300 font-serif leading-relaxed">
              {rep.description}
            </p>
          )}

          {/* Lead Meta Strip */}
          <div className="pt-4 border-t border-stone-100 dark:border-stone-800 flex flex-wrap items-center justify-between gap-3 text-xs text-stone-500 dark:text-stone-400">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-stone-800 dark:text-stone-200 flex items-center gap-1">
                <ShieldCheck className="w-4 h-4 text-orange-600" />
                Original Reporting: {rep.source_name}
              </span>
              <span>•</span>
              <span title={formatFullDate(rep.published_at)}>{formatTimeAgo(rep.published_at)}</span>
            </div>

            <Link
              to={`/article/${rep.id}`}
              className="inline-flex items-center gap-1 text-orange-600 dark:text-orange-400 font-medium hover:underline"
            >
              <span>Read Full Article</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Multi-Source Coverage Section */}
      <section className="space-y-6">
        <div className="flex items-center justify-between gap-4 pb-4 border-b border-stone-200 dark:border-stone-800">
          <div>
            <h2 className="text-xl sm:text-2xl font-serif font-bold text-stone-900 dark:text-stone-100">
              Coverage & Multi-Source Perspectives
            </h2>
            <p className="text-xs text-stone-600 dark:text-stone-400 mt-0.5">
              {story.article_count} article{story.article_count === 1 ? '' : 's'} reporting on this event from {story.sources.length} outlet{story.sources.length === 1 ? '' : 's'}.
            </p>
          </div>

          {/* Sources Count Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-900/50 text-xs font-semibold">
            <Newspaper className="w-3.5 h-3.5" />
            <span>{story.sources.length} Publishers</span>
          </div>
        </div>

        {/* Articles List */}
        <div className="space-y-4">
          {story.articles.map((art) => {
            const isLead = rep?.id === art.id;

            return (
              <div
                key={art.id}
                className={`p-6 bg-white dark:bg-stone-900 rounded-xl border transition-all ${
                  isLead
                    ? 'border-orange-300 dark:border-orange-800/80 bg-orange-50/20 dark:bg-orange-950/10'
                    : 'border-stone-200 dark:border-stone-800 hover:border-stone-300 dark:hover:border-stone-700'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <Link
                    to={`/article/${art.id}`}
                    className="flex flex-col sm:flex-row sm:items-start gap-4 flex-1 block cursor-pointer group"
                  >
                    {art.image_url && (
                      <div className="w-full sm:w-28 sm:h-24 rounded-lg overflow-hidden flex-shrink-0 bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-800">
                        <img
                          src={art.image_url}
                          alt={art.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          loading="lazy"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2 text-xs text-stone-500 dark:text-stone-400">
                        <span className="font-semibold text-stone-800 dark:text-stone-200 flex items-center gap-1">
                          <ShieldCheck className="w-3.5 h-3.5 text-orange-600" />
                          {art.source_name}
                        </span>
                        {isLead && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-100 dark:bg-orange-950 text-orange-700 dark:text-orange-300">
                            Lead
                          </span>
                        )}
                        <span>•</span>
                        <span className="flex items-center gap-1" title={formatFullDate(art.published_at)}>
                          <Clock className="w-3 h-3" />
                          {formatTimeAgo(art.published_at)}
                        </span>
                      </div>

                      <h3 className="block text-lg font-serif font-bold text-stone-900 dark:text-stone-100 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors leading-snug">
                        {art.title}
                      </h3>

                      {art.description && (
                        <p className="text-sm text-stone-600 dark:text-stone-400 font-serif leading-relaxed line-clamp-3">
                          {art.description}
                        </p>
                      )}
                    </div>
                  </Link>

                  {/* External Publisher Action */}
                  <div className="flex sm:flex-col items-center sm:items-end gap-2 shrink-0 pt-2 sm:pt-0 z-10">
                    <Link
                      to={`/article/${art.id}`}
                      className="px-3.5 py-1.5 bg-stone-900 hover:bg-orange-600 dark:bg-stone-800 dark:hover:bg-orange-600 text-white text-xs font-medium rounded-lg transition-colors cursor-pointer"
                    >
                      Read Story
                    </Link>
                    {art.canonical_url && (
                      <a
                        href={art.canonical_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] text-stone-500 hover:text-stone-700 dark:hover:text-stone-300 font-medium transition-colors cursor-pointer"
                        title={`Open original article at ${art.source_name}`}
                      >
                        <span>Original</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </main>
  );
};
