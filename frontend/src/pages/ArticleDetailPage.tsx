import React from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getArticle, getLatestNews } from '../api/news';
import { getRelatedCoverage } from '../api/storiesApi';
import { getBookmarkStatusApi, addBookmarkApi, removeBookmarkApi } from '../api/bookmarksApi';
import { transformApiArticleToArticle, transformApiArticles } from '../utils/adapters';
import { RelatedNews } from '../components/news/RelatedNews';
import { WiderPerspectiveSection } from '../components/news/WiderPerspectiveSection';
import { formatFullDate, getCategoryBadgeClasses, getRegionBadgeClasses } from '../utils';
import { useAuth } from '../auth/AuthContext';
import { useReadingTracker } from '../hooks/useReadingTracker';
import { ArrowLeft, Clock, MapPin, ExternalLink, ShieldCheck, Share2, Bookmark, BookmarkCheck } from 'lucide-react';

export const ArticleDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();

  const numericId = id ? Number(id) : undefined;
  const [imgError, setImgError] = React.useState(false);

  // Scroll to top and reset image error on article change
  React.useEffect(() => {
    window.scrollTo(0, 0);
    setImgError(false);
  }, [id]);

  // Track dwell time & view interaction
  useReadingTracker(numericId);

  const {
    data: apiArticle,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['article', id],
    queryFn: () => getArticle(id || ''),
    enabled: !!id,
    retry: false,
  });

  // Bookmark status query
  const { data: bookmarkData } = useQuery({
    queryKey: ['bookmark-status', numericId],
    queryFn: () => getBookmarkStatusApi(numericId!),
    enabled: isAuthenticated && !!numericId,
  });

  const isBookmarked = bookmarkData?.is_bookmarked ?? false;

  const bookmarkMutation = useMutation({
    mutationFn: () => {
      if (isBookmarked) {
        return removeBookmarkApi(numericId!);
      } else {
        return addBookmarkApi(numericId!);
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['bookmark-status', numericId], data);
      queryClient.invalidateQueries({ queryKey: ['user-bookmarks'] });
    },
  });

  const handleBookmarkToggle = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: location } });
      return;
    }
    bookmarkMutation.mutate();
  };

  const article = React.useMemo(() => {
    return apiArticle ? transformApiArticleToArticle(apiArticle) : null;
  }, [apiArticle]);


  // Fetch related articles by category
  const { data: relatedData } = useQuery({
    queryKey: ['news', 'related', article?.category],
    queryFn: () =>
      getLatestNews({
        category: article?.category,
        limit: 4,
      }),
    enabled: !!article?.category,
  });

  const relatedArticles = React.useMemo(() => {
    if (!relatedData?.items) return [];
    return transformApiArticles(
      relatedData.items.filter((item) => String(item.id) !== id)
    ).slice(0, 3);
  }, [relatedData, id]);

  // Fetch story group multi-source coverage ("See the wider perspective")
  const { data: relatedCoverage, isLoading: isRelatedCoverageLoading } = useQuery({
    queryKey: ['article-related-coverage', numericId],
    queryFn: () => getRelatedCoverage(numericId!),
    enabled: !!numericId,
  });

  const handleShare = () => {
    if (!article) return;
    if (navigator.share) {
      navigator
        .share({
          title: article.title,
          text: article.description,
          url: window.location.href,
        })
        .catch(() => {});
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Article link copied to clipboard!');
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-pulse">
        <div className="h-6 w-32 bg-gray-200 dark:bg-paper-800 rounded" />
        <div className="h-10 w-full bg-gray-200 dark:bg-paper-800 rounded" />
        <div className="h-10 w-4/5 bg-gray-200 dark:bg-paper-800 rounded" />
        <div className="h-6 w-3/4 bg-gray-200 dark:bg-paper-800 rounded" />
        <div className="h-72 w-full bg-gray-200 dark:bg-paper-800 rounded-xl" />
        <div className="space-y-3">
          <div className="h-4 w-full bg-gray-200 dark:bg-paper-800 rounded" />
          <div className="h-4 w-full bg-gray-200 dark:bg-paper-800 rounded" />
          <div className="h-4 w-2/3 bg-gray-200 dark:bg-paper-800 rounded" />
        </div>
      </div>
    );
  }

  if (isError || !article) {
    return (
      <div className="text-center py-20 bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-8 max-w-xl mx-auto shadow-xs">
        <h2 className="text-2xl font-serif font-bold text-editorial-ink dark:text-white">
          Article Not Found
        </h2>
        <p className="text-sm text-editorial-muted dark:text-gray-400 mt-2 font-serif">
          {error instanceof Error && !error.message.includes('404')
            ? error.message
            : 'The requested news story could not be found in the BharatLens database.'}
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="px-5 py-2.5 bg-gray-100 dark:bg-paper-800 text-editorial-ink dark:text-gray-200 text-xs font-semibold rounded-lg hover:bg-gray-200 transition-colors"
          >
            Go Back
          </button>
          <Link
            to="/"
            className="px-5 py-2.5 bg-bharat-navy text-white text-xs font-semibold rounded-lg hover:bg-bharat-saffron transition-colors"
          >
            Return to Frontpage
          </Link>
        </div>
      </div>
    );
  }

  return (
    <article className="max-w-4xl mx-auto">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center justify-between gap-4 mb-6 pb-4 border-b border-gray-200 dark:border-paper-800 text-xs">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-editorial-muted dark:text-gray-400 hover:text-bharat-saffron transition-colors font-medium cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Feed</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={handleBookmarkToggle}
            title={isBookmarked ? 'Remove from bookmarks' : 'Bookmark this story'}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
              isBookmarked
                ? 'bg-orange-100 dark:bg-orange-950/60 text-orange-700 dark:text-orange-300 border border-orange-300 dark:border-orange-800'
                : 'bg-gray-100 dark:bg-paper-800 hover:bg-gray-200 dark:hover:bg-paper-700 text-editorial-ink dark:text-gray-200'
            }`}
          >
            {isBookmarked ? (
              <>
                <BookmarkCheck className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
                <span>Saved</span>
              </>
            ) : (
              <>
                <Bookmark className="w-3.5 h-3.5" />
                <span>Bookmark</span>
              </>
            )}
          </button>

          <button
            onClick={handleShare}
            className="flex items-center gap-1 px-3 py-1 bg-gray-100 dark:bg-paper-800 rounded-md hover:bg-gray-200 dark:hover:bg-paper-700 text-editorial-ink dark:text-gray-200 transition-colors cursor-pointer"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Share</span>
          </button>
        </div>

      </div>

      {/* Category, Region & State Badges */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <Link
          to={`/category/${article.category}`}
          className={`text-xs font-semibold px-2.5 py-0.5 rounded border ${getCategoryBadgeClasses(article.category)} hover:opacity-80 transition-opacity`}
        >
          {article.categoryName}
        </Link>
        <span className={`text-xs px-2.5 py-0.5 rounded-full border ${getRegionBadgeClasses(article.region)}`}>
          {article.region === 'INDIA' ? 'India' : 'International'}
        </span>
        {article.state && (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-gray-100 dark:bg-paper-800 text-editorial-ink dark:text-gray-200 border border-gray-200 dark:border-paper-700 flex items-center gap-1 font-medium">
            <MapPin className="w-3 h-3 text-bharat-saffron" />
            {article.state}
          </span>
        )}
      </div>

      {/* Main Headline */}
      <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-black text-editorial-ink dark:text-white leading-tight tracking-tight mb-6">
        {article.title}
      </h1>

      {/* Summary / Sub-headline Deck */}
      <p className="text-lg sm:text-xl text-editorial-muted dark:text-gray-300 font-serif leading-relaxed mb-6 font-normal">
        {article.description}
      </p>

      {/* Metadata Strip: Author, Source, Date */}
      <div className="flex flex-wrap items-center justify-between gap-4 py-3.5 px-4 bg-gray-50 dark:bg-paper-900 border-y border-gray-200 dark:border-paper-800 rounded-lg mb-8 text-xs text-editorial-muted dark:text-gray-400">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-bharat-navy text-white flex items-center justify-center font-bold text-xs">
            {article.author ? article.author.charAt(0) : article.source.name.charAt(0)}
          </div>
          <div>
            {article.author && (
              <span className="font-semibold text-editorial-ink dark:text-gray-200 block">
                {article.author}
              </span>
            )}
            <span className="flex items-center gap-1 text-[11px]">
              <ShieldCheck className="w-3 h-3 text-emerald-500" />
              Source: <span className="font-medium text-editorial-ink dark:text-gray-300">{article.source.name}</span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-right">
          <div>
            <span className="block font-medium text-editorial-ink dark:text-gray-200">
              {formatFullDate(article.published_at)}
            </span>
            <span className="text-[11px] flex items-center justify-end gap-1">
              <Clock className="w-3 h-3" />
              {article.read_time_minutes} min read • BharatLens Archive
            </span>
          </div>
        </div>
      </div>

      {/* Hero Visual Image */}
      {article.image_url && !imgError && (
        <figure className="mb-8 rounded-xl overflow-hidden bg-gray-100 dark:bg-paper-800 border border-gray-200/80 dark:border-paper-800">
          <img
            src={article.image_url}
            alt={article.title}
            className="w-full h-auto max-h-[500px] object-cover"
            onError={() => setImgError(true)}
          />
          <figcaption className="p-3 text-xs text-editorial-muted dark:text-gray-400 font-serif italic bg-white dark:bg-paper-900 border-t border-gray-100 dark:border-paper-800 flex justify-between">
            <span>Visual reportage for {article.title}</span>
            <span>Source: {article.source.name}</span>
          </figcaption>
        </figure>
      )}

      {/* Article Editorial Summary Body */}
      <div className="prose dark:prose-invert max-w-none text-base sm:text-lg text-editorial-ink dark:text-gray-200 font-serif leading-relaxed space-y-5">
        <p className="drop-cap">
          {article.description}
        </p>
      </div>

      {/* Prominent Original Publisher Link Callout (Respecting Copyright & Source) */}
      <div className="mt-10 p-6 bg-paper-100 dark:bg-paper-900 border-2 border-dashed border-gray-300 dark:border-paper-700 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-editorial-ink dark:text-white flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Independent Source Attribution
          </h4>
          <p className="text-xs text-editorial-muted dark:text-gray-400 font-serif mt-0.5">
            BharatLens aggregates verified summaries. Read the complete story directly at the original publisher.
          </p>
        </div>
        {article.canonical_url && article.canonical_url.trim() !== '' && (
          <a
            href={article.canonical_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-bharat-navy text-white hover:bg-bharat-saffron text-xs font-semibold rounded-lg shadow-sm transition-all whitespace-nowrap cursor-pointer"
          >
            <span>Read Full Story</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      {/* Multi-Source Story Grouping ("See the wider perspective") */}
      <WiderPerspectiveSection
        currentSourceName={article.source.name}
        relatedCoverage={relatedCoverage || []}
        isLoading={isRelatedCoverageLoading}
      />

      {/* Related Stories */}
      {relatedArticles.length > 0 && (
        <RelatedNews articles={relatedArticles} />
      )}
    </article>
  );
};
