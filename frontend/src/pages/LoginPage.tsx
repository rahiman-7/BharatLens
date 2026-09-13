import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { LogIn, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  // If already authenticated, redirect
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim() || !password) {
      setErrorMessage('Please enter both your email address and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Invalid email or password. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-[75vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white dark:bg-stone-900 p-8 rounded-2xl border border-stone-200 dark:border-stone-800 shadow-xl">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-orange-100 dark:bg-orange-950/50 text-orange-600 dark:text-orange-400 mb-4">
            <LogIn className="w-7 h-7" />
          </div>
          <h1 className="text-3xl font-serif font-bold text-stone-900 dark:text-stone-100 tracking-tight">
            Welcome Back
          </h1>
          <p className="mt-2 text-sm text-stone-600 dark:text-stone-400">
            Sign in to access your saved bookmarks and reading history
          </p>
        </div>

        {errorMessage && (
          <div className="flex items-center gap-3 p-4 text-sm text-red-700 bg-red-50 dark:bg-red-950/40 dark:text-red-300 rounded-xl border border-red-200 dark:border-red-900/50 animate-fade-in">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p>{errorMessage}</p>
          </div>
        )}

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="login-email"
              className="block text-xs font-semibold uppercase tracking-wider text-stone-700 dark:text-stone-300 mb-1.5"
            >
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-stone-400">
                <Mail className="w-5 h-5" />
              </div>
              <input
                id="login-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="reader@bharatlens.in"
                className="w-full pl-11 pr-4 py-2.5 bg-stone-50 dark:bg-stone-800/60 border border-stone-300 dark:border-stone-700 rounded-xl text-stone-900 dark:text-stone-100 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors text-sm"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="block text-xs font-semibold uppercase tracking-wider text-stone-700 dark:text-stone-300 mb-1.5"
            >
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-stone-400">
                <Lock className="w-5 h-5" />
              </div>
              <input
                id="login-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-11 pr-4 py-2.5 bg-stone-50 dark:bg-stone-800/60 border border-stone-300 dark:border-stone-700 rounded-xl text-stone-900 dark:text-stone-100 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 flex items-center justify-center gap-2 py-3 px-4 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-sm"
          >
            {isSubmitting ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Signing in...
              </span>
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-stone-200 dark:border-stone-800 text-center text-sm text-stone-600 dark:text-stone-400">
          Don't have an account?{' '}
          <Link
            to="/register"
            className="font-medium text-orange-600 dark:text-orange-400 hover:underline inline-flex items-center gap-1"
          >
            Create one now
          </Link>
        </div>
      </div>
    </main>
  );
};
