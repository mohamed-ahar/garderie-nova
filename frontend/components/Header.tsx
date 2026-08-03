"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '../lib/axios';

interface User {
  full_name: string;
  role_display: string;
  email: string;
}

export default function Header({ toggleSidebar }: { toggleSidebar: () => void }) {
  const router = useRouter();
  const [time, setTime] = useState('');
  const [date, setDate] = useState('');
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check local storage for theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    } else {
      setIsDark(false);
      document.documentElement.classList.remove('dark');
    }

    const fetchUser = async () => {
      try {
        const response = await api.get('/api/me/');
        setUser(response.data);
      } catch (error) {
        console.error('Error fetching user:', error);
      }
    };

    fetchUser();

    const updateClock = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString());
      setDate(now.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSignOut = (e: React.MouseEvent) => {
    e.preventDefault();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/login');
  };

  const toggleTheme = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    if (newDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-slate-200 dark:border-slate-800/60">
        <div className="flex items-center justify-between px-6 md:px-10 py-3 border-b border-slate-100 dark:border-slate-800/40">
            
            {/* Left Section: Toggle & Title */}
            <div className="flex items-center gap-6">
                 <button onClick={toggleSidebar} className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-emerald-500 transition-colors shadow-sm">
                    <i className="fa-solid fa-bars"></i>
                 </button>

                <div className="hidden md:flex flex-col relative">
                    <div className="flex ml-16 items-center gap-2 mb-0.5">
                        <div className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></span>
                        </div>
                        <span className="text-[9px] font-black uppercase tracking-[0.2em] text-emerald-700/70 dark:text-emerald-400/80">
                            {date}
                        </span>
                    </div>
                    <div className="flex ml-16 items-center gap-4 group/header">
                        <div className="flex flex-col">
                            <h2 className="text-2xl font-black text-slate-800 dark:text-slate-100 tracking-tighter leading-none flex items-center gap-2">
                                <span className="relative">
                                    Main
                                    <span className="absolute -bottom-1.5 left-0 w-0 h-[3px] bg-slate-800 dark:bg-slate-200 rounded-full transition-all duration-500 group-hover/header:w-full"></span>
                                </span>
                                <span className="bg-gradient-to-r from-slate-900 via-slate-600 to-slate-400 dark:from-white dark:via-slate-300 dark:to-slate-500 bg-clip-text text-transparent drop-shadow-sm">
                                    Dashboard
                                </span>
                            </h2>
                            <p className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.25em] mt-2 ml-0.5">
                                GarderieNova Management System
                            </p>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100/80 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 rounded-xl transition-all duration-300 hover:bg-slate-200 dark:hover:bg-slate-700/60">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-slate-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-slate-500 dark:bg-slate-400"></span>
                            </span>
                            <span className="text-[10px] font-black text-slate-600 dark:text-slate-300 tracking-tighter uppercase">
                                v1.0.0
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Section: Clock, Theme, User */}
            <div className="flex items-center gap-4">
                <div className="hidden xl:flex items-center gap-4 px-5 py-2 rounded-2xl bg-white/50 dark:bg-slate-900/40 backdrop-blur-md border border-slate-200/60 dark:border-emerald-500/10 shadow-[0_4px_15px_rgba(0,0,0,0.05)] group/clock transition-all hover:border-emerald-500/30">
                    <div className="relative flex items-center justify-center w-2 h-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-40"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                    </div>
                    <div className="flex flex-col items-start border-l border-slate-200 dark:border-white/10 pl-3">
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] font-black text-slate-500 dark:text-emerald-400/80 uppercase tracking-[0.2em] leading-none">
                                Live Terminal
                            </span>
                            <span className="text-[7px] font-bold px-1 rounded bg-slate-200 dark:bg-emerald-500/20 text-slate-600 dark:text-emerald-300 border border-transparent dark:border-emerald-500/20">
                                AST
                            </span>
                        </div>
                        <span className="font-mono font-black text-base tabular-nums text-slate-900 dark:text-white tracking-tighter mt-1">
                            {time}
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-1.5 bg-slate-100/50 dark:bg-slate-900/50 p-1 rounded-xl border border-slate-200 dark:border-slate-800">
                    <button onClick={toggleFullScreen} className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:text-emerald-500 transition-all active:scale-90 group shadow-sm">
                        <i className="fa-solid fa-expand text-slate-500 text-xs"></i>
                    </button>
                    <button onClick={toggleTheme} className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:text-emerald-500 transition-all active:scale-90 group shadow-sm">
                        {isDark ? (
                            <i className="fa-solid fa-sun text-amber-400 text-xs"></i>
                        ) : (
                            <i className="fa-solid fa-moon text-slate-500 text-xs"></i>
                        )}
                    </button>
                </div>

                <div className="relative">
                    <button onClick={() => setUserMenuOpen(!userMenuOpen)} className="flex items-center gap-3 p-1 pr-3 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-emerald-500/50 transition-all shadow-sm group">
                        <div className="relative">
                            <img src="https://img.icons8.com/?size=100&id=11781&format=png&color=40C057" className="w-8 h-8 rounded-xl bg-emerald-50 p-0.5 object-cover" alt="User" />
                            <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 border-2 border-white dark:border-slate-800 rounded-full"></div>
                        </div>
                        <div className="hidden sm:block text-left">
                            <p className="text-[11px] font-bold text-slate-800 dark:text-slate-100 leading-tight">{user ? user.full_name : 'Loading...'}</p>
                            <p className="text-[9px] text-emerald-600 dark:text-emerald-400 font-medium uppercase tracking-tighter">{user ? user.role_display : '...'}</p>
                        </div>
                        <i className="fa-solid fa-chevron-down text-[8px] text-slate-400 group-hover:translate-y-0.5 transition-transform"></i>
                    </button>

                    {userMenuOpen && (
                        <div className="absolute right-0 mt-3 w-64 bg-white dark:bg-slate-900 rounded-[1.5rem] border border-slate-200 dark:border-emerald-500/20 shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-5 duration-200">
                            <div className="p-5 bg-gradient-to-br from-slate-50 to-white dark:from-emerald-950/20 dark:to-slate-900 border-b border-slate-100 dark:border-slate-800">
                                <p className="text-sm font-black text-slate-800 dark:text-white">{user ? user.full_name : 'Loading...'}</p>
                                <p className="text-xs text-slate-500 dark:text-emerald-400/60">{user ? user.email : '...'}</p>
                            </div>
                            <div className="p-2.5">
                                <a href="#" className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 hover:text-emerald-600 dark:hover:text-emerald-400 rounded-xl transition-colors group">
                                    <i className="fa-solid fa-user-circle text-lg opacity-40 group-hover:opacity-100"></i> Profile
                                </a>
                                <div className="my-2 border-t border-slate-100 dark:border-slate-800"></div>
                                <button onClick={handleSignOut} className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-xl transition-colors">
                                    <i className="fa-solid fa-power-off"></i> Sign Out
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>

        {/* Bottom Nav Section */}
        <div className="px-6 md:px-10 py-2 flex items-center justify-center bg-slate-50/50 dark:bg-slate-800/20 hidden">
            <nav className="flex items-center gap-2 md:gap-3 p-2 bg-slate-900/90 backdrop-blur-2xl rounded-[2rem] border border-slate-800 shadow-[0_20px_50px_rgba(0,0,0,0.4)] overflow-hidden max-w-full">
                <a href="#" className="relative flex items-center gap-3 md:gap-4 px-5 md:px-8 py-3 rounded-[1.5rem] bg-gradient-to-br from-emerald-500 to-emerald-700 text-white shadow-[0_10px_20px_rgba(16,185,129,0.3)] group/nav overflow-hidden shrink-0 transition-transform active:scale-95">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover/nav:animate-[shimmer_2s_infinite]"></div>
                    <div className="relative w-9 h-9 md:w-11 md:h-11 flex items-center justify-center rounded-2xl bg-white/20 backdrop-blur-md border border-white/40 shadow-inner group-hover:rotate-6 transition-transform duration-500">
                        <i className="fa-solid fa-graduation-cap text-sm md:text-base text-white"></i>
                    </div>
                    <div className="hidden sm:flex flex-col items-start leading-tight relative z-10">
                        <span className="text-[11px] md:text-[13px] font-black uppercase tracking-wider text-white">Table Center</span>
                        <span className="text-[8px] md:text-[9px] font-bold text-white flex items-center gap-1.5 uppercase tracking-tighter">
                            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span>Management Center
                        </span>
                    </div>
                </a>
                
                <button className="flex items-center gap-3 md:gap-4 px-4 md:px-7 py-3 rounded-[1.5rem] text-white hover:bg-slate-800/80 transition-all duration-500 group border border-transparent hover:border-slate-700">
                    <div className="w-9 h-9 md:w-11 md:h-11 flex items-center justify-center rounded-2xl bg-slate-800 group-hover:bg-emerald-500 group-hover:text-white transition-all duration-500 shadow-sm border border-slate-700">
                        <i className="fa-solid fa-user-tie text-sm text-slate-200 group-hover:text-white"></i>
                    </div>
                    <div className="hidden sm:flex flex-col items-start leading-tight text-left">
                        <span className="text-[11px] md:text-[13px] font-extrabold uppercase tracking-wide text-white group-hover:text-emerald-400 transition-colors">Table Staff</span>
                    </div>
                </button>

                <div className="hidden md:block h-10 w-px bg-slate-800 mx-2"></div>

                <a href="#" className="relative flex items-center justify-center w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-slate-800 text-white hover:bg-emerald-500 transition-all duration-500 group shadow-sm shrink-0 border border-slate-700">
                    <div className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-rose-500 text-white text-[9px] font-black flex items-center justify-center rounded-full border-2 border-slate-900 shadow-lg group-hover:scale-110 transition-transform">2</div>
                    <i className="fa-solid fa-bell text-sm"></i>
                </a>
            </nav>
        </div>
    </header>
  );
}