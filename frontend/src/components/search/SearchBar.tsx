import React from 'react';
import { Search, X } from 'lucide-react';

interface SearchBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClear: () => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  query,
  onQueryChange,
  onSubmit,
  onClear,
}) => {
  return (
    <form onSubmit={onSubmit} role="search" aria-label="Database News Search" className="relative w-full">
      <div className="relative flex items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          aria-label="Search articles by headline, topic, or source"
          placeholder="Search stored database by headline, keywords, topic, or source..."
          className="w-full pl-12 pr-12 py-3.5 bg-white dark:bg-paper-900 border-2 border-editorial-border dark:border-editorial-darkBorder rounded-xl text-base text-editorial-ink dark:text-white font-medium placeholder:text-gray-400 focus:outline-none focus:border-bharat-saffron dark:focus:border-bharat-saffron shadow-sm transition-all"
        />
        <Search className="w-5 h-5 text-gray-400 absolute left-4 pointer-events-none" />
        {query && (
          <button
            type="button"
            onClick={onClear}
            aria-label="Clear search input"
            className="p-1 rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 absolute right-4 hover:bg-gray-100 dark:hover:bg-paper-800"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </form>
  );
};
