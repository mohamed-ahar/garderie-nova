"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isDark, setIsDark] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check local storage for theme
    const savedTheme = localStorage.getItem('garderie_theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    } else {
      setIsDark(false);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleTheme = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    if (newDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('garderie_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('garderie_theme', 'light');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:8001/api/token/', {
        email: email,
        password: password
      });

      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        router.push('/dashboard');
      }
    } catch (err: any) {
      if (err.response && err.response.status === 401) {
        setError('Courriel ou mot de passe invalide');
      } else {
        setError('Une erreur est survenue. Veuillez réessayer plus tard.');
      }
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen bg-white dark:bg-slate-950 font-sans antialiased text-slate-900 dark:text-white transition-colors duration-300`}>
      
      {/* Top Controls */}
      <div className="fixed top-6 right-6 z-50 flex items-center gap-3">
          <button onClick={toggleTheme} className="p-2.5 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm text-slate-600 dark:text-slate-300 hover:text-brand-600 transition-colors">
              {isDark ? (
                 <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 9H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
              )}
          </button>
      </div>

      <div className="flex min-h-screen">
        {/* Left Side (Hero) */}
        <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-emerald-600 via-green-600 to-green-700 relative flex-col justify-between p-12 overflow-hidden border-r border-green-500/20">
            <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-white/10 rounded-full filter blur-3xl opacity-60"></div>
            <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 bg-black/10 rounded-full filter blur-3xl opacity-30"></div>
            <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-brand-200 dark:bg-brand-900/20 rounded-full filter blur-3xl opacity-70"></div>

            <div className="relative flex items-center gap-3 z-10">
                <div className="flex items-center gap-3 mb-10">
                    <div className="w-11 h-11 bg-white rounded-2xl flex items-center justify-center shadow-2xl text-brand-600">
                        <i className="fa-solid fa-leaf text-2xl"></i>
                    </div>
                    <span className="text-2xl font-black tracking-tighter text-white uppercase italic">GarderieNova</span>
                </div>
            </div>

            <div className="relative z-10">
                <h1 className="text-5xl font-extrabold text-white dark:text-white tracking-tight leading-[1.1] mb-6">
                    <span>Gestion de Garderie</span> <br />
                    <span className="text-green-200">optimisée</span> <span>pour le N.-B.</span>
                </h1>
                <p className="text-sm text-white dark:text-white max-w-md leading-relaxed">
                   Une plateforme complète pour les garderies du Nouveau-Brunswick. Gérez les ratios légaux, les portfolios et l'engagement familial.
                </p>
            </div>

            <div className="relative z-10 flex flex-col gap-4">
                <div className="flex items-center gap-3">
                    <div className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-bold rounded-full uppercase tracking-wider">Conforme Régulation N.-B.</div>
                </div>
                <p className="text-sm font-medium text-white dark:text-slate-400 italic">Approuvé par les centres éducatifs leaders de la province.</p>
            </div>
        </div>

        {/* Right Side (Form) */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8 sm:p-12 md:p-20">
            <div className="w-full max-w-md">

                <div className="mb-10 text-center lg:text-left">
                    <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Connexion Portail</h2>
                    <p className="text-slate-500 dark:text-slate-400 mt-2">Sélectionnez votre rôle pour accéder au tableau de bord.</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-5" autoComplete="on">
                    {error && (
                        <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-2xl text-red-600 dark:text-red-400 text-sm font-bold animate-shake">
                            {error}
                        </div>
                    )}
                    <div>
                        <label htmlFor="email" className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Courriel Professionnel</label>
                        <input 
                            type="email" 
                            id="email" 
                            required 
                            className="w-full px-4 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-brand-500/10 focus:border-brand-500 dark:focus:border-brand-500 outline-none transition-all dark:text-white"
                            placeholder="educator@garderienova.ca"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div>
                        <div className="flex justify-between mb-2">
                            <label htmlFor="password" className="text-sm font-bold text-slate-700 dark:text-slate-300">Mot de passe</label>
                            <a href="#" className="text-sm font-bold text-brand-600 hover:text-brand-700">Mot de passe oublié ?</a>
                        </div>
                        <input 
                            type="password" 
                            id="password" 
                            required 
                            className="w-full px-4 py-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:ring-4 focus:ring-brand-500/10 focus:border-brand-500 dark:focus:border-brand-500 outline-none transition-all dark:text-white"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center">
                            <input type="checkbox" id="remember" className="w-4 h-4 text-brand-600 bg-slate-100 border-slate-300 rounded focus:ring-brand-500" disabled={loading} />
                            <label htmlFor="remember" className="ml-2 text-sm font-medium text-slate-600 dark:text-slate-400">Rester connecté</label>
                        </div>
                    </div>

                    <button 
                        type="submit"
                        disabled={loading}
                        className={`inline-block w-full py-4 ${loading ? 'bg-brand-400 cursor-not-allowed' : 'bg-brand-600 hover:bg-brand-700'} text-white font-bold rounded-2xl shadow-lg shadow-brand-500/25 active:scale-[0.98] transition-all text-center flex items-center justify-center gap-2`}
                    >
                        {loading && (
                            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        )}
                        Accéder au tableau de bord
                    </button>
                </form>

                <p className="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
                    <span>Nouveau centre ? </span>
                    <a href="#" className="font-bold text-brand-600 hover:text-brand-700">Inscrire votre garderie</a>
                </p>
            </div>
        </div>
      </div>
    </div>
  );
}