import type { CategorySlug, Region } from '../types';

export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    }).format(date);
  } catch {
    return dateString;
  }
}

export function formatFullDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(date);
  } catch {
    return dateString;
  }
}

export function formatTimeAgo(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date('2026-09-10T18:00:00Z'); // normalized reference
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours <= 0) return 'Just now';
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays} days ago`;
  } catch {
    return 'Recently';
  }
}

export function getCategoryBadgeClasses(category: CategorySlug): string {
  const map: Record<CategorySlug, string> = {
    politics: 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800',
    sports: 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800',
    technology: 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800',
    business: 'bg-indigo-50 text-indigo-800 border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800',
    'movies-entertainment': 'bg-fuchsia-50 text-fuchsia-800 border-fuchsia-200 dark:bg-fuchsia-950/40 dark:text-fuchsia-300 dark:border-fuchsia-800',
    education: 'bg-cyan-50 text-cyan-800 border-cyan-200 dark:bg-cyan-950/40 dark:text-cyan-300 dark:border-cyan-800',
    science: 'bg-violet-50 text-violet-800 border-violet-200 dark:bg-violet-950/40 dark:text-violet-300 dark:border-violet-800',
    health: 'bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800',
    lifestyle: 'bg-orange-50 text-orange-800 border-orange-200 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-800',
    crime: 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800',
    environment: 'bg-teal-50 text-teal-800 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800',
  };
  return map[category] || 'bg-gray-100 text-gray-800 border-gray-200';
}

export function getRegionBadgeClasses(region: Region): string {
  if (region === 'INDIA') {
    return 'bg-bharat-saffron/10 text-bharat-saffron font-medium border-bharat-saffron/30';
  }
  return 'bg-blue-100 text-blue-800 font-medium border-blue-200 dark:bg-blue-900/40 dark:text-blue-300';
}

export const INDIAN_LANGUAGES_MAP: Record<string, { en: string; native: string }> = {
  hi: { en: 'Hindi', native: 'हिन्दी' },
  te: { en: 'Telugu', native: 'తెలుగు' },
  ta: { en: 'Tamil', native: 'தமிழ்' },
  kn: { en: 'Kannada', native: 'ಕನ್ನಡ' },
  ml: { en: 'Malayalam', native: 'മലയാളം' },
  mr: { en: 'Marathi', native: 'मराठी' },
  bn: { en: 'Bengali', native: 'বাংলা' },
  gu: { en: 'Gujarati', native: 'ગુજરાતી' },
  pa: { en: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
  or: { en: 'Odia', native: 'ଓଡ଼ିଆ' },
  ur: { en: 'Urdu', native: 'اردو' },
  as: { en: 'Assamese', native: 'অসমীয়া' },
  en: { en: 'English', native: 'English' },
};

export function getLanguageNativeName(code?: string | null): string {
  if (!code) return 'English';
  const clean = code.trim().toLowerCase();
  return INDIAN_LANGUAGES_MAP[clean]?.native || clean.toUpperCase();
}

export function getLanguageEnglishName(code?: string | null): string {
  if (!code) return 'English';
  const clean = code.trim().toLowerCase();
  return INDIAN_LANGUAGES_MAP[clean]?.en || clean.toUpperCase();
}

