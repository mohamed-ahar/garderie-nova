"use client";

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';

export default function DashboardPage() {
  return (
    <>
      <section className="relative p-10 rounded-[2.5rem] bg-slate-900 shadow-2xl shadow-green-500/30 overflow-hidden">
          <div className="relative z-10 max-w-xl">
              <span className="px-3 py-1 bg-white/20 rounded-full text-[10px] font-bold text-white uppercase tracking-widest">October Update</span>
              <h1 className="text-4xl md:text-5xl font-extrabold text-white mt-4 tracking-tight">Welcome back, walid!</h1>
              <p className="text-white mt-4 text-sm font-medium ">Your workspace is looking great. You've completed 85% of your weekly tasks. Check your recent notifications below.</p>
              <div className="mt-8 flex gap-4">
                  <button className="px-6 py-3 bg-white text-green-600 rounded-2xl font-bold shadow-lg hover:scale-105 transition-transform">Get Started</button>
                  <button className="px-6 py-3 bg-green-500 text-white rounded-2xl font-bold border border-green-400 hover:bg-green-400 transition-all">View Statistics</button>
              </div>
          </div>
          <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-green-400 rounded-full mix-blend-multiply filter blur-3xl opacity-50"></div>
          <div className="absolute right-20 -top-20 w-72 h-72 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30"></div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10">
          {/* Stats Card 1 */}
          <div className="relative group overflow-hidden p-9 rounded-[3rem] shadow-[0_20px_50px_rgba(79,70,229,0.2)] transition-all duration-500 hover:-translate-y-3 border border-white/10 bg-[#4f46e5]">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500 via-green-600 to-green-900"></div>
              <div className="absolute -top-12 -right-12 w-48 h-48 bg-white/10 blur-[60px] rounded-full"></div>

              <div className="relative z-10">
                  <div className="flex justify-between items-start mb-12">
                      <div className="w-16 h-16 bg-white/10 backdrop-blur-2xl text-white rounded-3xl flex items-center justify-center text-2xl shadow-xl border border-white/20">
                          <i className="fa-solid fa-children"></i>
                      </div>
                      <div className="text-right">
                          <span className="bg-emerald-400/20 backdrop-blur-md px-3 py-1 rounded-full border border-emerald-400/30 text-[10px] font-black text-emerald-300 tracking-tighter uppercase">
                              Legal Ratios: OK
                          </span>
                          <p className="text-[9px] text-white/40 font-bold uppercase tracking-widest mt-2">All Departments</p>
                      </div>
                  </div>

                  <p className="text-white/60 text-xs font-black uppercase tracking-[0.25em]">Current Attendance</p>
                  <div className="flex items-baseline gap-2 mt-1">
                      <h3 className="text-5xl font-black text-white tracking-tighter">142</h3>
                      <span className="text-white/40 text-sm font-bold">/ 160 Capacity</span>
                  </div>

                  <div className="mt-8">
                      <div className="h-1.5 w-full bg-black/20 rounded-full overflow-hidden">
                          <div className="h-full w-[88%] bg-white shadow-[0_0_15px_#fff] transition-all duration-1000"></div>
                      </div>
                      <p className="text-[10px] font-black text-white/40 uppercase tracking-widest mt-3">88% Total Occupancy</p>
                  </div>
              </div>
          </div>

          {/* Stats Card 2 */}
          <div className="relative group overflow-hidden p-9 rounded-[3rem] shadow-[0_20px_50px_rgba(244,63,94,0.2)] transition-all duration-500 hover:-translate-y-3 border border-white/10 bg-[#e11d48]">
              <div className="absolute inset-0 bg-gradient-to-br from-rose-500 via-pink-600 to-rose-800"></div>
              <div className="absolute -bottom-10 -left-10 w-44 h-44 bg-white/10 blur-[55px] rounded-full"></div>

              <div className="relative z-10">
                  <div className="flex justify-between items-start mb-12">
                      <div className="w-16 h-16 bg-white/10 backdrop-blur-2xl text-white rounded-3xl flex items-center justify-center text-2xl shadow-xl border border-white/20">
                          <i className="fa-solid fa-file-signature"></i>
                      </div>
                      <div className="flex flex-col items-end">
                          <div className="flex -space-x-2">
                              <div className="w-8 h-8 rounded-full bg-white/20 border border-white/30 flex items-center justify-center text-[10px] font-black text-white">3</div>
                              <div className="w-8 h-8 rounded-full bg-white/10 border border-white/30 flex items-center justify-center text-[10px] font-black text-white/60">...</div>
                          </div>
                          <p className="text-[9px] text-white/40 font-bold uppercase tracking-widest mt-2">Pending Signatures</p>
                      </div>
                  </div>

                  <p className="text-white/60 text-xs font-black uppercase tracking-[0.25em]">Pending Incidents</p>
                  <h3 className="text-5xl font-black text-white mt-1 tracking-tighter">04</h3>

                  <div className="mt-8 py-3 px-5 bg-black/10 backdrop-blur-md rounded-2xl border border-white/10 flex items-center justify-between group-hover:bg-white/10 transition-colors cursor-pointer">
                      <span className="text-[10px] font-black text-white uppercase tracking-widest">Action Required</span>
                      <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
                  </div>
              </div>
          </div>

          {/* Stats Card 3 */}
          <div className="relative group overflow-hidden p-9 rounded-[3rem] shadow-[0_20px_50px_rgba(5,150,105,0.2)] transition-all duration-500 hover:-translate-y-3 border border-white/10 bg-[#059669]">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500 via-teal-600 to-emerald-800"></div>
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 blur-[40px] rounded-full"></div>

              <div className="relative z-10">
                  <div className="flex justify-between items-start mb-12">
                      <div className="w-16 h-16 bg-white/10 backdrop-blur-2xl text-white rounded-3xl flex items-center justify-center text-2xl shadow-xl border border-white/20">
                          <i className="fa-solid fa-graduation-cap"></i>
                      </div>
                      <div className="text-right">
                          <p className="text-white font-black text-lg">92%</p>
                          <p className="text-[9px] text-white/40 font-bold uppercase tracking-widest">Compliance</p>
                      </div>
                  </div>

                  <p className="text-white/60 text-xs font-black uppercase tracking-[0.25em]">Observations Filed</p>
                  <h3 className="text-5xl font-black text-white mt-1 tracking-tighter">842</h3>

                  <div className="mt-8 flex items-end gap-1.5 h-10">
                      <div className="w-full bg-white/20 h-2/3 rounded-t-sm group-hover:h-full transition-all duration-700"></div>
                      <div className="w-full bg-white/20 h-1/2 rounded-t-sm group-hover:h-2/3 transition-all duration-700 delay-75"></div>
                      <div className="w-full bg-white/40 h-3/4 rounded-t-sm group-hover:h-5/6 transition-all duration-700 delay-150"></div>
                      <div className="w-full bg-white/20 h-1/3 rounded-t-sm group-hover:h-1/2 transition-all duration-700 delay-200"></div>
                      <div className="w-full bg-white h-5/6 rounded-t-sm group-hover:h-full transition-all duration-700 delay-300"></div>
                  </div>
              </div>
          </div>
      </div>

      {/* Student Directory */}
      <div className="max-w-6xl mx-auto mt-6 px-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-black text-emerald-600 dark:text-white tracking-tighter">Student Directory</h1>
                    <p className="text-slate-500 text-sm dark:text-slate-400 font-medium">Manage enrollment and daily attendance status.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-5 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-sm font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 transition-all shadow-sm">
                        <i className="fa-solid fa-download"></i>
                        Export
                    </button>
                    <button className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-2xl text-sm font-bold hover:bg-emerald-700 transition-all shadow-lg shadow-emerald-500/25 active:scale-95">
                        <i className="fa-solid fa-plus"></i>
                        Add Student
                    </button>
                </div>
            </div>
            
            <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-100 dark:border-slate-800 shadow-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50/50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800">
                                <th className="px-8 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">Student</th>
                                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">Classroom</th>
                                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">Status</th>
                                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">Parent/Guardian</th>
                                <th className="px-8 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50 dark:divide-slate-800">
                            {/* Row 1 */}
                            <tr className="group hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                                <td className="px-8 py-5">
                                    <div className="flex items-center gap-4">
                                        <div className="relative">
                                            <img className="w-12 h-12 rounded-2xl object-cover bg-slate-100 ring-2 ring-white dark:ring-slate-800" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Liam" alt="Student" />
                                            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-white dark:border-slate-900 rounded-full"></div>
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900 dark:text-white">Liam Anderson</p>
                                            <p className="text-xs text-slate-500 font-medium italic">Age: 4 years</p>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-5">
                                    <span className="px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[11px] font-black rounded-lg uppercase">Pre-K Blue</span>
                                </td>
                                <td className="px-6 py-5">
                                    <div className="flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300">Present</span>
                                    </div>
                                </td>
                                <td className="px-6 py-5">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-slate-700 dark:text-slate-200">Sarah Anderson</span>
                                        <span className="text-xs text-slate-500 underline decoration-slate-300">sarah.a@email.com</span>
                                    </div>
                                </td>
                                <td className="px-8 py-5 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <Link href="/students/liam-anderson" className="w-9 h-9 flex items-center justify-center text-slate-400 bg-slate-50 dark:bg-slate-800/50 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-xl border border-slate-100 dark:border-slate-700 transition-all shadow-sm">
                                            <i className="fa-solid fa-pen-to-square text-xs"></i>
                                        </Link>
                                        <button className="w-9 h-9 flex items-center justify-center text-slate-400 bg-slate-50 dark:bg-slate-800/50 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-xl border border-slate-100 dark:border-slate-700 transition-all shadow-sm">
                                            <i className="fa-solid fa-eye text-xs"></i>
                                        </button>
                                        <button className="w-9 h-9 flex items-center justify-center text-slate-400 bg-slate-50 dark:bg-slate-800/50 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-xl border border-slate-100 dark:border-slate-700 transition-all shadow-sm">
                                            <i className="fa-solid fa-trash-can text-xs"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
      </div>
    </>
  );
}