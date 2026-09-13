import React from 'react';
import type { Article } from '../../types';
import { CompactNewsItem } from './CompactNewsItem';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface EditorialListProps {
  title: string;
  subtitle?: string;
  articles: Article[];
  showIndex?: boolean;
  viewAllLink?: string;
  viewAllText?: string;
}

export const EditorialList: React.FC<EditorialListProps> = ({
  title,
  subtitle,
  articles,
  showIndex = true,
  viewAllLink,
  viewAllText = 'View full section',
}) => {
  return (
    <div className="bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-5 sm:p-6 shadow-sm flex flex-col justify-between">
      <div>
        {/* Header with clean BharatLens accent */}
        <div className="border-b border-gray-200 dark:border-paper-700 pb-3 mb-3 flex items-center justify-between">
          <div>
            <h3 className="font-serif font-black text-lg sm:text-xl text-editorial-ink dark:text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-bharat-saffron rounded-full"></span>
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-editorial-muted dark:text-gray-400 font-serif italic mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        {/* List of articles */}
        <div className="divide-y divide-gray-100 dark:divide-paper-800">
          {articles.map((article, idx) => (
            <CompactNewsItem
              key={article.id}
              article={article}
              index={idx}
              showIndex={showIndex}
            />
          ))}
        </div>
      </div>

      {/* Footer link */}
      {viewAllLink && (
        <div className="pt-3.5 mt-2 border-t border-gray-100 dark:border-paper-800 text-right">
          <Link
            to={viewAllLink}
            className="inline-flex items-center gap-1 text-xs font-semibold text-bharat-navy dark:text-bharat-saffron hover:gap-2 transition-all"
          >
            <span>{viewAllText}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
};
