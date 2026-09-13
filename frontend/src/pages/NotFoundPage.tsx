import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Compass, ArrowLeft, Layers, Home } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <main className="min-h-[70vh] flex items-center justify-center py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full text-center bg-white dark:bg-stone-900 p-8 sm:p-10 rounded-2xl border border-stone-200 dark:border-stone-800 shadow-xl space-y-6">
        {/* Editorial Icon */}
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-100 dark:bg-orange-950/50 text-orange-600 dark:text-orange-400">
          <Compass className="w-8 h-8" />
        </div>

        {/* Headline and Narrative */}
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-orange-600 dark:text-orange-400">
            Error 404
          </span>
          <h1 className="text-3xl sm:text-4xl font-serif font-black text-stone-900 dark:text-stone-100 tracking-tight">
            Story Not Found
          </h1>
          <p className="text-sm text-stone-600 dark:text-stone-400 font-serif leading-relaxed mt-2">
            The page or news dispatch you are looking for has moved, expired, or does not exist in the BharatLens archive.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 text-stone-700 dark:text-stone-300 font-medium rounded-xl text-xs transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back</span>
          </button>

          <Link
            to="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-xl text-xs shadow-sm transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Frontpage</span>
          </Link>

          <Link
            to="/stories"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 border border-stone-200 dark:border-stone-700 hover:border-orange-500 text-stone-700 dark:text-stone-300 hover:text-orange-600 dark:hover:text-orange-400 font-medium rounded-xl text-xs transition-colors"
          >
            <Layers className="w-4 h-4" />
            <span>Story Clusters</span>
          </Link>
        </div>
      </div>
    </main>
  );
};
