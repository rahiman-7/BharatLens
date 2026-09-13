import React, { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getArchiveNews, getArchiveDates } from '../api/news';
import { transformApiArticles } from '../utils/adapters';
import { ArchiveCalendar } from '../components/archive/ArchiveCalendar';
import { ArchiveFilters } from '../components/archive/ArchiveFilters';
import { NewsCard } from '../components/news/NewsCard';
import { HeroStory } from '../components/news/HeroStory';
import { HeroSkeleton, GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import type { Region, CategorySlug } from '../types';
import { Inbox } from 'lucide-react';
import { formatFullDate } from '../utils';

export const ArchivePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const dateFromUrl = searchParams.get('date');

  // Load available archive dates directly from the database API
  const { data: availableDates = [], isLoading: isDatesLoading } = useQuery({
    queryKey: ['archive', 'dates'],
    queryFn: () => getArchiveDates(30),
  });

  const [selectedDateState, setSelectedDateState] = useState<string>('');
  const [selectedRegion, setSelectedRegion] = useState<'ALL' | Region>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<'ALL' | CategorySlug>('ALL');
  const [selectedState, setSelectedState] = useState<'ALL' | string>('ALL');

  // Dynamic today and yesterday dates
  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  
  const yesterdayDate = new Date();
  yesterdayDate.setDate(yesterdayDate.getDate() - 1);
  const yesterdayStr = `${yesterdayDate.getFullYear()}-${String(yesterdayDate.getMonth() + 1).padStart(2, '0')}-${String(yesterdayDate.getDate()).padStart(2, '0')}`;

  // Automatically default date: URL -> User Pick -> Today (if has articles) -> Yesterday (if has articles) -> Latest available date -> Today
  const selectedDate = useMemo(() => {
    if (selectedDateState) return selectedDateState;
    if (dateFromUrl) return dateFromUrl;
    
    // Check if Today has stored articles
    if (availableDates.some((d) => d.date === todayStr && d.article_count > 0)) {
      return todayStr;
    }
    // Check if Yesterday has stored articles
    if (availableDates.some((d) => d.date === yesterdayStr && d.article_count > 0)) {
      return yesterdayStr;
    }
    // Fall back to latest available stored date
    if (availableDates.length > 0) {
      return availableDates[0].date;
    }
    return todayStr;
  }, [selectedDateState, dateFromUrl, availableDates, todayStr, yesterdayStr]);

  const handleSelectDate = (dateStr: string) => {
    setSelectedDateState(dateStr);
    const next = new URLSearchParams(searchParams);
    next.set('date', dateStr);
    setSearchParams(next);
  };

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['archive', selectedDate, selectedRegion, selectedCategory, selectedState],
    queryFn: () =>
      getArchiveNews({
        date: selectedDate || undefined,
        region: selectedRegion === 'ALL' ? undefined : selectedRegion,
        category: selectedCategory === 'ALL' ? undefined : selectedCategory,
        state: selectedState === 'ALL' ? undefined : selectedState,
        limit: 30,
      }),
    enabled: !!selectedDate,
  });

  const archivedArticles = useMemo(() => {
    return data?.items ? transformApiArticles(data.items) : [];
  }, [data]);

  const handleResetFilters = () => {
    setSelectedRegion('ALL');
    setSelectedCategory('ALL');
    setSelectedState('ALL');
  };

  const leadStory = archivedArticles[0];
  const gridStories = archivedArticles.slice(1);

  return (
    <div className="space-y-10 w-full">
      {/* 1. Archive Time Machine Header & Compact 3-Control Date Picker */}
      <ArchiveCalendar
        selectedDate={selectedDate}
        onSelectDate={handleSelectDate}
      />

      {/* 2. Facet Filters */}
      <ArchiveFilters
        selectedRegion={selectedRegion}
        selectedCategory={selectedCategory}
        selectedState={selectedState}
        onSelectRegion={setSelectedRegion}
        onSelectCategory={setSelectedCategory}
        onSelectState={setSelectedState}
        onReset={handleResetFilters}
      />

      {/* 3. Archive Results Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-paper-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="font-serif font-black text-xl sm:text-2xl text-editorial-ink dark:text-white">
              Archived News for {selectedDate ? formatFullDate(selectedDate) : 'Selected Date'}
            </span>
          </div>
          <span className="text-xs font-semibold text-bharat-saffron bg-amber-50 dark:bg-amber-950/40 px-3.5 py-1 rounded-full border border-amber-200 dark:border-amber-800">
            {data?.total ?? 0} {data?.total === 1 ? 'Article' : 'Articles'} Found
          </span>
        </div>

        {isLoading || isDatesLoading ? (
          <div className="space-y-8">
            <HeroSkeleton />
            <GridSkeleton count={4} />
          </div>
        ) : isError ? (
          <ErrorMessage
            title="Unable to load Historical Archive"
            message={error instanceof Error ? error.message : 'Backend connection error.'}
            onRetry={() => refetch()}
          />
        ) : archivedArticles.length === 0 ? (
          <div className="text-center py-20 bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-8">
            <Inbox className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <h3 className="text-lg font-serif font-bold text-editorial-ink dark:text-white">
              No articles archived for {selectedDate ? formatFullDate(selectedDate) : 'this date'} under current filters
            </h3>
            <p className="text-xs sm:text-sm text-editorial-muted dark:text-gray-400 mt-1 max-w-md mx-auto font-serif">
              Try selecting another date from the available publication dates above or clearing the category/state filters.
            </p>
            <div className="mt-5 flex justify-center gap-3">
              <button
                onClick={handleResetFilters}
                className="px-4 py-2 bg-gray-100 dark:bg-paper-800 text-editorial-ink dark:text-gray-200 text-xs font-medium rounded-lg hover:bg-gray-200 transition-colors cursor-pointer"
              >
                Reset Filters
              </button>
              {availableDates.length > 0 && (
                <button
                  onClick={() => handleSelectDate(availableDates[0].date)}
                  className="px-4 py-2 bg-bharat-navy text-white text-xs font-medium rounded-lg hover:bg-bharat-saffron transition-colors cursor-pointer"
                >
                  Jump to Latest ({availableDates[0].date})
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-10">
            {leadStory && (
              <HeroStory article={leadStory} />
            )}

            {gridStories.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {gridStories.map((article) => (
                  <NewsCard key={article.id} article={article} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
