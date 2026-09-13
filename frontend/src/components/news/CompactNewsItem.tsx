import React from 'react';
import { Link } from 'react-router-dom';
import type { Article } from '../../types';
import { formatTimeAgo, getCategoryBadgeClasses } from '../../utils';
import { Clock, MapPin } from 'lucide-react';

interface CompactNewsItemProps {
  article: Article;
  index?: number;
  showIndex?: boolean;
}

export const CompactNewsItem: React.FC<CompactNewsItemProps> = ({ article, index, showIndex = false }) => {
  const [imgError, setImgError] = React.useState(false);

  return (
    <article className="group py-3.5 border-b border-gray-100 dark:border-paper-800 last:border-none">
      <Link
        to={`/article/${article.id}`}
        className="flex items-center sm:items-start justify-between gap-3 sm:gap-4 cursor-pointer"
      >
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {showIndex && typeof index === 'number' && (
            <span className="font-serif font-black text-2xl text-gray-300 dark:text-paper-700 group-hover:text-bharat-saffron transition-colors w-7 flex-shrink-0 text-right">
              0{index + 1}
            </span>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 text-[11px]">
              <span className={`px-1.5 py-0.2 rounded font-semibold border ${getCategoryBadgeClasses(article.category)}`}>
                {article.categoryName}
              </span>
              <span className="text-gray-400 dark:text-gray-500">•</span>
              <span className="text-editorial-muted dark:text-gray-400 font-medium truncate">
                {article.source.name}
              </span>
              {article.state && (
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-0.5">
                  <MapPin className="w-2.5 h-2.5 text-bharat-saffron" />
                  {article.state}
                </span>
              )}
            </div>

            <h4 className="font-serif font-semibold text-sm sm:text-base text-editorial-ink dark:text-gray-100 group-hover:text-bharat-indigo dark:group-hover:text-blue-400 transition-colors leading-snug line-clamp-2">
              {article.title}
            </h4>

            <div className="mt-1 flex items-center gap-2 text-[11px] text-editorial-muted dark:text-gray-500">
              <span className="flex items-center gap-1">
                <Clock className="w-2.5 h-2.5" />
                {formatTimeAgo(article.published_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Article Poster / Thumbnail */}
        {article.image_url && !imgError && (
          <div className="w-20 h-16 sm:w-24 sm:h-18 rounded-lg overflow-hidden flex-shrink-0 bg-gray-100 dark:bg-paper-800 border border-gray-100 dark:border-paper-800 self-center sm:self-start">
            <img
              src={article.image_url}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
              onError={() => setImgError(true)}
            />
          </div>
        )}
      </Link>
    </article>
  );
};
