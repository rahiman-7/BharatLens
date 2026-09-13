import React from 'react';
import type { Region, CategorySlug } from '../../types';
import { CATEGORIES, INDIAN_STATES } from '../../data/mockNews';
import { Filter, Globe, RotateCcw } from 'lucide-react';

interface ArchiveFiltersProps {
  selectedRegion: 'ALL' | Region;
  selectedCategory: 'ALL' | CategorySlug;
  selectedState: 'ALL' | string;
  onSelectRegion: (region: 'ALL' | Region) => void;
  onSelectCategory: (category: 'ALL' | CategorySlug) => void;
  onSelectState: (state: 'ALL' | string) => void;
  onReset: () => void;
}

export const ArchiveFilters: React.FC<ArchiveFiltersProps> = ({
  selectedRegion,
  selectedCategory,
  selectedState,
  onSelectRegion,
  onSelectCategory,
  onSelectState,
  onReset,
}) => {
  const isFiltered = selectedRegion !== 'ALL' || selectedCategory !== 'ALL' || selectedState !== 'ALL';

  return (
    <div className="bg-white dark:bg-paper-900 border border-editorial-border dark:border-editorial-darkBorder rounded-xl p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-editorial-ink dark:text-white">
          <Filter className="w-4 h-4 text-bharat-saffron" />
          <span>Filter Archive Stories</span>
        </div>
        {isFiltered && (
          <button
            onClick={onReset}
            className="flex items-center gap-1 text-xs text-bharat-crimson hover:underline font-medium"
          >
            <RotateCcw className="w-3 h-3" />
            Reset Filters
          </button>
        )}
      </div>

      {/* 1. Region Switcher */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 mb-2">
          Scope / Region:
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => {
              onSelectRegion('ALL');
              if (selectedState !== 'ALL') onSelectState('ALL');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              selectedRegion === 'ALL'
                ? 'bg-bharat-navy text-white dark:bg-paper-800 dark:text-bharat-saffron shadow-xs'
                : 'bg-gray-100 dark:bg-paper-800/60 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
            }`}
          >
            All Regions
          </button>
          <button
            onClick={() => onSelectRegion('INDIA')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              selectedRegion === 'INDIA'
                ? 'bg-bharat-saffron text-white shadow-xs'
                : 'bg-gray-100 dark:bg-paper-800/60 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            India Focus
          </button>
          <button
            onClick={() => {
              onSelectRegion('INTERNATIONAL');
              onSelectState('ALL');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              selectedRegion === 'INTERNATIONAL'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-gray-100 dark:bg-paper-800/60 text-gray-700 dark:text-gray-300 hover:bg-gray-200'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            International
          </button>
        </div>
      </div>

      {/* 2. State Filter (Active for India or All) */}
      {selectedRegion !== 'INTERNATIONAL' && (
        <div>
          <label htmlFor="archive-state-filter" className="block text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 mb-1.5">
            Indian State / UT:
          </label>
          <select
            id="archive-state-filter"
            value={selectedState}
            onChange={(e) => onSelectState(e.target.value)}
            className="w-full sm:w-72 px-3 py-1.5 bg-gray-50 dark:bg-paper-800 border border-gray-300 dark:border-paper-700 rounded-lg text-xs text-editorial-ink dark:text-white font-medium focus:ring-2 focus:ring-bharat-saffron focus:outline-none"
          >
            <option value="ALL">All States & Union Territories</option>
            {INDIAN_STATES.map((stateName) => (
              <option key={stateName} value={stateName}>
                {stateName}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* 3. Category Selector */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-widestEditorial text-editorial-muted dark:text-gray-400 mb-2">
          Category:
        </label>
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => onSelectCategory('ALL')}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
              selectedCategory === 'ALL'
                ? 'bg-editorial-ink text-white dark:bg-white dark:text-editorial-ink'
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
                onClick={() => onSelectCategory(cat.slug)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
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
  );
};
