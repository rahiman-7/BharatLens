import React from 'react';
import { Link } from 'react-router-dom';
import type { StoryArticleSummary } from '../../api/storiesApi';
import { formatTimeAgo, formatFullDate } from '../../utils';
import { Layers, ExternalLink, ShieldCheck, ArrowUpRight } from 'lucide-react';

interface WiderPerspectiveSectionProps {
  currentSourceName: string;
  relatedCoverage: StoryArticleSummary[];
  isLoading?: boolean;
}

export const WiderPerspectiveSection: React.FC<WiderPerspectiveSectionProps> = ({
  currentSourceName,
  relatedCoverage,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="my-10 p-6 bg-stone-50 dark:bg-stone-900/60 rounded-2xl border border-stone-200 dark:border-stone-800 animate-pulse space-y-4">
        <div className="h-6 w-48 bg-stone-200 dark:bg-stone-800 rounded" />
        <div className="h-4 w-64 bg-stone-200 dark:bg-stone-800 rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="h-24 bg-stone-200 dark:bg-stone-800 rounded-xl" />
          <div className="h-24 bg-stone-200 dark:bg-stone-800 rounded-xl" />
        </div>
      </div>
    );
  }

  // If there are no peer coverage articles, don't render an empty bulky block
  if (!relatedCoverage || relatedCoverage.length === 0) {
    return null;
  }

  const allSourceNames = Array.from(
    new Set([currentSourceName, ...relatedCoverage.map((c) => c.source_name)])
  );
  const totalCoverageCount = relatedCoverage.length + 1;

  return (
    <section className="my-10 p-6 sm:p-8 bg-stone-50 dark:bg-stone-900/60 rounded-2xl border border-stone-200 dark:border-stone-800 shadow-xs transition-colors">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-6 border-b border-stone-200 dark:border-stone-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-orange-600 dark:text-orange-400 mb-1">
            <Layers className="w-4 h-4" />
            <span>Story Cluster</span>
          </div>
          <h2 className="text-2xl font-serif font-bold text-stone-900 dark:text-stone-100 tracking-tight">
            See the Wider Perspective
          </h2>
          <p className="text-xs text-stone-600 dark:text-stone-400 mt-1">
            <span className="font-semibold text-stone-800 dark:text-stone-200">{totalCoverageCount} sources</span> covering this development across India and global media.
          </p>
        </div>

        {/* Source Pills Ribbon */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {allSourceNames.map((source, idx) => (
            <span
              key={idx}
              className={`text-[11px] font-medium px-2.5 py-1 rounded-full border transition-colors ${
                source === currentSourceName
                  ? 'bg-orange-600 text-white border-orange-600 font-semibold'
                  : 'bg-white dark:bg-stone-800 text-stone-700 dark:text-stone-300 border-stone-200 dark:border-stone-700'
              }`}
            >
              {source} {source === currentSourceName && '(Current)'}
            </span>
          ))}
        </div>
      </div>

      {/* Coverage Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-6">
        {relatedCoverage.map((item) => (
          <div
            key={item.id}
            className="group relative flex flex-col justify-between p-5 bg-white dark:bg-stone-900 rounded-xl border border-stone-200 dark:border-stone-800 hover:border-orange-300 dark:hover:border-orange-800/80 hover:shadow-md transition-all duration-200 cursor-pointer"
          >
            <Link
              to={`/article/${item.id}`}
              className="block flex-1 flex flex-col justify-between"
            >
              <div>
                {/* Publisher & Timestamp */}
                <div className="flex items-center justify-between gap-2 text-xs text-stone-500 dark:text-stone-400 mb-2">
                  <span className="inline-flex items-center gap-1 font-semibold text-stone-800 dark:text-stone-200">
                    <ShieldCheck className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
                    {item.source_name}
                  </span>
                  <span title={formatFullDate(item.published_at)} className="text-[11px]">
                    {formatTimeAgo(item.published_at)}
                  </span>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    {/* Headline */}
                    <h3 className="block text-base font-serif font-bold text-stone-900 dark:text-stone-100 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors leading-snug">
                      {item.title}
                    </h3>

                    {/* Optional brief snippet */}
                    {item.description && (
                      <p className="mt-2 text-xs text-stone-600 dark:text-stone-400 font-serif line-clamp-2 leading-relaxed">
                        {item.description}
                      </p>
                    )}
                  </div>
                  {item.image_url && (
                    <div className="w-20 h-16 sm:w-24 sm:h-18 rounded-lg overflow-hidden flex-shrink-0 bg-stone-100 dark:bg-stone-800 border border-stone-200 dark:border-stone-800">
                      <img
                        src={item.image_url}
                        alt={item.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </Link>

            {/* Bottom Actions */}
            <div className="mt-4 pt-3 border-t border-stone-100 dark:border-stone-800/80 flex items-center justify-between text-xs z-10">
              <Link
                to={`/article/${item.id}`}
                className="inline-flex items-center gap-1 font-medium text-orange-600 dark:text-orange-400 hover:underline"
              >
                <span>Read Coverage</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>

              {item.canonical_url && (
                <a
                  href={item.canonical_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 transition-colors"
                  title={`Open original article at ${item.source_name}`}
                  onClick={(e) => e.stopPropagation()}
                >
                  <span>Original</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
