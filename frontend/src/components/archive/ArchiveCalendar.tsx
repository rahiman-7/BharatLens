import React, { useRef } from 'react';
import { Calendar, History } from 'lucide-react';
import { formatFullDate } from '../../utils';

interface ArchiveCalendarProps {
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

export const ArchiveCalendar: React.FC<ArchiveCalendarProps> = ({
  selectedDate,
  onSelectDate,
}) => {
  const dateInputRef = useRef<HTMLInputElement>(null);

  // Dynamically compute today and yesterday strings in YYYY-MM-DD
  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  
  const yesterdayDate = new Date();
  yesterdayDate.setDate(yesterdayDate.getDate() - 1);
  const yesterdayStr = `${yesterdayDate.getFullYear()}-${String(yesterdayDate.getMonth() + 1).padStart(2, '0')}-${String(yesterdayDate.getDate()).padStart(2, '0')}`;

  const isToday = selectedDate === todayStr;
  const isYesterday = selectedDate === yesterdayStr;
  const isCustomDate = selectedDate && !isToday && !isYesterday;

  const handleOpenPicker = () => {
    if (dateInputRef.current) {
      if (typeof dateInputRef.current.showPicker === 'function') {
        try {
          dateInputRef.current.showPicker();
        } catch (err) {
          console.warn('showPicker failed, focusing input', err);
          dateInputRef.current.focus();
        }
      } else {
        dateInputRef.current.focus();
      }
    }
  };

  return (
    <div className="bg-white dark:bg-paper-900 border border-editorial-border dark:border-editorial-darkBorder rounded-xl p-6 sm:p-7 shadow-xs">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widestEditorial text-bharat-saffron">
            <History className="w-4 h-4" />
            Historical Archive
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif font-black text-editorial-ink dark:text-white mt-1">
            {selectedDate ? formatFullDate(selectedDate) : 'Select a Publication Date'}
          </h2>
          <p className="text-xs sm:text-sm font-serif italic text-bharat-saffron mt-1">
            "A living archive of the news BharatLens collects."
          </p>
          <p className="text-xs sm:text-sm text-editorial-muted dark:text-gray-400 font-serif mt-1 max-w-2xl leading-relaxed">
            BharatLens continuously stores the news it collects, preserving each article's original publication date so you can explore previously collected stories from the past.
          </p>
        </div>

        {/* Compact Quick Date Selector Controls: [ Today ] [ Yesterday ] [ 📅 Choose a date ] */}
        <div className="flex flex-wrap items-center gap-2.5 sm:gap-3 flex-shrink-0">
          {/* 1. Today Button */}
          <button
            type="button"
            onClick={() => onSelectDate(todayStr)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              isToday
                ? 'bg-bharat-navy text-white dark:bg-bharat-saffron dark:text-white shadow-xs font-semibold ring-2 ring-bharat-saffron/30'
                : 'bg-gray-100 dark:bg-paper-800 text-editorial-ink dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-paper-700 border border-gray-200 dark:border-paper-700'
            }`}
          >
            Today
          </button>

          {/* 2. Yesterday Button */}
          <button
            type="button"
            onClick={() => onSelectDate(yesterdayStr)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              isYesterday
                ? 'bg-bharat-navy text-white dark:bg-bharat-saffron dark:text-white shadow-xs font-semibold ring-2 ring-bharat-saffron/30'
                : 'bg-gray-100 dark:bg-paper-800 text-editorial-ink dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-paper-700 border border-gray-200 dark:border-paper-700'
            }`}
          >
            Yesterday
          </button>

          {/* 3. Choose a Date Button + Date Input with showPicker() */}
          <div className="relative inline-flex items-center">
            <button
              type="button"
              id="choose-date-button"
              onClick={handleOpenPicker}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
                isCustomDate
                  ? 'bg-bharat-navy text-white dark:bg-bharat-saffron dark:text-white border-bharat-navy dark:border-bharat-saffron shadow-xs ring-2 ring-bharat-saffron/30 font-semibold'
                  : 'bg-gray-100 dark:bg-paper-800 text-editorial-ink dark:text-gray-300 border-gray-200 dark:border-paper-700 hover:bg-gray-200 dark:hover:bg-paper-700'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>{isCustomDate ? selectedDate : 'Choose a date'}</span>
            </button>

            <input
              ref={dateInputRef}
              id="archive-date-picker"
              type="date"
              value={selectedDate}
              onChange={(e) => {
                if (e.target.value) {
                  onSelectDate(e.target.value);
                }
              }}
              max={todayStr}
              className="sr-only"
              tabIndex={-1}
              aria-hidden="true"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
