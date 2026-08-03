"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api from '../../../lib/axios';

interface Educator {
  user_id: string;
  full_name: string;
  email: string;
  phone_number: string;
  profile_photo_url: string | null;
  current_group_id: string | null;
  current_group_name: string | null;
  is_active_in_ratio: boolean;
}

export default function EducatorsPage() {
  const [educators, setEducators] = useState<Educator[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
  });

  useEffect(() => {
    fetchEducators();
  }, []);

  const fetchEducators = async () => {
    try {
      const response = await api.get('/api/educators/available/');
      setEducators(response.data);
    } catch (error) {
      console.error('Error fetching educators', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/educators/available/', formData);
      setShowAddModal(false);
      setFormData({ full_name: '', email: '', phone_number: '', password: '' });
      fetchEducators();
    } catch (error) {
      console.error('Error adding educator', error);
      alert('Failed to add educator.');
    }
  };

  const toggleRatioActive = async (educatorId: string, currentStatus: boolean) => {
      try {
          await api.patch(`/api/educators/${educatorId}/`, { is_active_in_ratio: !currentStatus });
          fetchEducators();
      } catch (error) {
          console.error('Error toggling status', error);
      }
  };

  const deleteEducator = async (educatorId: string) => {
      if (!confirm('Are you sure you want to remove this educator? This will delete their account.')) return;
      try {
          await api.delete(`/api/educators/${educatorId}/`);
          fetchEducators();
      } catch (error) {
          console.error('Error deleting educator', error);
      }
  };

  const filteredEducators = educators.filter(e => 
    e.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">Educator Management</h1>
          <p className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mt-1">
             Manage staff, assignments, and roles
          </p>
        </div>
        <div className="flex gap-4">
            <div className="relative">
                <i className="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
                <input 
                    type="text" 
                    placeholder="Search staff..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-full md:w-64"
                />
            </div>
            <button 
                onClick={() => setShowAddModal(true)}
                className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2"
            >
                <i className="fa-solid fa-user-plus"></i> Add Educator
            </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
            <i className="fa-solid fa-circle-notch fa-spin text-emerald-500 text-2xl"></i>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEducators.map(educator => (
            <div key={educator.user_id} className="bg-white dark:bg-slate-900 rounded-[2rem] p-6 border border-slate-100 dark:border-slate-800 shadow-xl flex flex-col h-full relative group overflow-hidden">
                <div className="flex items-start justify-between mb-6">
                    <Link href={`/dashboard/educators/${educator.user_id}`} className="flex items-center gap-4 group/info">
                        <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300 text-xl font-black shadow-inner group-hover/info:bg-emerald-100 transition-colors overflow-hidden">
                            {educator.profile_photo_url ? (
                                <img src={educator.profile_photo_url} className="w-full h-full object-cover" />
                            ) : (
                                educator.full_name.charAt(0)
                            )}
                        </div>
                        <div>
                            <h3 className="text-lg font-black text-slate-900 dark:text-white leading-tight group-hover/info:text-emerald-600 transition-colors">{educator.full_name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                                <span className={`w-2 h-2 rounded-full ${educator.is_active_in_ratio ? 'bg-emerald-500' : 'bg-slate-300'}`}></span>
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                    {educator.is_active_in_ratio ? 'Active in Ratio' : 'Inactive'}
                                </span>
                            </div>
                        </div>
                    </Link>
                    <div className="flex flex-col gap-2">
                        <button 
                            onClick={() => deleteEducator(educator.user_id)}
                            className="w-8 h-8 rounded-lg bg-red-50 text-red-500 hover:bg-red-500 hover:text-white transition-colors flex items-center justify-center"
                        >
                            <i className="fa-solid fa-trash-can text-xs"></i>
                        </button>
                    </div>
                </div>

                <div className="space-y-3 flex-1">
                    <div className="flex items-center gap-3 text-slate-500">
                        <i className="fa-solid fa-envelope text-xs w-4"></i>
                        <span className="text-xs font-bold truncate">{educator.email}</span>
                    </div>
                    <div className="flex items-center gap-3 text-slate-500">
                        <i className="fa-solid fa-phone text-xs w-4"></i>
                        <span className="text-xs font-bold">{educator.phone_number || 'N/A'}</span>
                    </div>
                </div>

                <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Current Assignment</p>
                    {educator.current_group_id ? (
                        <Link 
                            href={`/dashboard/groups/${educator.current_group_id}`}
                            className="flex items-center justify-between p-3 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20 group/assign"
                        >
                            <div className="flex items-center gap-2">
                                <i className="fa-solid fa-users-rectangle text-emerald-600"></i>
                                <span className="text-xs font-black text-emerald-700 dark:text-emerald-400">{educator.current_group_name}</span>
                            </div>
                            <i className="fa-solid fa-arrow-right text-[10px] text-emerald-400 group-hover/assign:translate-x-1 transition-transform"></i>
                        </Link>
                    ) : (
                        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-center">
                            <span className="text-xs font-bold text-slate-400">Not Assigned</span>
                        </div>
                    )}
                </div>

                <div className="mt-4 flex gap-2">
                    <button 
                        onClick={() => toggleRatioActive(educator.user_id, educator.is_active_in_ratio)}
                        className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase transition-all ${educator.is_active_in_ratio ? 'bg-slate-100 text-slate-600 hover:bg-slate-200' : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'}`}
                    >
                        {educator.is_active_in_ratio ? 'Set Inactive' : 'Activate in Ratio'}
                    </button>
                </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-8 shadow-2xl border border-slate-100 dark:border-slate-800">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Add New Educator</h3>
                    <button onClick={() => setShowAddModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-red-50 hover:text-red-500 transition-colors">
                        <i className="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <form onSubmit={handleAddSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Full Name</label>
                        <input 
                            type="text" 
                            required
                            value={formData.full_name}
                            onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. Marie Curie"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Email</label>
                        <input 
                            type="email" 
                            required
                            value={formData.email}
                            onChange={(e) => setFormData({...formData, email: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. marie@garderie.com"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Phone Number</label>
                        <input 
                            type="text" 
                            value={formData.phone_number}
                            onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. (555) 000-0000"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Initial Password</label>
                        <input 
                            type="password" 
                            required
                            value={formData.password}
                            onChange={(e) => setFormData({...formData, password: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="min 8 chars"
                        />
                    </div>

                    <button 
                        type="submit" 
                        className="w-full py-4 mt-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black shadow-lg shadow-emerald-500/20 transition-all active:scale-[0.98]"
                    >
                        Create Educator Profile
                    </button>
                </form>
            </div>
        </div>
      )}
    </div>
  );
}