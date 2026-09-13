import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Navigation } from './components/layout/Navigation';
import { Footer } from './components/layout/Footer';

// Pages
import { HomePage } from './pages/HomePage';
import { IndiaPage } from './pages/IndiaPage';
import { InternationalPage } from './pages/InternationalPage';
import { CategoryPage } from './pages/CategoryPage';
import { ArticleDetailPage } from './pages/ArticleDetailPage';
import { ArchivePage } from './pages/ArchivePage';
import { SearchPage } from './pages/SearchPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { BookmarksPage } from './pages/BookmarksPage';
import { ForYouPage } from './pages/ForYouPage';
import { StoriesPage } from './pages/StoriesPage';
import { StoryDetailPage } from './pages/StoryDetailPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { AuthProvider } from './auth/AuthContext';

// Scroll to top helper
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('bharatlens_theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('bharatlens_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('bharatlens_theme', 'light');
    }
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode((prev) => !prev);

  return (
    <AuthProvider>
      <Router>
        <ScrollToTop />
        <div className="min-h-screen flex flex-col bg-paper-50 dark:bg-paper-950 text-editorial-ink dark:text-gray-100 transition-colors duration-200">
          {/* Masthead & Main Ticker */}
          <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />

          {/* Section Navigation & Category Ribbon */}
          <Navigation />

          {/* Main Content Viewport with Wide Responsive Container */}
          <main className="flex-1 max-w-[1620px] w-[94%] mx-auto px-2 sm:px-4 lg:px-6 py-8 sm:py-12">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/india" element={<IndiaPage />} />
              <Route path="/international" element={<InternationalPage />} />
              <Route path="/category/:slug" element={<CategoryPage />} />
              <Route path="/article/:id" element={<ArticleDetailPage />} />
              <Route path="/archive" element={<ArchivePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/bookmarks" element={<BookmarksPage />} />
              <Route path="/for-you" element={<ForYouPage />} />
              <Route path="/stories" element={<StoriesPage />} />
              <Route path="/stories/:id" element={<StoryDetailPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </main>

          {/* Footnote & Standards */}
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;

