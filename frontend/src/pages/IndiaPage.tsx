import React, { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getIndiaNews } from '../api/news';
import { getStatesMetadata } from '../api/states';
import { transformApiArticles } from '../utils/adapters';
import { CATEGORIES } from '../data/mockNews';
import { NewsCard } from '../components/news/NewsCard';
import { HeroStory } from '../components/news/HeroStory';
import { HeroSkeleton, GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { MapPin, RotateCcw, Building2, Info } from 'lucide-react';
import type { ApiStateMetadata } from '../api/types';

export const IndiaPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const selectedState = searchParams.get('state') || 'ALL';
  const selectedCategory = searchParams.get('category') || 'ALL';
  const selectedLanguage = searchParams.get('language') || 'ALL';

  // Load state metadata dynamically from the backend single source of truth
  const { data: statesData } = useQuery({
    queryKey: ['states', 'metadata'],
    queryFn: getStatesMetadata,
    staleTime: 1000 * 60 * 60, // 1 hour cache
  });

  const stateList: ApiStateMetadata[] = useMemo(() => {
    return statesData?.states || [];
  }, [statesData]);

  // Primary news query
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['news', 'india', selectedCategory, selectedState, selectedLanguage],
    queryFn: () =>
      getIndiaNews({
        category: selectedCategory === 'ALL' ? undefined : selectedCategory,
        state: selectedState === 'ALL' ? undefined : selectedState,
        language: selectedLanguage === 'ALL' ? undefined : selectedLanguage,
        limit: 30,
      }),
  });

  // Secondary fallback query: If user picked a specific native language and 0 articles exist, fetch English coverage
  const shouldFetchFallback = selectedLanguage !== 'ALL' && selectedLanguage !== 'en' && data && data.items.length === 0;
  const { data: fallbackData, isLoading: isFallbackLoading } = useQuery({
    queryKey: ['news', 'india', 'fallback', selectedCategory, selectedState],
    queryFn: () =>
      getIndiaNews({
        category: selectedCategory === 'ALL' ? undefined : selectedCategory,
        state: selectedState === 'ALL' ? undefined : selectedState,
        language: 'en',
        limit: 30,
      }),
    enabled: !!shouldFetchFallback,
  });

  const articles = useMemo(() => {
    if (data?.items && data.items.length > 0) {
      return transformApiArticles(data.items);
    }
    if (shouldFetchFallback && fallbackData?.items) {
      return transformApiArticles(fallbackData.items);
    }
    return [];
  }, [data, shouldFetchFallback, fallbackData]);

  const featuredIndiaStory = articles[0];
  const remainingArticles = articles.slice(1);
  const isFiltered = selectedState !== 'ALL' || selectedCategory !== 'ALL' || selectedLanguage !== 'ALL';

  const handleStateChange = (newState: string) => {
    const next = new URLSearchParams(searchParams);
    if (newState === 'ALL') {
      next.delete('state');
    } else {
      next.set('state', newState);
    }
    setSearchParams(next);
  };

  const handleCategoryChange = (newCat: string) => {
    const next = new URLSearchParams(searchParams);
    if (newCat === 'ALL') {
      next.delete('category');
    } else {
      next.set('category', newCat);
    }
    setSearchParams(next);
  };

  const handleResetFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  // Language label display helper
  const languageDisplayLabel = useMemo(() => {
    switch (selectedLanguage) {
      case 'hi': return 'Hindi (हिंदी)';
      case 'mr': return 'Marathi (मराठी)';
      case 'ta': return 'Tamil (தமிழ்)';
      case 'te': return 'Telugu (తెలుగు)';
      case 'ml': return 'Malayalam (മലയാളം)';
      case 'gu': return 'Gujarati (ગુજરાતી)';
      case 'kn': return 'Kannada (ಕನ್ನಡ)';
      case 'en': return 'English';
      case 'ALL': return 'All Languages';
      default: return selectedLanguage.toUpperCase();
    }
  }, [selectedLanguage]);

  return (
    <div className="space-y-10 w-full">
      {/* Header Banner */}
      <div className="bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-6 sm:p-8 lg:p-10 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron">
              <MapPin className="w-4 h-4" />
              National & Regional Coverage
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-black text-editorial-ink dark:text-white mt-1">
              India Spotlight
            </h1>
            <p className="text-sm sm:text-base text-editorial-muted dark:text-gray-400 font-serif mt-1 max-w-2xl">
              Real-time headlines, state-specific reporting, and multi-language coverage from across India. Select a regional language from the top bar or pick an individual state below.
            </p>
          </div>

          {/* Quick Active Stats */}
          <div className="flex items-center gap-4 bg-gray-50 dark:bg-paper-800 px-5 py-3 rounded-xl border border-gray-100 dark:border-paper-700 self-start md:self-auto text-xs">
            <div>
              <span className="text-editorial-muted dark:text-gray-400 block font-medium">Stories</span>
              <span className="font-serif font-bold text-lg text-editorial-ink dark:text-white">
                {shouldFetchFallback ? (fallbackData?.total ?? 0) : (data?.total ?? 0)}
              </span>
            </div>
            <span className="text-gray-300 dark:text-gray-700 select-none">|</span>
            <div>
              <span className="text-editorial-muted dark:text-gray-400 block font-medium">Scope</span>
              <span className="font-semibold text-bharat-saffron">
                {selectedState === 'ALL' ? 'Pan-India' : selectedState}
              </span>
            </div>
            {selectedLanguage !== 'ALL' && (
              <>
                <span className="text-gray-300 dark:text-gray-700 select-none">|</span>
                <div>
                  <span className="text-editorial-muted dark:text-gray-400 block font-medium">Language</span>
                  <span className="font-semibold text-bharat-navy dark:text-blue-400">
                    {languageDisplayLabel}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Filter Controls Strip */}
        <div className="mt-8 pt-6 border-t border-gray-100 dark:border-paper-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* State Filter Dropdown */}
            <div className="flex flex-wrap items-center gap-3">
              <label htmlFor="india-state-select" className="text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-bharat-saffron" />
                Select State:
              </label>
              <select
                id="india-state-select"
                value={selectedState}
                onChange={(e) => handleStateChange(e.target.value)}
                className="px-3.5 py-1.5 bg-gray-50 dark:bg-paper-800 border border-gray-300 dark:border-paper-700 rounded-lg text-xs font-semibold text-editorial-ink dark:text-white focus:ring-2 focus:ring-bharat-saffron focus:outline-none cursor-pointer"
              >
                <option value="ALL">All 28 States & 8 UTs</option>
                {stateList.map((state) => (
                  <option key={state.slug} value={state.name}>
                    {state.name} ({state.type})
                  </option>
                ))}
              </select>
            </div>

            {/* Reset Button */}
            {isFiltered && (
              <button
                onClick={handleResetFilters}
                className="flex items-center gap-1 text-xs text-bharat-crimson hover:underline font-medium cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Reset Filters
              </button>
            )}
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pt-1">
            <button
              onClick={() => handleCategoryChange('ALL')}
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                selectedCategory === 'ALL'
                  ? 'bg-editorial-ink text-white dark:bg-white dark:text-editorial-ink shadow-xs'
                  : 'bg-gray-100 dark:bg-paper-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
              }`}
            >
              All Categories
            </button>
            {CATEGORIES.map((cat) => {
              const isSelected = selectedCategory === cat.slug;
              return (
                <button
                  key={cat.slug}
                  onClick={() => handleCategoryChange(cat.slug)}
                  className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-bharat-saffron text-white shadow-xs'
                      : 'bg-gray-100 dark:bg-paper-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
                  }`}
                >
                  {cat.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Honest Native-Language Fallback Banner */}
      {shouldFetchFallback && (
        <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 rounded-xl p-4 flex items-start gap-3 text-amber-900 dark:text-amber-200 text-sm shadow-xs">
          <Info className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-xs uppercase tracking-wider text-amber-800 dark:text-amber-300">
              Regional Coverage Notice
            </p>
            <p className="text-xs sm:text-sm leading-relaxed">
              Regional-language coverage is currently limited. Showing English coverage for {selectedState === 'ALL' ? 'India' : selectedState}.
            </p>
          </div>
        </div>
      )}

      {/* Main Results View */}
      {isLoading || isFallbackLoading ? (
        <div className="space-y-10">
          <HeroSkeleton />
          <GridSkeleton count={4} />
        </div>
      ) : isError ? (
        <ErrorMessage
          title="Unable to load India news feed"
          message={error instanceof Error ? error.message : 'Backend connection error.'}
          onRetry={() => refetch()}
        />
      ) : articles.length === 0 ? (
        <EmptyState
          icon={<MapPin className="w-10 h-10" />}
          title="No Indian articles found for this filter combination"
          message="Try switching the state or selecting another language in the top header."
          actionText="Clear All Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="space-y-10">
          {/* Featured Lead for current filter */}
          {featuredIndiaStory && (
            <HeroStory article={featuredIndiaStory} />
          )}

          {/* Remaining grid */}
          {remainingArticles.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 lg:gap-8">
              {remainingArticles.map((article) => (
                <NewsCard key={article.id} article={article} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

