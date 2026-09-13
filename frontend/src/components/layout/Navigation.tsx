import { NavLink, useLocation } from 'react-router-dom';
import { CATEGORIES } from '../../data/mockNews';
import type { CategorySlug } from '../../types';
import {
  Sparkles as SparklesNav,
  Layers,
  Globe,
  MapPin,
  History,
  Search,
  Compass,
  Landmark,
  Trophy,
  Cpu,
  Briefcase,
  Clapperboard,
  GraduationCap,
  FlaskConical,
  HeartPulse,
  Sparkles,
  ShieldAlert,
  Leaf,
  type LucideIcon,
} from 'lucide-react';

interface CategoryStyleConfig {
  icon: LucideIcon;
  inactiveClasses: string;
  iconColor: string;
}

const CATEGORY_STYLE_MAP: Record<CategorySlug, CategoryStyleConfig> = {
  politics: {
    icon: Landmark,
    inactiveClasses: 'bg-amber-50/70 dark:bg-amber-950/30 text-amber-900 dark:text-amber-300 border-amber-200/70 dark:border-amber-900/50 hover:bg-amber-100 dark:hover:bg-amber-950/50',
    iconColor: 'text-amber-700 dark:text-amber-400',
  },
  sports: {
    icon: Trophy,
    inactiveClasses: 'bg-emerald-50/70 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-300 border-emerald-200/70 dark:border-emerald-900/50 hover:bg-emerald-100 dark:hover:bg-emerald-950/50',
    iconColor: 'text-emerald-700 dark:text-emerald-400',
  },
  technology: {
    icon: Cpu,
    inactiveClasses: 'bg-blue-50/70 dark:bg-blue-950/30 text-blue-900 dark:text-blue-300 border-blue-200/70 dark:border-blue-900/50 hover:bg-blue-100 dark:hover:bg-blue-950/50',
    iconColor: 'text-blue-700 dark:text-blue-400',
  },
  business: {
    icon: Briefcase,
    inactiveClasses: 'bg-indigo-50/70 dark:bg-indigo-950/30 text-indigo-900 dark:text-indigo-300 border-indigo-200/70 dark:border-indigo-900/50 hover:bg-indigo-100 dark:hover:bg-indigo-950/50',
    iconColor: 'text-indigo-700 dark:text-indigo-400',
  },
  'movies-entertainment': {
    icon: Clapperboard,
    inactiveClasses: 'bg-fuchsia-50/70 dark:bg-fuchsia-950/30 text-fuchsia-900 dark:text-fuchsia-300 border-fuchsia-200/70 dark:border-fuchsia-900/50 hover:bg-fuchsia-100 dark:hover:bg-fuchsia-950/50',
    iconColor: 'text-fuchsia-700 dark:text-fuchsia-400',
  },
  education: {
    icon: GraduationCap,
    inactiveClasses: 'bg-purple-50/70 dark:bg-purple-950/30 text-purple-900 dark:text-purple-300 border-purple-200/70 dark:border-purple-900/50 hover:bg-purple-100 dark:hover:bg-purple-950/50',
    iconColor: 'text-purple-700 dark:text-purple-400',
  },
  science: {
    icon: FlaskConical,
    inactiveClasses: 'bg-cyan-50/70 dark:bg-cyan-950/30 text-cyan-900 dark:text-cyan-300 border-cyan-200/70 dark:border-cyan-900/50 hover:bg-cyan-100 dark:hover:bg-cyan-950/50',
    iconColor: 'text-cyan-700 dark:text-cyan-400',
  },
  health: {
    icon: HeartPulse,
    inactiveClasses: 'bg-rose-50/70 dark:bg-rose-950/30 text-rose-900 dark:text-rose-300 border-rose-200/70 dark:border-rose-900/50 hover:bg-rose-100 dark:hover:bg-rose-950/50',
    iconColor: 'text-rose-700 dark:text-rose-400',
  },
  lifestyle: {
    icon: Sparkles,
    inactiveClasses: 'bg-orange-50/70 dark:bg-orange-950/30 text-orange-900 dark:text-orange-300 border-orange-200/70 dark:border-orange-900/50 hover:bg-orange-100 dark:hover:bg-orange-950/50',
    iconColor: 'text-orange-700 dark:text-orange-400',
  },
  crime: {
    icon: ShieldAlert,
    inactiveClasses: 'bg-slate-100/80 dark:bg-slate-900/40 text-slate-800 dark:text-slate-300 border-slate-200/80 dark:border-slate-800/60 hover:bg-slate-200/80 dark:hover:bg-slate-800/60',
    iconColor: 'text-slate-700 dark:text-slate-400',
  },
  environment: {
    icon: Leaf,
    inactiveClasses: 'bg-teal-50/70 dark:bg-teal-950/30 text-teal-900 dark:text-teal-300 border-teal-200/70 dark:border-teal-900/50 hover:bg-teal-100 dark:hover:bg-teal-950/50',
    iconColor: 'text-teal-700 dark:text-teal-400',
  },
};

