import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getInternationalNews } from '../api/news';
import { transformApiArticles } from '../utils/adapters';
import { CATEGORIES } from '../data/mockNews';
import { NewsCard } from '../components/news/NewsCard';
import { HeroStory } from '../components/news/HeroStory';
import { HeroSkeleton, GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { Globe } from 'lucide-react';

export const InternationalPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['news', 'international', selectedCategory],
    queryFn: () =>
      getInternationalNews({
        category: selectedCategory === 'ALL' ? undefined : selectedCategory,
        limit: 30,
      }),
  });

  const internationalArticles = React.useMemo(() => {
    return data?.items ? transformApiArticles(data.items) : [];
  }, [data]);

  const featuredGlobalStory = internationalArticles[0];
  const remainingGlobalStories = internationalArticles.slice(1);

  return (
    <div className="space-y-10 w-full">
      {/* Editorial Header */}
      <div className="bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 text-white rounded-2xl p-6 sm:p-10 lg:p-12 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-blue-300">
              <Globe className="w-4 h-4" />
              Global Geopolitics & Innovation
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-black text-white mt-1">
              "See the World" — International News
            </h1>
            <p className="text-sm sm:text-base text-blue-200/80 font-serif mt-1 max-w-2xl">
              Essential global events, international economic treaties, climate diplomacy, and frontier space discoveries.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md px-5 py-3 rounded-xl border border-white/10 text-xs self-start md:self-auto">
            <span className="text-blue-200 block font-medium">International Feed</span>
            <span className="font-serif font-bold text-lg text-white">
              {data?.total ?? 0} Stories Available
            </span>
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="mt-8 pt-6 border-t border-white/10 flex items-center gap-2 overflow-x-auto no-scrollbar">
          <button
            onClick={() => setSelectedCategory('ALL')}
            className={`px-3.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
              selectedCategory === 'ALL'
                ? 'bg-blue-500 text-white shadow-xs font-semibold'
                : 'bg-white/10 text-blue-200 hover:bg-white/20'
            }`}
          >
            All International
          </button>
          {['environment', 'technology', 'business', 'science', 'sports', 'politics'].map((catSlug) => {
            const catInfo = CATEGORIES.find((c) => c.slug === catSlug);
            if (!catInfo) return null;
            const isSelected = selectedCategory === catSlug;
            return (
              <button
                key={catSlug}
                onClick={() => setSelectedCategory(catSlug)}
                className={`px-3.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                  isSelected
                    ? 'bg-white text-blue-950 font-bold shadow-xs'
                    : 'bg-white/10 text-blue-200 hover:bg-white/20'
                }`}
              >
                {catInfo.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Global Content */}
      {isLoading ? (
        <div className="space-y-10">
          <HeroSkeleton />
          <GridSkeleton count={3} />
        </div>
      ) : isError ? (
        <ErrorMessage
          title="Unable to load International News"
          message={error instanceof Error ? error.message : 'Backend connection error.'}
          onRetry={() => refetch()}
        />
      ) : internationalArticles.length === 0 ? (
        <EmptyState
          icon={<Globe className="w-10 h-10" />}
          title="No international stories matching this filter"
          message="No international stories were found in the current backend database for this category."
          actionText="View All International News"
          onAction={() => setSelectedCategory('ALL')}
        />
      ) : (
        <div className="space-y-10">
          {featuredGlobalStory && (
            <HeroStory article={featuredGlobalStory} />
          )}

          {remainingGlobalStories.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 lg:gap-8">
              {remainingGlobalStories.map((article) => (
                <NewsCard key={article.id} article={article} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
