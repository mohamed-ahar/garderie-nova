"use client";

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import api from '../../../../lib/axios';

interface Child {
  child_id: string;
  first_name: string;
  last_name: string;
  age_label: string;
  profile_photo_url: string;
  group_name: string | null;
}

interface EducatorDetail {
  user_id: string;
  full_name: string;
  email: string;
  phone_number: string;
  profile_photo_url: string | null;
  current_group_id: string | null;
  current_group_name: string | null;
  is_active_in_ratio: boolean;
  assigned_children: Child[];
}

export default function EducatorProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const educatorId = unwrappedParams.id;
  const [educator, setEducator] = useState<EducatorDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Edit State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState<{
      full_name: string;
      email: string;
      phone_number: string;
      is_active_in_ratio: boolean;
      profile_photo: File | null;
  }>({
      full_name: '',
      email: '',
      phone_number: '',
      is_active_in_ratio: true,
      profile_photo: null
  });

  useEffect(() => {
    fetchEducatorDetails();
  }, [educatorId]);

  const fetchEducatorDetails = async () => {
    try {
      const response = await api.get(`/api/educators/${educatorId}/`);
      setEducator(response.data);
      setEditForm({
          full_name: response.data.full_name,
          email: response.data.email,
          phone_number: response.data.phone_number || '',
          is_active_in_ratio: response.data.is_active_in_ratio,
          profile_photo: null
      });
    } catch (error) {
      console.error('Error fetching educator details', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
          const formData = new FormData();
          formData.append('full_name', editForm.full_name);
          formData.append('email', editForm.email);
          formData.append('phone_number', editForm.phone_number);
          formData.append('is_active_in_ratio', String(editForm.is_active_in_ratio));
          
          if (editForm.profile_photo) {
              formData.append('profile_photo', editForm.profile_photo);
          }

          const response = await api.patch(`/api/educators/${educatorId}/`, formData, {
              headers: {
                  'Content-Type': 'multipart/form-data',
              },
          });
          setEducator(response.data);
          setShowEditModal(false);
      } catch (error) {
          console.error('Error updating educator', error);
          alert('Failed to update educator.');
      }
  };

  if (loading) return <div className="p-12 text-center"><i className="fa-solid fa-circle-notch fa-spin text-emerald-500 text-3xl"></i></div>;
  if (!educator) return <div className="p-12 text-center text-slate-500">Educator not found</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
       <Link href="/dashboard/educators" className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-emerald-600 mb-6 transition-colors">
         <i className="fa-solid fa-arrow-left"></i> Back to Educators
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar Info */}
          <div className="space-y-8">
              <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800 relative overflow-hidden">
                  <div className="flex flex-col items-center text-center relative z-10">
                      <div className="w-24 h-24 rounded-3xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300 text-3xl font-black mb-4 shadow-inner overflow-hidden">
                          {educator.profile_photo_url ? (
                              <img src={educator.profile_photo_url} className="w-full h-full object-cover" />
                          ) : (
                              educator.full_name.charAt(0)
                          )}
                      </div>
                      <h1 className="text-2xl font-black text-slate-900 dark:text-white mb-1">{educator.full_name}</h1>
                      <div className="flex items-center gap-2 mb-6">
                          <span className={`w-2 h-2 rounded-full ${educator.is_active_in_ratio ? 'bg-emerald-500' : 'bg-slate-300'}`}></span>
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                              {educator.is_active_in_ratio ? 'Active in Ratio' : 'Inactive'}
                          </span>
                      </div>

                      <button 
                        onClick={() => setShowEditModal(true)}
                        className="w-full py-3 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-xl font-bold transition-colors text-sm flex items-center justify-center gap-2"
                      >
                          <i className="fa-solid fa-pen-to-square text-xs"></i> Edit Profile
                      </button>
                  </div>

                  <div className="mt-8 space-y-4 border-t border-slate-50 dark:border-slate-800 pt-8">
                      <div className="flex items-center gap-3 text-slate-500">
                          <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center text-blue-500">
                              <i className="fa-solid fa-envelope text-xs"></i>
                          </div>
                          <div className="flex-1 min-w-0">
                              <p className="text-[10px] font-bold text-slate-400 uppercase">Email</p>
                              <p className="text-xs font-bold text-slate-700 dark:text-slate-300 truncate">{educator.email}</p>
                          </div>
                      </div>
                      <div className="flex items-center gap-3 text-slate-500">
                          <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-500">
                              <i className="fa-solid fa-phone text-xs"></i>
                          </div>
                          <div className="flex-1 min-w-0">
                              <p className="text-[10px] font-bold text-slate-400 uppercase">Phone</p>
                              <p className="text-xs font-bold text-slate-700 dark:text-slate-300">{educator.phone_number || 'Not provided'}</p>
                          </div>
                      </div>
                  </div>
              </div>

              <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800">
                  <h2 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest mb-6">Current Assignment</h2>
                  {educator.current_group_id ? (
                      <Link 
                        href={`/dashboard/groups/${educator.current_group_id}`}
                        className="flex items-center justify-between p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20 group"
                      >
                          <div className="flex items-center gap-3">
                              <i className="fa-solid fa-users-rectangle text-emerald-600 text-lg"></i>
                              <div>
                                  <p className="text-xs font-black text-emerald-700 dark:text-emerald-400 uppercase">{educator.current_group_name}</p>
                                  <p className="text-[10px] text-emerald-600/60 font-bold">Assigned Group</p>
                              </div>
                          </div>
                          <i className="fa-solid fa-arrow-right text-emerald-400 group-hover:translate-x-1 transition-transform"></i>
                      </Link>
                  ) : (
                      <div className="p-6 rounded-2xl border-2 border-dashed border-slate-100 dark:border-slate-800 text-center">
                          <p className="text-xs font-bold text-slate-400">No active assignment</p>
                      </div>
                  )}
              </div>
          </div>

          {/* Main Content: Assigned Children */}
          <div className="lg:col-span-2 space-y-8">
              <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800">
                  <div className="flex items-center justify-between mb-8">
                      <h2 className="text-xl font-black text-slate-900 dark:text-white flex items-center gap-3">
                          <i className="fa-solid fa-children text-rose-500"></i>
                          Assigned Children
                          <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 px-3 py-1 rounded-full text-xs ml-2">
                              {educator.assigned_children.length}
                          </span>
                      </h2>
                  </div>

                  {educator.assigned_children.length === 0 ? (
                      <div className="text-center py-16">
                          <div className="w-16 h-16 rounded-full bg-slate-50 dark:bg-slate-800 flex items-center justify-center text-slate-200 dark:text-slate-700 mx-auto mb-4">
                              <i className="fa-solid fa-child text-3xl"></i>
                          </div>
                          <p className="text-slate-400 font-bold text-sm">No children assigned to this educator yet.</p>
                          <p className="text-xs text-slate-400 mt-1">Assign children in Group Management.</p>
                      </div>
                  ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {educator.assigned_children.map(child => (
                              <Link key={child.child_id} href={`/dashboard/students/${child.child_id}`} className="block group/child">
                                  <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 hover:border-emerald-200 dark:hover:border-emerald-900 transition-all flex items-center justify-between">
                                      <div className="flex items-center gap-4">
                                          <div className="w-12 h-12 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400 font-black overflow-hidden shadow-inner">
                                              {child.profile_photo_url ? <img src={child.profile_photo_url} className="w-full h-full object-cover" /> : child.first_name.charAt(0)}
                                          </div>
                                          <div>
                                              <p className="text-sm font-bold text-slate-900 dark:text-white group-hover/child:text-emerald-600 transition-colors">{child.first_name} {child.last_name}</p>
                                              <div className="flex items-center gap-2 mt-0.5">
                                                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{child.age_label}</span>
                                                  <span className="text-[10px] text-slate-300">•</span>
                                                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{child.group_name || 'No Group'}</span>
                                              </div>
                                          </div>
                                      </div>
                                      <i className="fa-solid fa-chevron-right text-slate-300 group-hover/child:translate-x-1 transition-transform text-xs"></i>
                                  </div>
                              </Link>
                          ))}
                      </div>
                  )}
              </div>
          </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-8 shadow-2xl border border-slate-100 dark:border-slate-800">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Edit Educator</h3>
                    <button onClick={() => setShowEditModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-red-50 hover:text-red-500 transition-colors">
                        <i className="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <form onSubmit={handleEditSubmit} className="space-y-4">
                    <div className="flex justify-center mb-6">
                        <div className="relative group">
                            <div className="w-24 h-24 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700">
                                {editForm.profile_photo ? (
                                    <img src={URL.createObjectURL(editForm.profile_photo)} className="w-full h-full object-cover" />
                                ) : (
                                    educator.profile_photo_url ? (
                                        <img src={educator.profile_photo_url} className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-slate-400">
                                            <i className="fa-solid fa-camera text-2xl"></i>
                                        </div>
                                    )
                                )}
                            </div>
                            <label className="absolute bottom-0 right-0 w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center text-white cursor-pointer hover:bg-emerald-600 transition-colors shadow-lg">
                                <i className="fa-solid fa-pencil text-xs"></i>
                                <input 
                                    type="file" 
                                    className="hidden" 
                                    accept="image/*"
                                    onChange={(e) => {
                                        if (e.target.files && e.target.files[0]) {
                                            setEditForm({...editForm, profile_photo: e.target.files[0]});
                                        }
                                    }}
                                />
                            </label>
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Full Name</label>
                        <input 
                            type="text" 
                            required
                            value={editForm.full_name}
                            onChange={(e) => setEditForm({...editForm, full_name: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Email</label>
                        <input 
                            type="email" 
                            required
                            value={editForm.email}
                            onChange={(e) => setEditForm({...editForm, email: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Phone Number</label>
                        <input 
                            type="text" 
                            value={editForm.phone_number}
                            onChange={(e) => setEditForm({...editForm, phone_number: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>
                    <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active in Ratio</span>
                        <button 
                            type="button"
                            onClick={() => setEditForm({...editForm, is_active_in_ratio: !editForm.is_active_in_ratio})}
                            className={`w-12 h-6 rounded-full transition-colors relative ${editForm.is_active_in_ratio ? 'bg-emerald-500' : 'bg-slate-300'}`}
                        >
                            <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${editForm.is_active_in_ratio ? 'left-7' : 'left-1'}`}></div>
                        </button>
                    </div>

                    <button 
                        type="submit" 
                        className="w-full py-4 mt-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black shadow-lg shadow-emerald-500/20 transition-all active:scale-[0.98]"
                    >
                        Save Changes
                    </button>
                </form>
            </div>
        </div>
      )}
    </div>
  );
}