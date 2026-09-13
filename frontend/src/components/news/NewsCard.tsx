import React from 'react';
import { Link } from 'react-router-dom';
import type { Article } from '../../types';
import { formatTimeAgo, getCategoryBadgeClasses, getRegionBadgeClasses } from '../../utils';
import { Clock, MapPin } from 'lucide-react';

interface NewsCardProps {
  article: Article;
  compact?: boolean;
  borderless?: boolean;
}

export const NewsCard: React.FC<NewsCardProps> = ({ article, compact = false, borderless = false }) => {
  const [imgError, setImgError] = React.useState(false);

  return (
    <article
      className={`group bg-white dark:bg-paper-900 rounded-xl overflow-hidden flex flex-col justify-between transition-all duration-200 cursor-pointer ${
        borderless
          ? 'p-0'
          : 'border border-gray-200/70 dark:border-paper-800 hover:border-gray-300 dark:hover:border-paper-700 hover:shadow-sm'
      }`}
    >
      <Link
        to={`/article/${article.id}`}
        className="flex-1 flex flex-col justify-between block focus:outline-none"
      >
        <div>
          {/* Card Thumbnail */}
          {article.image_url && !imgError && (
            <div className="relative overflow-hidden bg-gray-100 dark:bg-paper-800 aspect-[16/10]">
              <img
                src={article.image_url}
                alt={article.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
                onError={(e) => {
                  e.preventDefault();
                  setImgError(true);
                }}
              />
              <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                <span className={`text-[10px] px-2 py-0.5 rounded-full border backdrop-blur-md ${getRegionBadgeClasses(article.region)}`}>
                  {article.region === 'INDIA' ? 'India' : 'Global'}
                </span>
                {article.state && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/90 dark:bg-paper-900/90 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-paper-700 flex items-center gap-0.5 font-medium">
                    <MapPin className="w-2.5 h-2.5 text-bharat-saffron" />
                    {article.state}
                  </span>
                )}
                {article.language_code && article.language_code !== 'en' && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-600/90 text-white font-medium shadow-xs">
                    {article.language_code.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="p-4 sm:p-5">
            {/* Category & Source Metadata */}
            <div className="flex items-center justify-between text-xs mb-2">
              <span
                className={`font-semibold px-2 py-0.5 rounded text-[11px] border ${getCategoryBadgeClasses(article.category)}`}
              >
                {article.categoryName}
              </span>
              <span className="text-editorial-muted dark:text-gray-400 font-medium text-[11px] truncate max-w-[120px]">
                {article.source.name}
              </span>
            </div>

            {/* Headline */}
            <h3 className={`font-serif font-bold text-editorial-ink dark:text-white group-hover:text-bharat-indigo dark:group-hover:text-blue-400 transition-colors leading-snug line-clamp-2 ${compact ? 'text-sm sm:text-base' : 'text-base sm:text-lg'}`}>
              {article.title}
            </h3>

            {/* Summary */}
            {!compact && (
              <p className="mt-2 text-xs sm:text-sm text-editorial-muted dark:text-gray-300 font-serif leading-relaxed line-clamp-2">
                {article.description}
              </p>
            )}
          </div>
        </div>

        {/* Card Footer */}
        <div className="px-4 sm:px-5 py-3 border-t border-gray-100 dark:border-paper-800/80 flex items-center justify-between text-xs text-editorial-muted dark:text-gray-400">
          <span className="flex items-center gap-1 text-[11px]">
            <Clock className="w-3 h-3" />
            {formatTimeAgo(article.published_at)}
          </span>
          <span className="text-[11px] font-medium">
            {article.read_time_minutes} min read
          </span>
        </div>
      </Link>
    </article>
  );
};
