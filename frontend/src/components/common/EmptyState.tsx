import React from 'react';
import { FileQuestion } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No stories found',
  message = 'There are currently no reports stored matching this criteria.',
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div className="text-center py-16 bg-white dark:bg-paper-900 border border-gray-200/80 dark:border-paper-800 rounded-2xl p-8 max-w-xl mx-auto shadow-xs">
      <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-paper-800 text-gray-400 flex items-center justify-center mx-auto mb-4">
        {icon || <FileQuestion className="w-6 h-6" />}
      </div>
      <h3 className="text-lg font-serif font-bold text-editorial-ink dark:text-white">
        {title}
      </h3>
      <p className="text-xs sm:text-sm text-editorial-muted dark:text-gray-400 mt-2 font-serif leading-relaxed">
        {message}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-6 inline-flex items-center px-4 py-2 bg-bharat-navy text-white text-xs font-semibold rounded-lg hover:bg-bharat-saffron transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
