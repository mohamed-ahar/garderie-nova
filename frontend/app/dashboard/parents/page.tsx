"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api from '../../../lib/axios';

interface ChildSummary {
    relationship_type: string;
    child: {
        first_name: string;
        last_name: string;
        status: string;
    };
}

interface Parent {
  user_id: string;
  full_name: string;
  email: string;
  phone_number: string;
  profile_photo_url: string | null;
  home_address: string;
  children: ChildSummary[];
}

export default function ParentsPage() {
  const [parents, setParents] = useState<Parent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    home_address: '',
  });

  useEffect(() => {
    fetchParents();
  }, []);

  const fetchParents = async () => {
    try {
      const response = await api.get('/api/parents/');
      setParents(response.data);
    } catch (error) {
      console.error('Error fetching parents', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/parents/', formData);
      setShowAddModal(false);
      setFormData({ full_name: '', email: '', phone_number: '', password: '', home_address: '' });
      fetchParents();
    } catch (error) {
      console.error('Error adding parent', error);
      alert('Failed to add parent.');
    }
  };

  const deleteParent = async (parentId: string) => {
      if (!confirm('Are you sure you want to remove this parent? This will delete their account.')) return;
      try {
          await api.delete(`/api/parents/${parentId}/`);
          fetchParents();
      } catch (error) {
          console.error('Error deleting parent', error);
      }
  };

  const filteredParents = parents.filter(p => 
    p.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">Parent Management</h1>
          <p className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mt-1">
             Manage family accounts and relationships
          </p>
        </div>
        <div className="flex gap-4">
            <div className="relative">
                <i className="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
                <input 
                    type="text" 
                    placeholder="Search parents..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-full md:w-64"
                />
            </div>
            <button 
                onClick={() => setShowAddModal(true)}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-2"
            >
                <i className="fa-solid fa-user-plus"></i> Add Parent
            </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
            <i className="fa-solid fa-circle-notch fa-spin text-emerald-500 text-2xl"></i>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredParents.map(parent => (
            <div key={parent.user_id} className="bg-white dark:bg-slate-900 rounded-[2rem] p-6 border border-slate-100 dark:border-slate-800 shadow-xl flex flex-col h-full relative group overflow-hidden">
                <div className="flex items-start justify-between mb-6">
                    <Link href={`/dashboard/parents/${parent.user_id}`} className="flex items-center gap-4 group/info">
                        <div className="w-14 h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 text-xl font-black shadow-inner group-hover/info:bg-indigo-100 transition-colors overflow-hidden">
                            {parent.profile_photo_url ? (
                                <img src={parent.profile_photo_url} className="w-full h-full object-cover" />
                            ) : (
                                parent.full_name.charAt(0)
                            )}
                        </div>
                        <div>
                            <h3 className="text-lg font-black text-slate-900 dark:text-white leading-tight group-hover/info:text-indigo-600 transition-colors">{parent.full_name}</h3>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Parent Account</p>
                        </div>
                    </Link>
                    <button 
                        onClick={() => deleteParent(parent.user_id)}
                        className="w-8 h-8 rounded-lg bg-red-50 text-red-500 hover:bg-red-500 hover:text-white transition-colors flex items-center justify-center"
                    >
                        <i className="fa-solid fa-trash-can text-xs"></i>
                    </button>
                </div>

                <div className="space-y-3 flex-1">
                    <div className="flex items-center gap-3 text-slate-500">
                        <i className="fa-solid fa-envelope text-xs w-4"></i>
                        <span className="text-xs font-bold truncate">{parent.email}</span>
                    </div>
                    <div className="flex items-center gap-3 text-slate-500">
                        <i className="fa-solid fa-phone text-xs w-4"></i>
                        <span className="text-xs font-bold">{parent.phone_number || 'N/A'}</span>
                    </div>
                    <div className="flex items-start gap-3 text-slate-500">
                        <i className="fa-solid fa-location-dot text-xs w-4 mt-1"></i>
                        <span className="text-xs font-bold leading-relaxed">{parent.home_address || 'No address provided'}</span>
                    </div>
                </div>

                <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Linked Children</p>
                    <div className="flex flex-wrap gap-2">
                        {parent.children.length > 0 ? parent.children.map((rel, idx) => (
                            <div key={idx} className="px-3 py-1 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 flex items-center gap-2">
                                <span className="text-[10px] font-black text-slate-700 dark:text-slate-300">
                                    {rel.child.first_name}
                                </span>
                                <span className={`w-1.5 h-1.5 rounded-full ${rel.child.status === 'active' ? 'bg-emerald-500' : rel.child.status === 'waitlist' ? 'bg-amber-500' : 'bg-slate-300'}`}></span>
                            </div>
                        )) : (
                            <span className="text-xs font-bold text-slate-400 italic">No children linked</span>
                        )}
                    </div>
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
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Add New Parent</h3>
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
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. John Doe"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Email</label>
                        <input 
                            type="email" 
                            required
                            value={formData.email}
                            onChange={(e) => setFormData({...formData, email: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. john@example.com"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Phone Number</label>
                        <input 
                            type="text" 
                            value={formData.phone_number}
                            onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
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
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="min 8 chars"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Home Address</label>
                        <input 
                            type="text" 
                            value={formData.home_address}
                            onChange={(e) => setFormData({...formData, home_address: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. 123 Maple St."
                        />
                    </div>

                    <button 
                        type="submit" 
                        className="w-full py-4 mt-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98]"
                    >
                        Create Parent Account
                    </button>
                </form>
            </div>
        </div>
      )}
    </div>
  );
}
