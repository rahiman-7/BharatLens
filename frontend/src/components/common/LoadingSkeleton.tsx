import React from 'react';

export const HeroSkeleton: React.FC = () => {
  return (
    <div className="bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl overflow-hidden shadow-sm animate-pulse">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
        <div className="lg:col-span-7 bg-gray-200 dark:bg-paper-800 min-h-[300px] lg:min-h-[440px]" />
        <div className="lg:col-span-5 p-6 sm:p-8 lg:p-10 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="h-5 w-24 bg-gray-200 dark:bg-paper-800 rounded" />
              <div className="h-4 w-32 bg-gray-200 dark:bg-paper-800 rounded" />
            </div>
            <div className="h-8 w-full bg-gray-200 dark:bg-paper-800 rounded" />
            <div className="h-8 w-3/4 bg-gray-200 dark:bg-paper-800 rounded" />
            <div className="space-y-2 pt-2">
              <div className="h-4 w-full bg-gray-200 dark:bg-paper-800 rounded" />
              <div className="h-4 w-5/6 bg-gray-200 dark:bg-paper-800 rounded" />
              <div className="h-4 w-4/6 bg-gray-200 dark:bg-paper-800 rounded" />
            </div>
          </div>
          <div className="pt-4 border-t border-gray-100 dark:border-paper-800 flex justify-between items-center">
            <div className="h-4 w-28 bg-gray-200 dark:bg-paper-800 rounded" />
            <div className="h-4 w-20 bg-gray-200 dark:bg-paper-800 rounded" />
          </div>
        </div>
      </div>
    </div>
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <div className="bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl overflow-hidden shadow-sm animate-pulse flex flex-col justify-between">
      <div>
        <div className="h-48 w-full bg-gray-200 dark:bg-paper-800" />
        <div className="p-5 sm:p-6 space-y-3">
          <div className="flex items-center justify-between">
            <div className="h-4 w-20 bg-gray-200 dark:bg-paper-800 rounded" />
            <div className="h-3 w-16 bg-gray-200 dark:bg-paper-800 rounded" />
          </div>
          <div className="h-5 w-full bg-gray-200 dark:bg-paper-800 rounded" />
          <div className="h-5 w-4/5 bg-gray-200 dark:bg-paper-800 rounded" />
          <div className="h-3 w-full bg-gray-200 dark:bg-paper-800 rounded mt-2" />
          <div className="h-3 w-3/4 bg-gray-200 dark:bg-paper-800 rounded" />
        </div>
      </div>
      <div className="p-5 sm:p-6 pt-0 border-t border-gray-100 dark:border-paper-800 mt-4 flex justify-between items-center">
        <div className="h-4 w-24 bg-gray-200 dark:bg-paper-800 rounded" />
        <div className="h-3 w-16 bg-gray-200 dark:bg-paper-800 rounded" />
      </div>
    </div>
  );
};

export const GridSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 lg:gap-8">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
};
