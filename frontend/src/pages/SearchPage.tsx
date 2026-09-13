import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getSearchNews } from '../api/news';
import { transformApiArticles } from '../utils/adapters';
import { SearchBar } from '../components/search/SearchBar';
import { SearchFilters } from '../components/search/SearchFilters';
import { NewsCard } from '../components/news/NewsCard';
import { GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import type { Region, CategorySlug } from '../types';
import { Search, Inbox, Sparkles } from 'lucide-react';

export const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';

  const [query, setQuery] = useState(initialQuery);
  const [selectedRegion, setSelectedRegion] = useState<'ALL' | Region>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<'ALL' | CategorySlug>('ALL');
  const [selectedState, setSelectedState] = useState<'ALL' | string>('ALL');
  const [selectedLanguage, setSelectedLanguage] = useState<'ALL' | string>('ALL');

  useEffect(() => {
    const q = searchParams.get('q');
    if (q !== null && q !== query) {
      setQuery(q);
    }
  }, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['search', query, selectedRegion, selectedCategory, selectedState, selectedLanguage],
    queryFn: () =>
      getSearchNews({
        q: query,
        region: selectedRegion === 'ALL' ? undefined : selectedRegion,
        category: selectedCategory === 'ALL' ? undefined : selectedCategory,
        state: selectedState === 'ALL' ? undefined : selectedState,
        language: selectedLanguage === 'ALL' ? undefined : selectedLanguage,
        limit: 30,
      }),
  });

  const searchResults = React.useMemo(() => {
    return data?.items ? transformApiArticles(data.items) : [];
  }, [data]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams(query.trim() ? { q: query.trim() } : {});
  };

  const handleClearQuery = () => {
    setQuery('');
    setSearchParams({});
  };

  const handleResetFilters = () => {
    setSelectedRegion('ALL');
    setSelectedCategory('ALL');
    setSelectedState('ALL');
    setSelectedLanguage('ALL');
  };

  return (
    <div className="space-y-8 w-full">
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron mb-2">
          <Search className="w-3.5 h-3.5" />
          BharatLens Knowledge Index
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-black text-editorial-ink dark:text-white">
          Search Stored Articles
        </h1>
        <p className="text-sm sm:text-base text-editorial-muted dark:text-gray-400 font-serif mt-1">
          Explore current and historical news stored across national, regional state, and international repositories.
        </p>
      </div>

      {/* Main Search Input */}
      <div className="max-w-4xl mx-auto">
        <SearchBar
          query={query}
          onQueryChange={(val) => {
            setQuery(val);
            setSearchParams(val.trim() ? { q: val.trim() } : {});
          }}
          onSubmit={handleSearchSubmit}
          onClear={handleClearQuery}
        />
      </div>

      {/* Facet Refinement Box */}
      <SearchFilters
        selectedRegion={selectedRegion}
        selectedCategory={selectedCategory}
        selectedState={selectedState}
        selectedLanguage={selectedLanguage}
        onSelectRegion={setSelectedRegion}
        onSelectCategory={setSelectedCategory}
        onSelectState={setSelectedState}
        onSelectLanguage={setSelectedLanguage}
        onReset={handleResetFilters}
      />

      {/* Search Results Display */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-paper-800 pb-3">
          <div className="text-sm font-semibold text-editorial-ink dark:text-white">
            {query.trim() ? (
              <span>
                Results for "<span className="text-bharat-saffron">{query}</span>"
              </span>
            ) : (
              <span>Enter a keyword to query the BharatLens database</span>
            )}
          </div>
          <span className="text-xs text-editorial-muted dark:text-gray-400 font-medium">
            {data?.total ?? 0} {data?.total === 1 ? 'match' : 'matches'} found
          </span>
        </div>

        {isLoading ? (
          <div className="pt-4">
            <GridSkeleton count={4} />
          </div>
        ) : isError ? (
          <ErrorMessage
            title="Unable to execute database search"
            message={error instanceof Error ? error.message : 'Search service connection error.'}
            onRetry={() => refetch()}
          />
        ) : !query.trim() ? (
          <div className="text-center py-16 bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-8 max-w-xl mx-auto shadow-xs">
            <div className="w-12 h-12 rounded-full bg-amber-50 dark:bg-amber-950/40 text-bharat-saffron flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-serif font-bold text-editorial-ink dark:text-white">
              Instant Database Search
            </h3>
            <p className="text-xs sm:text-sm text-editorial-muted dark:text-gray-400 mt-2 font-serif">
              Search by policy, city, state, or key topics such as <strong>"ISRO"</strong>, <strong>"Semiconductor"</strong>, <strong>"Telangana"</strong>, or <strong>"Cricket"</strong>.
            </p>
          </div>
        ) : searchResults.length === 0 ? (
          <div className="text-center py-16 bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-8">
            <Inbox className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <h3 className="text-lg font-serif font-bold text-editorial-ink dark:text-white">
              No matching articles found
            </h3>
            <p className="text-xs text-editorial-muted dark:text-gray-400 mt-1 max-w-sm mx-auto font-serif">
              Try searching with broader terms like "ISRO", "AI", "Semiconductor", "Telangana", or "Cricket".
            </p>
            <button
              onClick={() => {
                handleClearQuery();
                handleResetFilters();
              }}
              className="mt-4 px-4 py-2 bg-bharat-navy text-white text-xs font-semibold rounded-lg hover:bg-bharat-saffron transition-colors"
            >
              Reset Search & Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {searchResults.map((article) => (
              <NewsCard key={article.id} article={article} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
