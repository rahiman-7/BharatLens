import React from 'react';
import { Link } from 'react-router-dom';
import { CATEGORIES } from '../../data/mockNews';
import { ShieldCheck, Sparkles, MapPin, Globe, History, ArrowUpRight } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#0B1120] text-gray-300 mt-24 border-t border-slate-800 transition-colors">
      {/* Top Section */}
      <div className="max-w-[1620px] w-[94%] mx-auto px-2 sm:px-4 lg:px-6 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 lg:gap-14">
          {/* Brand & Mission Statement (5 cols) */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-bharat-navy border border-slate-700 text-white flex items-center justify-center font-bold text-base shadow-sm">
                <span className="text-bharat-saffron font-serif">B</span>
              </span>
              <span className="text-2xl font-serif font-black tracking-tight text-white">
                Bharat<span className="text-bharat-saffron">Lens</span>
              </span>
            </div>
            
            <p className="text-xs font-serif italic text-bharat-saffron">
              "News with a wider perspective" — See India. See the World.
            </p>

            <p className="text-xs sm:text-sm text-gray-400 font-serif leading-relaxed max-w-md">
              BharatLens is an India-focused intelligent news aggregator bringing together national, regional state, and international reportage in a clean, distraction-free editorial broadsheet.
            </p>

            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-gray-400 pt-2">
              <span className="flex items-center gap-1.5 text-gray-300">
                <ShieldCheck className="w-4 h-4 text-emerald-400" /> Source-Attributed
              </span>
              <span className="flex items-center gap-1.5 text-gray-300">
                <Sparkles className="w-4 h-4 text-bharat-saffron" /> Zero Forced Onboarding
              </span>
              <span className="flex items-center gap-1.5 text-gray-300">
                <History className="w-4 h-4 text-amber-400" /> Persistent Archive
              </span>
            </div>

            <div className="pt-3 text-xs text-gray-400 font-serif max-w-md">
              <p className="leading-relaxed">
                We continuously store the news we collect, creating a persistent record you can explore by date.
              </p>
              <Link
                to="/archive"
                className="inline-flex items-center gap-1 text-bharat-saffron hover:underline font-sans font-medium mt-1.5 text-xs"
              >
                <span>Explore Archive →</span>
              </Link>
            </div>
          </div>

          {/* Core Sections (3 cols) */}
          <div className="md:col-span-3">
            <h4 className="text-xs font-semibold uppercase tracking-widestEditorial text-white mb-4 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-bharat-saffron"></span>
              Core Sections
            </h4>
            <ul className="space-y-2.5 text-xs sm:text-sm text-gray-400">
              <li>
                <Link to="/" className="hover:text-white transition-colors flex items-center justify-between group">
                  <span>Frontpage Headlines</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-bharat-saffron transition-colors" />
                </Link>
              </li>
              <li>
                <Link to="/india" className="hover:text-white transition-colors flex items-center justify-between group">
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-bharat-saffron" /> India National & States
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-bharat-saffron transition-colors" />
                </Link>
              </li>
              <li>
                <Link to="/international" className="hover:text-white transition-colors flex items-center justify-between group">
                  <span className="flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-blue-400" /> International ("See the World")
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-bharat-saffron transition-colors" />
                </Link>
              </li>
              <li>
                <Link to="/archive" className="hover:text-white transition-colors flex items-center justify-between group">
                  <span className="flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-amber-400" /> Historical Date Archive
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-bharat-saffron transition-colors" />
                </Link>
              </li>
              <li>
                <Link to="/search" className="hover:text-white transition-colors flex items-center justify-between group">
                  <span>Search Stored News</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-bharat-saffron transition-colors" />
                </Link>
              </li>
            </ul>
          </div>

          {/* All 11 Categories (4 cols) */}
          <div className="md:col-span-4">
            <h4 className="text-xs font-semibold uppercase tracking-widestEditorial text-white mb-4 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-bharat-saffron"></span>
              All Categories
            </h4>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-gray-400">
              {CATEGORIES.map((cat) => (
                <Link
                  key={cat.slug}
                  to={`/category/${cat.slug}`}
                  className="hover:text-bharat-saffron transition-colors truncate py-0.5"
                >
                  {cat.name}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom copyright & disclaimer strip */}
        <div className="mt-12 pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row justify-between items-center text-xs text-gray-500 gap-4">
          <p>© {new Date().getFullYear()} BharatLens. All news summaries attributed to respective publishers.</p>
          <div className="flex items-center gap-4">
            <Link to="/" className="hover:text-gray-300 transition-colors">Editorial Guidelines</Link>
            <span>•</span>
            <Link to="/archive" className="hover:text-gray-300 transition-colors">Archive Policy</Link>
            <span>•</span>
            <span className="text-gray-400">See India. See the World.</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
