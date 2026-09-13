import React from 'react';
import { Link } from 'react-router-dom';
import type { Article } from '../../types';
import { formatTimeAgo, getCategoryBadgeClasses, getRegionBadgeClasses } from '../../utils';
import { Clock, MapPin, ArrowRight, ShieldCheck } from 'lucide-react';

interface HeroStoryProps {
  article: Article;
}

export const HeroStory: React.FC<HeroStoryProps> = ({ article }) => {
  const [imgError, setImgError] = React.useState(false);
  const hasValidImage = article.image_url && !imgError;

  return (
    <article className="group relative bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
        {/* Visual Section (7 cols) */}
        <Link
          to={`/article/${article.id}`}
          className="lg:col-span-7 relative overflow-hidden bg-gradient-to-br from-stone-100 via-orange-50/30 to-stone-200 dark:from-stone-900 dark:via-stone-900 dark:to-stone-800 min-h-[280px] sm:min-h-[380px] lg:min-h-[460px] flex items-center justify-center cursor-pointer block"
        >
          {hasValidImage ? (
            <img
              src={article.image_url}
              alt={article.title}
              className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700"
              loading="eager"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="p-8 text-center space-y-3 opacity-40 dark:opacity-30 select-none">
              <span className="font-serif text-5xl sm:text-7xl font-black tracking-widest uppercase text-stone-400 dark:text-stone-600 block">
                {article.source.name.slice(0, 4)}
              </span>
              <span className="text-xs uppercase tracking-widest text-stone-500 font-sans block">
                Editorial Lead Report
              </span>
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent lg:hidden" />
          
          {/* Breaking / Featured Badges */}
          <div className="absolute top-4 left-4 flex flex-wrap items-center gap-2 z-10">
            {article.is_breaking && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-bharat-crimson text-white text-xs font-bold uppercase tracking-wider rounded-full shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                Lead Story
              </span>
            )}
            <span className={`text-xs px-2.5 py-0.5 rounded-full border backdrop-blur-md ${getRegionBadgeClasses(article.region)}`}>
              {article.region === 'INDIA' ? 'India' : 'International'}
            </span>
            {article.state && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-white/95 dark:bg-paper-900/95 text-editorial-ink dark:text-gray-200 border border-gray-200 dark:border-paper-700 flex items-center gap-1 font-medium shadow-xs">
                <MapPin className="w-3 h-3 text-bharat-saffron" />
                {article.state}
              </span>
            )}
          </div>

          {/* Mobile Overlay Source Info */}
          <div className="absolute bottom-4 left-4 lg:hidden text-white text-xs flex items-center gap-2 z-10">
            <span className="font-semibold flex items-center gap-1 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              {article.source.name}
            </span>
            <span className="text-gray-300">•</span>
            <span className="flex items-center gap-1 text-gray-200">
              <Clock className="w-3 h-3" />
              {formatTimeAgo(article.published_at)}
            </span>
          </div>
        </Link>

        {/* Editorial Content Section (5 cols) */}
        <div className="lg:col-span-5 p-6 sm:p-8 lg:p-10 flex flex-col justify-between">
          <div>
            {/* Category & Metadata header */}
            <div className="flex items-center justify-between gap-2 mb-4">
              <Link
                to={`/category/${article.category}`}
                className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${getCategoryBadgeClasses(article.category)} hover:opacity-80 transition-opacity`}
              >
                {article.categoryName}
              </Link>
              <div className="hidden lg:flex items-center gap-2 text-xs text-editorial-muted dark:text-gray-400">
                <span className="font-medium text-editorial-ink dark:text-gray-300">{article.source.name}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTimeAgo(article.published_at)}
                </span>
              </div>
            </div>

            {/* Headline */}
            <Link to={`/article/${article.id}`} className="block group-hover:text-bharat-indigo dark:group-hover:text-blue-400 transition-colors">
              <h2 className="text-2xl sm:text-3xl lg:text-[1.95rem] font-serif font-black text-editorial-ink dark:text-white leading-[1.25] tracking-tight mb-4">
                {article.title}
              </h2>
            </Link>

            {/* Summary */}
            <p className="text-sm sm:text-base text-editorial-muted dark:text-gray-300 font-serif leading-relaxed line-clamp-3 lg:line-clamp-4 mb-6">
              {article.description}
            </p>
          </div>

          {/* Card Footer: Read More and Tags */}
          <div className="pt-5 border-t border-gray-100 dark:border-paper-800 flex items-center justify-between">
            <Link
              to={`/article/${article.id}`}
              className="inline-flex items-center gap-1.5 text-sm font-bold text-bharat-navy dark:text-bharat-saffron hover:gap-2.5 transition-all"
            >
              <span>Read Full Report</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <span className="text-xs text-editorial-muted dark:text-gray-400 font-medium">
              {article.read_time_minutes} min read
            </span>
          </div>
        </div>
      </div>
    </article>
  );
};
