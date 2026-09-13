import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBookmarksApi, removeBookmarkApi } from '../api/bookmarksApi';
import { transformApiArticles } from '../utils/adapters';
import { useAuth } from '../auth/AuthContext';
import { NewsCard } from '../components/news/NewsCard';
import { GridSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { Bookmark, BookmarkX, LogIn, ArrowLeft, Newspaper } from 'lucide-react';

export const BookmarksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated, user } = useAuth();
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['user-bookmarks', page],
    queryFn: () => getBookmarksApi(page, 20),
    enabled: isAuthenticated,
  });

  const removeMutation = useMutation({
    mutationFn: (articleId: number) => removeBookmarkApi(articleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-bookmarks'] });
      queryClient.invalidateQueries({ queryKey: ['bookmark-status'] });
    },
  });

  const articles = React.useMemo(() => {
    return data?.items ? transformApiArticles(data.items) : [];
  }, [data]);

  if (!isAuthenticated) {
    return (
      <main className="min-h-[70vh] flex items-center justify-center py-16 px-4">
        <div className="max-w-md w-full text-center bg-white dark:bg-stone-900 p-8 rounded-2xl border border-stone-200 dark:border-stone-800 shadow-xl space-y-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-100 dark:bg-orange-950/50 text-orange-600 dark:text-orange-400">
            <Bookmark className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-serif font-bold text-stone-900 dark:text-stone-100">
              Sign In to View Bookmarks
            </h1>
            <p className="text-sm text-stone-600 dark:text-stone-400">
              Save articles from across India and the world to read later in your personal collection.
            </p>
          </div>
          <div className="pt-2 flex flex-col gap-3">
            <Link
              to="/login"
              state={{ from: { pathname: '/bookmarks' } }}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-xl shadow-sm transition-colors text-sm"
            >
              <LogIn className="w-4 h-4" />
              <span>Sign In</span>
            </Link>
            <Link
              to="/register"
              className="w-full py-2.5 px-4 text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 rounded-xl transition-colors text-sm font-medium"
            >
              Create Account
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl">
      {/* Header Banner */}
      <div className="mb-8 pb-6 border-b border-stone-200 dark:border-stone-800 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-orange-600 dark:text-orange-400 mb-1.5">
            <Bookmark className="w-4 h-4" />
            <span>Saved Stories</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-serif font-bold text-stone-900 dark:text-stone-100 tracking-tight">
            Your Bookmarks
          </h1>
          <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
            {data?.total ? `${data.total} article${data.total === 1 ? '' : 's'} saved for ${user?.email}` : 'Your personal saved articles collection'}
          </p>
        </div>

        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-stone-600 dark:text-stone-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Top Stories</span>
        </Link>
      </div>

      {/* Content */}
      {isLoading ? (
        <GridSkeleton count={6} />
      ) : isError ? (
        <ErrorMessage
          message={error instanceof Error ? error.message : 'Failed to load your bookmarks.'}
          onRetry={() => refetch()}
        />
      ) : articles.length === 0 ? (
        <div className="py-20 text-center bg-stone-50 dark:bg-stone-900/40 rounded-2xl border border-dashed border-stone-300 dark:border-stone-800 max-w-lg mx-auto p-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-stone-200 dark:bg-stone-800 text-stone-400 mb-4">
            <Newspaper className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-serif font-bold text-stone-800 dark:text-stone-200">
            No Bookmarks Yet
          </h2>
          <p className="mt-2 text-sm text-stone-500 dark:text-stone-400">
            While reading any article on BharatLens, click the bookmark button to save it here for later reading.
          </p>
          <Link
            to="/"
            className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-xl shadow-sm text-sm transition-colors"
          >
            <span>Explore News</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {articles.map((article) => (
              <div key={article.id} className="relative group">
                <NewsCard article={article} />
                <button
                  onClick={() => removeMutation.mutate(Number(article.id))}
                  title="Remove bookmark"
                  className="absolute top-3 right-3 p-2 rounded-full bg-white/90 dark:bg-stone-900/90 hover:bg-red-50 dark:hover:bg-red-950/50 text-stone-500 hover:text-red-600 shadow-md backdrop-blur-sm border border-stone-200 dark:border-stone-700 transition-colors z-10 cursor-pointer"
                >
                  <BookmarkX className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-8 border-t border-stone-200 dark:border-stone-800">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-4 py-2 rounded-xl border border-stone-300 dark:border-stone-700 text-sm font-medium text-stone-700 dark:text-stone-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-stone-500 dark:text-stone-400">
                Page {page} of {data.total_pages}
              </span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="px-4 py-2 rounded-xl border border-stone-300 dark:border-stone-700 text-sm font-medium text-stone-700 dark:text-stone-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </main>
  );
};
