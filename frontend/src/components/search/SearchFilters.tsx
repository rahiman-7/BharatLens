import React from 'react';
import type { Region, CategorySlug } from '../../types';
import { CATEGORIES, INDIAN_STATES } from '../../data/mockNews';
import { SlidersHorizontal, RotateCcw } from 'lucide-react';
import { INDIAN_LANGUAGES_MAP } from '../../utils';

interface SearchFiltersProps {
  selectedRegion: 'ALL' | Region;
  selectedCategory: 'ALL' | CategorySlug;
  selectedState: 'ALL' | string;
  selectedLanguage?: 'ALL' | string;
  onSelectRegion: (r: 'ALL' | Region) => void;
  onSelectCategory: (c: 'ALL' | CategorySlug) => void;
  onSelectState: (s: 'ALL' | string) => void;
  onSelectLanguage?: (l: 'ALL' | string) => void;
  onReset: () => void;
}

export const SearchFilters: React.FC<SearchFiltersProps> = ({
  selectedRegion,
  selectedCategory,
  selectedState,
  selectedLanguage = 'ALL',
  onSelectRegion,
  onSelectCategory,
  onSelectState,
  onSelectLanguage,
  onReset,
}) => {
  const isFiltered =
    selectedRegion !== 'ALL' ||
    selectedCategory !== 'ALL' ||
    selectedState !== 'ALL' ||
    selectedLanguage !== 'ALL';

  return (
    <div className="bg-white dark:bg-paper-900 border border-editorial-border dark:border-editorial-darkBorder rounded-xl p-5 shadow-xs mb-8 space-y-4">
      <div className="flex items-center justify-between border-b border-gray-100 dark:border-paper-800 pb-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-editorial-ink dark:text-white">
          <SlidersHorizontal className="w-4 h-4 text-bharat-saffron" />
          <span>Refine Search Index</span>
        </div>
        {isFiltered && (
          <button
            onClick={onReset}
            className="flex items-center gap-1 text-xs text-bharat-crimson hover:underline font-medium"
          >
            <RotateCcw className="w-3 h-3" />
            Clear Filters
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {/* Region */}
        <div>
          <label htmlFor="search-scope-filter" className="block text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 mb-1.5">
            Scope / Region:
          </label>
          <select
            id="search-scope-filter"
            value={selectedRegion}
            onChange={(e) => {
              const val = e.target.value as 'ALL' | Region;
              onSelectRegion(val);
              if (val === 'INTERNATIONAL') onSelectState('ALL');
            }}
            className="w-full px-3 py-2 bg-gray-50 dark:bg-paper-800 border border-gray-300 dark:border-paper-700 rounded-lg text-xs text-editorial-ink dark:text-white font-medium focus:ring-2 focus:ring-bharat-saffron focus:outline-none"
          >
            <option value="ALL">All Regions (India & Global)</option>
            <option value="INDIA">India Focus Only</option>
            <option value="INTERNATIONAL">International News Only</option>
          </select>
        </div>

        {/* Category */}
        <div>
          <label htmlFor="search-category-filter" className="block text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 mb-1.5">
            Category:
          </label>
          <select
            id="search-category-filter"
            value={selectedCategory}
            onChange={(e) => onSelectCategory(e.target.value as 'ALL' | CategorySlug)}
            className="w-full px-3 py-2 bg-gray-50 dark:bg-paper-800 border border-gray-300 dark:border-paper-700 rounded-lg text-xs text-editorial-ink dark:text-white font-medium focus:ring-2 focus:ring-bharat-saffron focus:outline-none"
          >
            <option value="ALL">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat.slug} value={cat.slug}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        {/* State */}
        <div>
          <label htmlFor="search-state-filter" className="block text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 mb-1.5">
            State / UT:
          </label>
          <select
            id="search-state-filter"
            value={selectedState}
            disabled={selectedRegion === 'INTERNATIONAL'}
            onChange={(e) => onSelectState(e.target.value)}
            className="w-full px-3 py-2 bg-gray-50 dark:bg-paper-800 border border-gray-300 dark:border-paper-700 rounded-lg text-xs text-editorial-ink dark:text-white font-medium focus:ring-2 focus:ring-bharat-saffron focus:outline-none disabled:opacity-40"
          >
            <option value="ALL">All States & UTs</option>
            {INDIAN_STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Language */}
        <div>
          <label htmlFor="search-language-filter" className="block text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 mb-1.5">
            Language:
          </label>
          <select
            id="search-language-filter"
            value={selectedLanguage}
            onChange={(e) => onSelectLanguage?.(e.target.value)}
            className="w-full px-3 py-2 bg-gray-50 dark:bg-paper-800 border border-gray-300 dark:border-paper-700 rounded-lg text-xs text-editorial-ink dark:text-white font-medium focus:ring-2 focus:ring-bharat-saffron focus:outline-none"
          >
            <option value="ALL">All Languages</option>
            {Object.entries(INDIAN_LANGUAGES_MAP).map(([code, meta]) => (
              <option key={code} value={code}>
                {meta.native} ({meta.en})
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

