"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api from '../../../lib/axios';

interface Child {
  child_id: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  profile_photo_url: string;
  age_label: string;
  status: string;
  created_at: string;
}

export default function WaitlistPage() {
  const [waitlist, setWaitlist] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    birth_date: '',
  });

  useEffect(() => {
    fetchWaitlist();
  }, []);

  const fetchWaitlist = async () => {
    try {
      const response = await api.get('/api/children/available/?status=waitlist');
      setWaitlist(response.data);
    } catch (error) {
      console.error('Error fetching waitlist', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/children/available/', {
        ...formData,
        status: 'waitlist'
      });
      setShowAddModal(false);
      setFormData({ first_name: '', last_name: '', birth_date: '' });
      fetchWaitlist();
    } catch (error) {
      console.error('Error adding to waitlist', error);
      alert('Failed to add child to waitlist.');
    }
  };

  const enrollChild = async (childId: string) => {
    if (!confirm('Are you sure you want to enroll this child? This will change their status to Active.')) return;
    try {
      await api.patch(`/api/children/${childId}/`, { status: 'active' });
      fetchWaitlist();
    } catch (error) {
      console.error('Error enrolling child', error);
    }
  };

  const removeChild = async (childId: string) => {
    if (!confirm('Are you sure you want to remove this child from the waitlist?')) return;
    try {
      await api.delete(`/api/children/${childId}/`);
      fetchWaitlist();
    } catch (error) {
      console.error('Error removing child', error);
    }
  };

  const getWaitTime = (createdAt: string) => {
    const start = new Date(createdAt);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 30) return `${diffDays} days`;
    const diffMonths = Math.floor(diffDays / 30);
    return `${diffMonths} month${diffMonths > 1 ? 's' : ''}`;
  };

  const filteredWaitlist = waitlist.filter(child => 
    `${child.first_name} ${child.last_name}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">Waitlist Management</h1>
          <p className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mt-1">
             Manage pending enrollments and priority
          </p>
        </div>
        <div className="flex gap-4">
            <div className="relative">
                <i className="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
                <input 
                    type="text" 
                    placeholder="Search waitlist..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-full md:w-64"
                />
            </div>
            <button 
                onClick={() => setShowAddModal(true)}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-2"
            >
                <i className="fa-solid fa-user-plus"></i> Add to Waitlist
            </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
            <i className="fa-solid fa-circle-notch fa-spin text-indigo-500 text-2xl"></i>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-100 dark:border-slate-800 shadow-xl overflow-hidden">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="bg-slate-50 dark:bg-slate-950/50">
                        <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Child</th>
                        <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Age</th>
                        <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Added On</th>
                        <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Wait Time</th>
                        <th className="px-6 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredWaitlist.length === 0 ? (
                        <tr>
                            <td colSpan={5} className="px-6 py-12 text-center text-slate-400 italic">No children on the waitlist.</td>
                        </tr>
                    ) : (
                        filteredWaitlist.map(child => (
                            <tr key={child.child_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors group">
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold overflow-hidden">
                                            {child.profile_photo_url ? <img src={child.profile_photo_url} className="w-full h-full object-cover" /> : child.first_name.charAt(0)}
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900 dark:text-white">{child.first_name} {child.last_name}</p>
                                            <p className="text-[10px] text-slate-500 font-medium">ID: {child.child_id.substring(0,8)}</p>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="text-xs font-bold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg">
                                        {child.age_label}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <p className="text-xs text-slate-600 dark:text-slate-400">{new Date(child.created_at).toLocaleDateString()}</p>
                                </td>
                                <td className="px-6 py-4">
                                    <p className="text-xs font-black text-emerald-600 dark:text-emerald-400">{getWaitTime(child.created_at)}</p>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button 
                                            onClick={() => enrollChild(child.child_id)}
                                            className="px-3 py-1.5 bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400 rounded-lg text-[10px] font-black uppercase hover:bg-emerald-200 transition-colors"
                                        >
                                            Enroll
                                        </button>
                                        <button 
                                            onClick={() => removeChild(child.child_id)}
                                            className="px-3 py-1.5 bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400 rounded-lg text-[10px] font-black uppercase hover:bg-red-200 transition-colors"
                                        >
                                            Remove
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-8 shadow-2xl border border-slate-100 dark:border-slate-800">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Add to Waitlist</h3>
                    <button onClick={() => setShowAddModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-red-50 hover:text-red-500 transition-colors">
                        <i className="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <form onSubmit={handleAddSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">First Name</label>
                        <input 
                            type="text" 
                            required
                            value={formData.first_name}
                            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Last Name</label>
                        <input 
                            type="text" 
                            required
                            value={formData.last_name}
                            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Date of Birth</label>
                        <input 
                            type="date" 
                            required
                            value={formData.birth_date}
                            onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>

                    <button 
                        type="submit" 
                        className="w-full py-4 mt-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98]"
                    >
                        Add to Waitlist
                    </button>
                </form>
            </div>
        </div>
      )}
    </div>
  );
}
