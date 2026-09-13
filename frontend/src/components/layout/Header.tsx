import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { Search, Calendar, Moon, Sun, Globe2, Bookmark, User as UserIcon, LogIn, LogOut } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';

interface HeaderProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

// Verified live Indian languages for top navigation
const TOP_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'mr', label: 'मराठी' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'ml', label: 'മലയാളം' },
  { code: 'gu', label: 'ગુજરાતી' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
] as const;

export const Header: React.FC<HeaderProps> = ({ darkMode, toggleDarkMode }) => {
  const [currentDateStr, setCurrentDateStr] = useState('');
  const [quickSearch, setQuickSearch] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, user, logout } = useAuth();

  useEffect(() => {
    const now = new Date();
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone: 'Asia/Kolkata',
    };
    setCurrentDateStr(new Intl.DateTimeFormat('en-IN', options).format(now));
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickSearch.trim()) {
      navigate(`/search?q=${encodeURIComponent(quickSearch.trim())}`);
      setQuickSearch('');
    }
  };

  // Determine currently active language from query params if on India page, else default to 'en'
  const isIndiaPage = location.pathname === '/india';
  const currentLangParam = searchParams.get('language');
  const activeLangCode = isIndiaPage ? (currentLangParam || 'en') : (currentLangParam || '');

  const handleLanguageSelect = (langCode: string) => {
    const newParams = new URLSearchParams();
    if (isIndiaPage) {
      const currentState = searchParams.get('state');
      const currentCategory = searchParams.get('category');
      if (currentState && currentState !== 'ALL') newParams.set('state', currentState);
      if (currentCategory && currentCategory !== 'ALL') newParams.set('category', currentCategory);
    }
    if (langCode !== 'en' || isIndiaPage) {
      newParams.set('language', langCode);
    }
    navigate(`/india?${newParams.toString()}`);
  };

  return (
    <header className="border-b border-editorial-border dark:border-editorial-darkBorder bg-white/90 dark:bg-paper-900/90 backdrop-blur-md sticky top-0 z-40 transition-colors">
      {/* Top utility ticker strip with editorial language navigation */}
      <div className="border-b border-gray-100 dark:border-paper-800 py-1.5 px-3 sm:px-6 lg:px-8 text-xs text-editorial-muted dark:text-gray-400">
        <div className="max-w-[1620px] w-[94%] mx-auto flex flex-col md:flex-row items-center justify-between gap-2">
          {/* Left Edition & Date */}
          <div className="flex items-center gap-2.5 sm:gap-3 flex-shrink-0">
            <span className="font-medium text-editorial-ink dark:text-gray-200 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Edition: <span className="text-bharat-saffron font-semibold">India & Global</span>
            </span>
            <span className="hidden xl:inline text-gray-300 dark:text-gray-700 select-none">|</span>
            <span className="hidden xl:inline">{currentDateStr || 'New Delhi, India'}</span>
          </div>

          {/* Center: Top Regional Language Navigation (Indian Express editorial style) */}
          <nav aria-label="Regional languages" className="overflow-x-auto no-scrollbar py-0.5 max-w-full flex items-center gap-1 sm:gap-1.5 text-xs">
            {TOP_LANGUAGES.map((lang, index) => {
              const isActive = activeLangCode === lang.code;
              return (
                <React.Fragment key={lang.code}>
                  {index > 0 && (
                    <span className="text-gray-300 dark:text-gray-700 select-none text-[11px] px-0.5">|</span>
                  )}
                  <button
                    type="button"
                    onClick={() => handleLanguageSelect(lang.code)}
                    title={`View news in ${lang.label}`}
                    className={`whitespace-nowrap px-1 py-0.5 rounded transition-all cursor-pointer ${
                      isActive
                        ? 'text-bharat-saffron dark:text-bharat-saffron font-bold underline decoration-bharat-saffron decoration-2 underline-offset-4'
                        : 'text-editorial-muted dark:text-gray-400 hover:text-editorial-ink dark:hover:text-gray-200 hover:underline font-medium'
                    }`}
                  >
                    {lang.label}
                  </button>
                </React.Fragment>
              );
            })}
          </nav>

          {/* Right: Utility actions */}
          <div className="flex items-center gap-2.5 sm:gap-3 flex-shrink-0">
            <Link 
              to="/archive" 
              className="flex items-center gap-1.5 text-editorial-ink dark:text-gray-300 hover:text-bharat-saffron dark:hover:text-bharat-saffron transition-colors font-medium"
            >
              <Calendar className="w-3.5 h-3.5 text-bharat-saffron" />
              <span>Date Archive</span>
            </Link>

            <span className="text-gray-300 dark:text-gray-700 select-none">|</span>

            {/* Auth Section */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2 sm:gap-2.5">
                <Link
                  to="/bookmarks"
                  className="flex items-center gap-1 text-editorial-ink dark:text-gray-300 hover:text-bharat-saffron dark:hover:text-bharat-saffron transition-colors font-medium"
                >
                  <Bookmark className="w-3.5 h-3.5 text-bharat-saffron" />
                  <span>Bookmarks</span>
                </Link>
                <span className="text-gray-300 dark:text-gray-700 select-none">|</span>
                <span className="hidden sm:inline-flex items-center gap-1 font-medium text-stone-600 dark:text-stone-300 max-w-[120px] truncate" title={user?.email}>
                  <UserIcon className="w-3 h-3 text-stone-400" />
                  <span className="truncate">{user?.email.split('@')[0]}</span>
                </span>
                <button
                  onClick={logout}
                  title="Sign Out"
                  aria-label="Sign Out"
                  className="flex items-center gap-1 text-red-600 dark:text-red-400 hover:underline cursor-pointer font-medium"
                >
                  <LogOut className="w-3 h-3" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 sm:gap-2.5">
                <Link
                  to="/login"
                  className="flex items-center gap-1 text-editorial-ink dark:text-gray-300 hover:text-bharat-saffron dark:hover:text-bharat-saffron transition-colors font-medium"
                >
                  <LogIn className="w-3.5 h-3.5 text-bharat-saffron" />
                  <span>Sign In</span>
                </Link>
                <span className="text-gray-300 dark:text-gray-700 select-none">|</span>
                <Link
                  to="/register"
                  className="text-bharat-saffron hover:underline font-semibold"
                >
                  Register
                </Link>
              </div>
            )}

            <span className="text-gray-300 dark:text-gray-700 select-none">|</span>
            <button
              onClick={toggleDarkMode}
              aria-label="Toggle dark mode"
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-paper-800 text-gray-600 dark:text-gray-300 transition-colors cursor-pointer"
            >
              {darkMode ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Main Masthead */}
      <div className="max-w-[1620px] w-[94%] mx-auto px-2 sm:px-4 lg:px-6 py-4 sm:py-6 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left tagline / quick link */}
        <div className="hidden lg:flex items-center gap-2 text-xs text-editorial-muted dark:text-gray-400 max-w-xs">
          <Globe2 className="w-4 h-4 text-bharat-indigo dark:text-blue-400 flex-shrink-0" />
          <span>Independent, contextual news aggregation for a modern India.</span>
        </div>

        {/* Center Masthead Brand */}
        <div className="text-center">
          <Link to="/" className="inline-block group">
            <div className="flex items-center justify-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-bharat-navy text-white flex items-center justify-center font-bold text-lg shadow-sm group-hover:scale-105 transition-transform">
                <span className="text-bharat-saffron font-serif">B</span>
              </span>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-black tracking-tight text-editorial-ink dark:text-white">
                Bharat<span className="text-bharat-saffron">Lens</span>
              </h1>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-editorial-muted dark:text-gray-400 font-serif italic tracking-wide">
              "News with a wider perspective" — See India. See the World.
            </p>
          </Link>
        </div>

        {/* Right Search Input */}
        <form onSubmit={handleSearchSubmit} role="search" aria-label="Quick News Search" className="w-full sm:w-auto relative">
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Search headlines, states, topics..."
              aria-label="Search headlines, states, topics"
              value={quickSearch}
              onChange={(e) => setQuickSearch(e.target.value)}
              className="w-full sm:w-64 lg:w-72 pl-9 pr-4 py-1.5 text-sm bg-gray-50 dark:bg-paper-800 border border-editorial-border dark:border-editorial-darkBorder rounded-full focus:outline-none focus:ring-2 focus:ring-bharat-saffron/50 dark:text-white transition-all placeholder:text-gray-400"
            />
            <Search className="w-4 h-4 text-gray-400 absolute left-3 pointer-events-none" />
          </div>
        </form>
      </div>
    </header>
  );
};
