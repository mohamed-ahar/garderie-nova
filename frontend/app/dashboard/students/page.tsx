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
  group_name: string | null;
  educator_name: string | null;
  status: string;
}

const AGE_GROUPS = [
    { label: 'All Ages', value: 'all', min: 0, max: 9999 },
    { label: 'Under 24 Months', value: 'under_24', min: 0, max: 24 },
    { label: '24 Months - 4 Years', value: '24_48', min: 24, max: 47 },
    { label: '4 Years +', value: '4_plus', min: 48, max: 9999 },
];

const STATUS_OPTIONS = [
    { label: 'All Statuses', value: 'all' },
    { label: 'Active', value: 'active' },
    { label: 'Inactive', value: 'inactive' },
    { label: 'Pending', value: 'pending' },
];

export default function StudentsPage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  
  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [ageFilter, setAgeFilter] = useState('all');

  // Form State
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [birthDate, setBirthDate] = useState('');

  useEffect(() => {
    fetchChildren();
  }, []);

  const fetchChildren = async () => {
    try {
      const response = await api.get('/api/children/available/');
      setChildren(response.data);
    } catch (error) {
      console.error('Error fetching children', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/api/children/available/', {
        first_name: firstName,
        last_name: lastName,
        birth_date: birthDate,
        status: 'active'
      });
      setShowModal(false);
      setFirstName('');
      setLastName('');
      setBirthDate('');
      fetchChildren();
    } catch (error) {
      console.error('Error creating child', error);
      alert('Failed to create child. Please check inputs.');
    }
  };

  const getAgeInMonths = (birthDateStr: string) => {
      const today = new Date();
      const birth = new Date(birthDateStr);
      return (today.getFullYear() - birth.getFullYear()) * 12 + (today.getMonth() - birth.getMonth());
  };

  const filteredChildren = children.filter(child => {
    // 1. Search Query
    const fullName = `${child.first_name} ${child.last_name}`.toLowerCase();
    if (!fullName.includes(searchQuery.toLowerCase())) return false;

    // 2. Status Filter
    if (statusFilter !== 'all' && child.status !== statusFilter) return false;

    // 3. Age Filter
    if (ageFilter !== 'all') {
        const ageMonths = getAgeInMonths(child.birth_date);
        const selectedGroup = AGE_GROUPS.find(g => g.value === ageFilter);
        if (selectedGroup) {
            if (ageMonths < selectedGroup.min || ageMonths > selectedGroup.max) return false;
        }
    }

    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">Students</h1>
          <p className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mt-1">
             Manage all children in the center
          </p>
        </div>
        <button 
            onClick={() => setShowModal(true)}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2"
        >
            <i className="fa-solid fa-plus"></i> Add Child
        </button>
      </div>

      {/* Filters Section */}
      <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-4 mb-8 border border-slate-100 dark:border-slate-800 shadow-sm flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full">
                <i className="fa-solid fa-search absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"></i>
                <input 
                    type="text" 
                    placeholder="Search students..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white placeholder:text-slate-400"
                />
            </div>
            
            <div className="flex gap-4 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
                 {/* Status Filter */}
                 <div className="relative min-w-[140px]">
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="w-full appearance-none px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white cursor-pointer"
                    >
                        {STATUS_OPTIONS.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                    <i className="fa-solid fa-chevron-down absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 text-xs pointer-events-none"></i>
                 </div>

                 {/* Age Filter */}
                 <div className="relative min-w-[180px]">
                    <select
                        value={ageFilter}
                        onChange={(e) => setAgeFilter(e.target.value)}
                        className="w-full appearance-none px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white cursor-pointer"
                    >
                        {AGE_GROUPS.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                    <i className="fa-solid fa-chevron-down absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 text-xs pointer-events-none"></i>
                 </div>
            </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
            <i className="fa-solid fa-circle-notch fa-spin text-emerald-500 text-2xl"></i>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredChildren.length === 0 ? (
             <div className="col-span-full text-center py-12 text-slate-400">
                 No students found matching your filters.
             </div>
          ) : (
            filteredChildren.map(child => (
                <Link key={child.child_id} href={`/dashboard/students/${child.child_id}`} className="block group">
                    <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-6 border border-slate-100 dark:border-slate-800 shadow-xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 h-full flex flex-col">
                        <div className="flex items-start justify-between mb-4">
                            <div className="w-16 h-16 rounded-2xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400 text-2xl font-bold overflow-hidden shadow-inner">
                                {child.profile_photo_url ? (
                                    <img src={child.profile_photo_url} alt={child.first_name} className="w-full h-full object-cover" />
                                ) : (
                                    child.first_name.charAt(0)
                                )}
                            </div>
                            <span className={`px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${child.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                                {child.status}
                            </span>
                        </div>
                        
                        <div className="mb-4 flex-1">
                            <h3 className="text-lg font-black text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                                {child.first_name} {child.last_name}
                            </h3>
                            <p className="text-sm font-bold text-slate-400">{child.age_label} old</p>
                        </div>

                        <div className="space-y-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-500 font-medium">Group</span>
                                <span className="font-bold text-slate-700 dark:text-slate-300">
                                    {child.group_name || <span className="text-amber-500">Unassigned</span>}
                                </span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-500 font-medium">Educator</span>
                                <span className="font-bold text-slate-700 dark:text-slate-300">
                                    {child.educator_name || <span className="text-slate-400">-</span>}
                                </span>
                            </div>
                        </div>
                    </div>
                </Link>
            ))
          )}
        </div>
      )}

      {/* Add Child Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-8 shadow-2xl border border-slate-100 dark:border-slate-800">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Add New Child</h3>
                    <button onClick={() => setShowModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-red-50 hover:text-red-500 transition-colors">
                        <i className="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">First Name</label>
                        <input 
                            type="text" 
                            required
                            value={firstName}
                            onChange={(e) => setFirstName(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. Noah"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Last Name</label>
                        <input 
                            type="text" 
                            required
                            value={lastName}
                            onChange={(e) => setLastName(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. Smith"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Date of Birth</label>
                        <input 
                            type="date" 
                            required
                            value={birthDate}
                            onChange={(e) => setBirthDate(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>

                    <button 
                        type="submit" 
                        className="w-full py-4 mt-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black shadow-lg shadow-emerald-500/20 transition-all active:scale-[0.98]"
                    >
                        Create Student Profile
                    </button>
                </form>
            </div>
        </div>
      )}
    </div>
  );
}