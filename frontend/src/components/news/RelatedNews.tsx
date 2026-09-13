import React from 'react';
import type { Article } from '../../types';
import { NewsCard } from './NewsCard';
import { Layers } from 'lucide-react';

interface RelatedNewsProps {
  articles: Article[];
}

export const RelatedNews: React.FC<RelatedNewsProps> = ({ articles }) => {
  if (!articles || articles.length === 0) return null;

  return (
    <section className="mt-14 pt-8 border-t-2 border-editorial-border dark:border-editorial-darkBorder">
      <div className="flex items-center gap-2 mb-6">
        <Layers className="w-5 h-5 text-bharat-saffron" />
        <h3 className="text-xl font-serif font-bold text-editorial-ink dark:text-white">
          Related & Contextual Coverage
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {articles.slice(0, 3).map((article) => (
          <NewsCard key={article.id} article={article} />
        ))}
      </div>
    </section>
  );
};
