import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getLatestNews } from '../api/news';
import { transformApiArticles } from '../utils/adapters';
import { CATEGORIES } from '../data/mockNews';
import { HeroStory } from '../components/news/HeroStory';
import { NewsCard } from '../components/news/NewsCard';
import { EditorialList } from '../components/news/EditorialList';
import { CompactNewsItem } from '../components/news/CompactNewsItem';
import { HeroSkeleton, GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { Globe, MapPin, Sparkles, ArrowRight, Compass, History } from 'lucide-react';

export const HomePage: React.FC = () => {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['news', 'latest'],
    queryFn: () => getLatestNews({ limit: 30 }),
  });

  const articles = React.useMemo(() => {
    return data?.items ? transformApiArticles(data.items) : [];
  }, [data]);

  // 1. Primary Featured Lead Hero Article (prefer INDIA region)
  const heroArticle = articles.find((a) => a.region === 'INDIA') || articles[0];
  
  // 2. Top 5 Briefs for the right-hand column
  const topBriefs = heroArticle
    ? articles.filter((a) => a.id !== heroArticle.id && a.region === 'INDIA').slice(0, 5)
    : [];

  // 3. India News spotlight
  const indiaStories = heroArticle
    ? articles.filter((a) => a.region === 'INDIA' && a.id !== heroArticle.id)
    : [];
  const indiaSubLead = indiaStories[0];
  const indiaSecondaryGrid = indiaStories.slice(1, 3);
  const indiaSideBriefs = indiaStories.slice(3, 7);

  // 4. International ("See the World")
  const internationalArticles = articles.filter((a) => a.region === 'INTERNATIONAL').slice(0, 3);

  if (isLoading) {
    return (
      <div className="space-y-16">
        <HeroSkeleton />
        <div className="pt-8 border-t border-gray-200 dark:border-paper-800">
          <div className="h-8 w-48 bg-gray-200 dark:bg-paper-800 rounded mb-8 animate-pulse" />
          <GridSkeleton count={4} />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorMessage
        title="Unable to load BharatLens Frontpage"
        message={error instanceof Error ? error.message : 'Backend connection error.'}
        onRetry={() => refetch()}
      />
    );
  }

  if (articles.length === 0) {
    return (
      <EmptyState
        title="No stories currently in repository"
        message="The database is currently empty. Run the seed script to populate sample editorial news."
      />
    );
  }

  return (
    <div className="space-y-16 sm:space-y-20">
      {/* ================= SECTION 1: Featured Hero & Top Briefs ================= */}
      {heroArticle && (
        <section>
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 xl:gap-12 items-start">
            {/* Main Lead Story (8 cols) */}
            <div className="lg:col-span-8">
              <div className="flex items-center justify-between mb-3.5">
                <span className="text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  Featured Editorial Lead
                </span>
                <span className="text-xs text-editorial-muted dark:text-gray-400">
                  Live backend feed
                </span>
              </div>
              <HeroStory article={heroArticle} />
            </div>

            {/* Right Column: Top 5 Editorial Briefs (4 cols) */}
            <div className="lg:col-span-4">
              <EditorialList
                title="Top Quick Briefs"
                subtitle="Essential national & regional developments"
                articles={topBriefs.length > 0 ? topBriefs : articles.slice(1, 5)}
                showIndex={true}
                viewAllLink="/india"
                viewAllText="Explore all India news"
              />
            </div>
          </div>
        </section>
      )}

      {/* ================= SECTION 2: India Spotlight (Asymmetric Broadsheet) ================= */}
      <section className="pt-8 border-t border-gray-200 dark:border-paper-800">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron">
              <MapPin className="w-4 h-4" />
              National & State Pulse
            </div>
            <h2 className="text-2xl sm:text-3xl font-serif font-black text-editorial-ink dark:text-white mt-1">
              India Focus
            </h2>
            <p className="text-xs sm:text-sm text-editorial-muted dark:text-gray-400 font-serif mt-1">
              Deep reportage spanning governance, state infrastructure, and scientific breakthroughs.
            </p>
          </div>
          <Link
            to="/india"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-bharat-navy dark:text-bharat-saffron hover:gap-2.5 transition-all self-start sm:self-auto bg-gray-100 dark:bg-paper-800 px-3.5 py-1.5 rounded-lg"
          >
            <span>Filter by 28 States</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Asymmetric broadsheet layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-start">
          {/* Sub-lead with prominent presence */}
          {indiaSubLead ? (
            <div className="lg:col-span-7">
              <NewsCard article={indiaSubLead} />
            </div>
          ) : (
            <div className="lg:col-span-7">
              {articles[0] && <NewsCard article={articles[0]} />}
            </div>
          )}

          {/* Supporting India stories stack */}
          <div className="lg:col-span-5 bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-5 sm:p-6 lg:p-7 shadow-sm divide-y divide-gray-100 dark:divide-paper-800">
            <h3 className="font-serif font-bold text-base text-editorial-ink dark:text-white mb-3 pb-2 border-b border-gray-100 dark:border-paper-800">
              State & Regional Highlights
            </h3>
            {(indiaSecondaryGrid.concat(indiaSideBriefs).length > 0
              ? indiaSecondaryGrid.concat(indiaSideBriefs)
              : articles.slice(1, 5)
            ).slice(0, 4).map((story) => (
              <CompactNewsItem key={story.id} article={story} />
            ))}
          </div>
        </div>
      </section>

      {/* ================= SECTION 3: "See the World" — International Perspective ================= */}
      {internationalArticles.length > 0 && (
        <section className="bg-gradient-to-br from-slate-900 via-[#0E172A] to-blue-950 text-white rounded-2xl p-6 sm:p-10 lg:p-12 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="relative z-10">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 pb-6 border-b border-white/10 gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-blue-300">
                  <Globe className="w-4 h-4" />
                  Global Perspective
                </div>
                <h2 className="text-2xl sm:text-3xl font-serif font-black text-white mt-1">
                  "See the World" — International News
                </h2>
                <p className="text-xs sm:text-sm text-blue-100/70 font-serif mt-1">
                  Curated international diplomacy, space science, and global economic transformations.
                </p>
              </div>
              <Link
                to="/international"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-200 hover:text-white hover:gap-2.5 transition-all self-start sm:self-auto bg-white/10 px-4 py-2 rounded-lg backdrop-blur-xs"
              >
                <span>View International Section</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
              {internationalArticles.map((article) => (
                <div key={article.id} className="bg-white/5 border border-white/10 rounded-xl p-5 sm:p-6 backdrop-blur-xs flex flex-col justify-between hover:bg-white/10 transition-colors">
                  <div>
                    <div className="flex items-center justify-between text-xs text-blue-300 mb-3">
                      <span className="font-semibold uppercase tracking-wider">{article.categoryName}</span>
                      <span className="text-gray-400">{article.source.name}</span>
                    </div>
                    <Link to={`/article/${article.id}`} className="block group">
                      <h3 className="font-serif font-bold text-base sm:text-lg text-white group-hover:text-blue-200 transition-colors line-clamp-2 leading-snug">
                        {article.title}
                      </h3>
                    </Link>
                    <p className="mt-2 text-xs sm:text-sm text-gray-300 line-clamp-3 font-serif leading-relaxed">
                      {article.description}
                    </p>
                  </div>
                  <div className="mt-5 pt-3 border-t border-white/10 flex items-center justify-between text-[11px] text-gray-400">
                    <span>{article.read_time_minutes} min read</span>
                    <Link to={`/article/${article.id}`} className="text-blue-300 hover:text-white font-medium flex items-center gap-1">
                      <span>Read Summary</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ================= SECTION 4: Historical Archive Feature Callout ================= */}
      <section className="bg-amber-50/50 dark:bg-paper-800/50 border border-amber-200/60 dark:border-paper-700 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-1.5 max-w-2xl">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron">
            <History className="w-4 h-4" />
            Your news, preserved.
          </div>
          <p className="font-serif text-sm sm:text-base text-editorial-ink dark:text-gray-200 leading-relaxed">
            BharatLens continuously stores the news it collects, so you can look back at what was reported on earlier days.
          </p>
        </div>
        <Link
          to="/archive"
          className="inline-flex items-center gap-2 text-xs sm:text-sm font-bold text-bharat-navy dark:text-bharat-saffron hover:gap-3 transition-all whitespace-nowrap bg-white dark:bg-paper-900 border border-editorial-border dark:border-editorial-darkBorder px-4 py-2.5 rounded-xl shadow-2xs hover:shadow-xs"
        >
          <span>Explore Historical Archive</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      {/* ================= SECTION 5: Clean Taxonomy Explorer ================= */}
      <section className="pt-8 border-t border-gray-200 dark:border-paper-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron">
              <Compass className="w-4 h-4" />
              Taxonomy Explorer
            </div>
            <h2 className="text-2xl font-serif font-bold text-editorial-ink dark:text-white mt-1">
              Browse by Category
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3.5 sm:gap-4">
          {CATEGORIES.map((cat) => {
            const articleCount = articles.filter((a) => a.category === cat.slug).length;
            return (
              <Link
                key={cat.slug}
                to={`/category/${cat.slug}`}
                className="group bg-white dark:bg-paper-900 border border-gray-200/70 dark:border-paper-800 rounded-xl p-4 hover:border-bharat-saffron dark:hover:border-bharat-saffron hover:shadow-xs transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <h3 className="font-serif font-bold text-sm text-editorial-ink dark:text-white group-hover:text-bharat-saffron transition-colors">
                      {cat.name}
                    </h3>
                    <span className="text-[10px] font-semibold text-editorial-muted dark:text-gray-400 bg-gray-100 dark:bg-paper-800 px-2 py-0.5 rounded-full">
                      {articleCount}
                    </span>
                  </div>
                  <p className="text-xs text-editorial-muted dark:text-gray-400 line-clamp-2 leading-relaxed">
                    {cat.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
};