export const Navigation: React.FC = () => {
  const location = useLocation();

  const primaryNavItems = [
    { label: 'Frontpage', path: '/', icon: SparklesNav },
    { label: 'For You', path: '/for-you', icon: Sparkles },
    { label: 'Story Clusters', path: '/stories', icon: Layers },
    { label: 'India Spotlight', path: '/india', icon: MapPin },
    { label: 'International', path: '/international', icon: Globe },
    { label: 'Historical Archive', path: '/archive', icon: History },
    { label: 'Search Index', path: '/search', icon: Search },
  ];

  return (
    <nav className="border-b border-editorial-border dark:border-editorial-darkBorder bg-white dark:bg-paper-900 sticky top-[97px] z-30 shadow-xs transition-colors">
      <div className="max-w-[1620px] w-[94%] mx-auto px-2 sm:px-4 lg:px-6">
        {/* Tier 1: Main Section Tabs */}
        <div className="flex items-center justify-between overflow-x-auto no-scrollbar py-2 border-b border-gray-100 dark:border-paper-800 text-sm font-medium gap-1 sm:gap-2">
          <div className="flex items-center gap-1 sm:gap-2">
            {primaryNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs sm:text-sm whitespace-nowrap transition-all ${
                    isActive
                      ? 'bg-bharat-navy text-white dark:bg-paper-800 dark:text-bharat-saffron font-semibold shadow-xs'
                      : 'text-editorial-muted dark:text-gray-400 hover:text-editorial-ink dark:hover:text-white hover:bg-gray-50 dark:hover:bg-paper-800/50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-bharat-saffron' : 'text-gray-400'}`} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        </div>

        {/* Tier 2: Category Ribbon with Soft Pastel Tints & High-Visibility Active Highlighting */}
        <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto no-scrollbar py-2.5 text-xs">
          <span className="font-semibold text-editorial-muted dark:text-gray-400 uppercase tracking-widestEditorial text-[10px] whitespace-nowrap flex items-center gap-1 mr-1">
            <Compass className="w-3 h-3 text-bharat-saffron" />
            Categories:
          </span>
          {CATEGORIES.map((cat) => {
            const isCatActive = location.pathname === `/category/${cat.slug}`;
            const styleConfig = CATEGORY_STYLE_MAP[cat.slug] || {
              icon: Compass,
              inactiveClasses: 'bg-gray-100 text-gray-800 border-gray-200',
              iconColor: 'text-gray-600',
            };
            const CatIcon = styleConfig.icon;

            return (
              <NavLink
                key={cat.slug}
                to={`/category/${cat.slug}`}
                className={`whitespace-nowrap px-2.5 sm:px-3 py-1 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 border ${
                  isCatActive
                    ? 'bg-bharat-saffron text-white border-bharat-saffron font-bold shadow-xs ring-2 ring-bharat-saffron/40 scale-[1.03]'
                    : `${styleConfig.inactiveClasses} transition-transform hover:scale-[1.01]`
                }`}
              >
                <CatIcon className={`w-3.5 h-3.5 flex-shrink-0 ${isCatActive ? 'text-white' : styleConfig.iconColor}`} />
                <span>{cat.name}</span>
              </NavLink>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
