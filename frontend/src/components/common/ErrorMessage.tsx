import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Unable to load stories',
  message = 'We encountered a connection issue fetching the latest reports. Please ensure the backend server is running.',
  onRetry,
}) => {
  return (
    <div className="text-center py-16 bg-white dark:bg-paper-900 border border-gray-200 dark:border-paper-800 rounded-2xl p-8 max-w-xl mx-auto shadow-xs">
      <div className="w-12 h-12 rounded-full bg-rose-50 dark:bg-rose-950/50 text-bharat-crimson flex items-center justify-center mx-auto mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-xl font-serif font-bold text-editorial-ink dark:text-white">
        {title}
      </h3>
      <p className="text-xs sm:text-sm text-editorial-muted dark:text-gray-400 mt-2 font-serif leading-relaxed">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-bharat-navy text-white text-xs font-semibold rounded-lg hover:bg-bharat-saffron transition-colors shadow-xs"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Retry Loading</span>
        </button>
      )}
    </div>
  );
};
