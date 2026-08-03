"use client";

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar({ isOpen, toggleSidebar }: { isOpen: boolean; toggleSidebar: () => void }) {
  const [dropdownOpen, setDropdownOpen] = useState<string | null>(null);

  const toggleDropdown = (name: string) => {
    setDropdownOpen(dropdownOpen === name ? null : name);
  };

  return (
    <aside id="sidebar" className={`fixed left-0 top-0 z-50 h-screen w-72 lg:w-72 
      bg-slate-900 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 
      transition-all duration-500 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
      
      {/* Toggle Button for Mobile */}
      <button onClick={toggleSidebar} 
        className="lg:hidden absolute -right-4 top-10 z-[70] flex items-center justify-center 
               w-8 h-8 group transition-all duration-300 ease-in-out
               bg-slate-900 border border-slate-700
               rounded-md shadow-lg hover:shadow-emerald-500/30 hover:border-emerald-500/60
               active:scale-90 focus:outline-none overflow-hidden text-white">
          <i className="fa-solid fa-xmark"></i>
      </button>

      <div className="flex flex-col h-full relative">
        <div className="p-8 flex items-center gap-4 group cursor-pointer">
            <div className="relative flex-shrink-0">
                <div className="absolute inset-0 bg-emerald-500/40 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                <div className="relative w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-2xl flex items-center justify-center text-white shadow-[0_8px_20px_-6px_rgba(16,185,129,0.5)] overflow-hidden transition-transform duration-500 group-hover:scale-110 group-hover:rotate-[5deg]">
                    <div className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
                    <i className="fa-solid fa-compass-drafting text-xl z-10 drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]"></i>
                    <div className="absolute bottom-0 inset-x-0 h-1/2 bg-gradient-to-t from-white/20 to-transparent opacity-50"></div>
                </div>
            </div>

            <div id="logo-container" className="flex flex-col transition-all duration-300">
                <div className="flex items-center">
                    <span className="text-lg font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-slate-900 dark:from-white dark:via-slate-200 dark:to-white">
                        Garderie<span className="text-emerald-600 dark:text-emerald-500">Nova</span>
                    </span>
                </div>
                <div className="flex items-center gap-1.5">
                    <span className="text-[9px] font-black text-white dark:text-slate-500 uppercase tracking-[0.3em]">
                        Management
                    </span>
                    <div className="h-[1px] w-4 bg-emerald-500/40"></div>
                </div>
            </div>
        </div>

        <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto custom-scrollbar">
            <p className="px-5 text-[10px] text-white dark:text-slate-500 uppercase tracking-[0.2em] mb-4 opacity-80">
                Management
            </p>
            
            {/* Dashboard Link */}
            <li className="list-none dropdown-group relative group">
                <div className="absolute inset-0 bg-emerald-500/10 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"></div>
                
                <button onClick={() => toggleDropdown('dashboard')} className="dropdown-trigger group relative z-30 flex items-center w-full gap-3 px-4 py-3 rounded-2xl 
                                               bg-gradient-to-br from-emerald-600 to-emerald-700
                                               text-white overflow-hidden
                                               shadow-[0_10px_25px_-5px_rgba(16,185,129,0.4),inset_0_1px_1px_rgba(255,255,255,0.2)]
                                               transition-all duration-300 active:scale-[0.98]">
                    
                    <div className="relative z-10 ml-4 mr-4 flex-shrink-0 flex items-center justify-center w-9 h-9 bg-white/20 rounded-xl backdrop-blur-md border border-white/30 group-hover:rotate-[8deg] transition-transform duration-300">
                        <i className="fa-solid fa-house-chimney text-[14px] text-white"></i>
                    </div>
            
                    <div className="relative z-10 flex flex-col items-start text-left gap-0.5">
                        <span className="font-extrabold tracking-wide text-[13.5px] text-white/95 drop-shadow-[0_2px_2px_rgba(0,0,0,0.1)] group-hover:text-white transition-colors duration-300">
                            Dashboard
                        </span>
                        <div className="flex items-center gap-1.5">
                            <span className="text-[8.5px] font-bold text-emerald-300/90 uppercase tracking-[0.15em] leading-none">
                                Center Management
                            </span>
                        </div>
                    </div>
            
                    <div className="ml-auto flex items-center gap-3 text-white">
                        <i className={`fa-solid fa-chevron-right text-[10px] transition-transform duration-500 ${dropdownOpen === 'dashboard' ? 'rotate-90' : ''}`}></i>
                    </div>
                </button>
            
                <div className={`overflow-hidden transition-all duration-500 ease-in-out relative z-20 ${dropdownOpen === 'dashboard' ? 'max-h-96' : 'max-h-0'}`}>
                    <div className="relative ml-2 mr-2 mt-2 bg-slate-800/50 rounded-xl p-2 space-y-1 shadow-inner border border-white/5">
                        <Link href="/dashboard" className="flex items-center px-4 py-3 text-[12px] font-medium text-white/80 hover:bg-emerald-500 hover:text-white rounded-lg transition-all">
                            <i className="fa-solid fa-chart-line mr-3 opacity-70"></i>
                            <span>Center Management</span>
                        </Link>
                        <Link href="/dashboard/groups" className="flex items-center px-4 py-3 text-[12px] font-medium text-white/80 hover:bg-emerald-500 hover:text-white rounded-lg transition-all">
                            <i className="fa-solid fa-users-rectangle mr-3 opacity-70"></i>
                            <span>Group Management</span>
                        </Link>
                        <Link href="/dashboard/educators" className="flex items-center px-4 py-3 text-[12px] font-medium text-white/80 hover:bg-emerald-500 hover:text-white rounded-lg transition-all">
                            <i className="fa-solid fa-user-tie mr-3 opacity-70"></i>
                            <span>Educators</span>
                        </Link>
                        <Link href="/dashboard/parents" className="flex items-center px-4 py-3 text-[12px] font-medium text-white/80 hover:bg-emerald-500 hover:text-white rounded-xl transition-all">
                            <i className="fa-solid fa-house-user mr-3 opacity-70"></i>
                            <span>Parents</span>
                        </Link>
                    </div>
                </div>
            </li>

             {/* Child Management */}
             <li className="list-none dropdown-group relative group mt-2">
                <button onClick={() => toggleDropdown('child')} className="dropdown-trigger group relative z-30 flex items-center w-full gap-3 px-4 py-3 rounded-2xl 
                bg-gradient-to-br from-slate-700 to-slate-800
                text-white overflow-hidden
                shadow-[0_10px_25px_-5px_rgba(30,41,59,0.4),inset_0_1px_1px_rgba(255,255,255,0.1)]
                transition-all duration-300 active:scale-[0.98]">
    
                       <div className="relative z-10 ml-4 mr-4 flex-shrink-0 flex items-center justify-center w-9 h-9 bg-white/10 rounded-xl backdrop-blur-md border border-white/20 group-hover:rotate-[8deg] transition-transform duration-300">
                      <i className="fa-solid fa-children text-[14px] text-white"></i>
                     </div>

                      <div className="relative z-10 flex flex-col items-start text-left">
                             <span className="font-bold tracking-tight text-[14px] text-white">Child Management</span>
                              <span className="text-[9px] font-medium text-slate-300 uppercase tracking-widest -mt-0.5">Control Center</span>
                         </div>

                     <div className="ml-auto flex items-center gap-3 text-white">
                     <i className={`fa-solid fa-chevron-down text-[10px] transition-transform duration-500 ${dropdownOpen === 'child' ? 'rotate-180' : ''}`}></i>
                       </div>
             </button>
            
                <div className={`overflow-hidden transition-all duration-500 ease-in-out relative z-20 ${dropdownOpen === 'child' ? 'max-h-96' : 'max-h-0'}`}>
                    <div className="relative ml-2 mr-2 mt-2 bg-slate-800/60 rounded-xl p-2 space-y-1 shadow-inner border border-white/5">
                        <Link href="/dashboard/students" className="flex items-center px-4 py-3 text-sm font-medium text-white/80 hover:bg-emerald-500 hover:text-white rounded-lg transition-all">
                            <i className="fa-solid fa-chart-line mr-3 opacity-70 text-white"></i>
                            <span className="text-[12px] text-white">Child Profiles</span>
                        </Link>
                        <Link href="/dashboard/waitlist" className="flex items-center px-4 py-3 text-sm font-medium text-white/80 hover:bg-emerald-500 hover:text-white rounded-lg transition-all">
                            <i className="fa-solid fa-server mr-3 opacity-70 text-white"></i>
                            <span className="text-[12px] text-white">Waitlist</span>
                        </Link>
                    </div>
                </div>
            </li>

        </nav>
      </div>
    </aside>
  );
}