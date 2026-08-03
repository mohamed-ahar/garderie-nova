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
  status: string;
}

interface Relationship {
    relationship_type: string;
    is_emergency_contact: boolean;
    child: Child;
}

interface ParentDetail {
  user_id: string;
  full_name: string;
  email: string;
  phone_number: string;
  profile_photo_url: string | null;
  home_address: string;
  billing_reference: string;
  children: Relationship[];
}

export default function ParentProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const parentId = unwrappedParams.id;
  const [parent, setParent] = useState<ParentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Link Child State
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [availableChildren, setAvailableChildren] = useState<Child[]>([]);
  const [linkData, setLinkData] = useState({
      child_id: '',
      relationship_type: 'Parent',
      is_emergency_contact: true
  });

  // Edit State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({
      full_name: '',
      email: '',
      phone_number: '',
      home_address: '',
      profile_photo: null as File | null
  });

  useEffect(() => {
    fetchParentDetails();
  }, [parentId]);

  const fetchParentDetails = async () => {
    try {
      const response = await api.get(`/api/parents/${parentId}/`);
      setParent(response.data);
      setEditForm({
          full_name: response.data.full_name,
          email: response.data.email,
          phone_number: response.data.phone_number || '',
          home_address: response.data.home_address || '',
          profile_photo: null
      });
    } catch (error) {
      console.error('Error fetching parent details', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableChildren = async () => {
      try {
          const response = await api.get('/api/children/available/');
          // Filter out children already linked
          const linkedIds = parent?.children.map(r => r.child.child_id) || [];
          setAvailableChildren(response.data.filter((c: Child) => !linkedIds.includes(c.child_id)));
          setShowLinkModal(true);
      } catch (error) {
          console.error('Error fetching children', error);
      }
  };

  const handleLinkSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!linkData.child_id) return;
      try {
          // We need an endpoint to link child to parent. 
          // Assuming we can use a generic relationship view or I'll need to add it.
          // For now, I'll assume a dedicated endpoint or handle it via a new view I'll add.
          await api.post(`/api/parents/${parentId}/link_child/`, linkData);
          setShowLinkModal(false);
          fetchParentDetails();
      } catch (error) {
          console.error('Error linking child', error);
          alert('Failed to link child.');
      }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
          const formData = new FormData();
          formData.append('full_name', editForm.full_name);
          formData.append('email', editForm.email);
          formData.append('phone_number', editForm.phone_number);
          formData.append('home_address', editForm.home_address);
          if (editForm.profile_photo) {
              formData.append('profile_photo', editForm.profile_photo);
          }

          const response = await api.patch(`/api/parents/${parentId}/`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
          });
          setParent(response.data);
          setShowEditModal(false);
      } catch (error) {
          console.error('Error updating parent', error);
      }
  };

  if (loading) return <div className="p-12 text-center"><i className="fa-solid fa-circle-notch fa-spin text-emerald-500 text-3xl"></i></div>;
  if (!parent) return <div className="p-12 text-center text-slate-500">Parent not found</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
       <Link href="/dashboard/parents" className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-indigo-600 mb-6 transition-colors">
         <i className="fa-solid fa-arrow-left"></i> Back to Parents
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="space-y-8">
              <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800 relative overflow-hidden">
                  <div className="flex flex-col items-center text-center relative z-10">
                      <div className="w-24 h-24 rounded-3xl bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 text-3xl font-black mb-4 shadow-inner overflow-hidden">
                          {parent.profile_photo_url ? (
                              <img src={parent.profile_photo_url} className="w-full h-full object-cover" />
                          ) : (
                              parent.full_name.charAt(0)
                          )}
                      </div>
                      <h1 className="text-2xl font-black text-slate-900 dark:text-white mb-1">{parent.full_name}</h1>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-6 text-indigo-500">Parent Profile</p>

                      <button 
                        onClick={() => setShowEditModal(true)}
                        className="w-full py-3 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-xl font-bold transition-colors text-sm flex items-center justify-center gap-2"
                      >
                          <i className="fa-solid fa-pen-to-square text-xs"></i> Edit Profile
                      </button>
                  </div>

                  <div className="mt-8 space-y-4 border-t border-slate-50 dark:border-slate-800 pt-8">
                      <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center text-blue-500">
                              <i className="fa-solid fa-envelope text-xs"></i>
                          </div>
                          <div className="flex-1 min-w-0">
                              <p className="text-[10px] font-bold text-slate-400 uppercase">Email</p>
                              <p className="text-xs font-bold text-slate-700 dark:text-slate-300 truncate">{parent.email}</p>
                          </div>
                      </div>
                      <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-500">
                              <i className="fa-solid fa-phone text-xs"></i>
                          </div>
                          <div className="flex-1 min-w-0">
                              <p className="text-[10px] font-bold text-slate-400 uppercase">Phone</p>
                              <p className="text-xs font-bold text-slate-700 dark:text-slate-300">{parent.phone_number || 'Not provided'}</p>
                          </div>
                      </div>
                      <div className="flex items-start gap-3">
                          <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center text-amber-500 flex-shrink-0">
                              <i className="fa-solid fa-location-dot text-xs"></i>
                          </div>
                          <div className="flex-1">
                              <p className="text-[10px] font-bold text-slate-400 uppercase">Address</p>
                              <p className="text-xs font-bold text-slate-700 dark:text-slate-300 leading-relaxed">{parent.home_address || 'Not provided'}</p>
                          </div>
                      </div>
                  </div>
              </div>
          </div>

          <div className="lg:col-span-2 space-y-8">
              <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800">
                  <div className="flex items-center justify-between mb-8">
                      <h2 className="text-xl font-black text-slate-900 dark:text-white flex items-center gap-3">
                          <i className="fa-solid fa-children text-rose-500"></i>
                          Linked Children
                      </h2>
                      <button 
                        onClick={fetchAvailableChildren}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-2"
                      >
                          <i className="fa-solid fa-plus"></i> Link Child
                      </button>
                  </div>

                  {parent.children.length === 0 ? (
                      <div className="text-center py-16">
                          <p className="text-slate-400 font-bold text-sm">No children linked to this parent account.</p>
                      </div>
                  ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {parent.children.map((rel, index) => (
                              <div key={index} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex items-center justify-between group/item">
                                  <div className="flex items-center gap-4">
                                      <div className="w-12 h-12 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400 font-black overflow-hidden">
                                          {rel.child.profile_photo_url ? <img src={rel.child.profile_photo_url} className="w-full h-full object-cover" /> : rel.child.first_name.charAt(0)}
                                      </div>
                                      <div>
                                          <p className="text-sm font-bold text-slate-900 dark:text-white">{rel.child.first_name} {rel.child.last_name}</p>
                                          <div className="flex items-center gap-2 mt-0.5">
                                              <span className="text-[10px] font-bold text-slate-400 uppercase">{rel.relationship_type}</span>
                                              <span className={`w-1.5 h-1.5 rounded-full ${rel.child.status === 'active' ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
                                          </div>
                                      </div>
                                  </div>
                                  <Link href={`/dashboard/students/${rel.child.child_id}`} className="w-8 h-8 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-400 hover:text-emerald-500 transition-colors opacity-0 group-hover/item:opacity-100 shadow-sm">
                                      <i className="fa-solid fa-arrow-right text-[10px]"></i>
                                  </Link>
                              </div>
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
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Edit Parent</h3>
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
                                    parent.profile_photo_url ? (
                                        <img src={parent.profile_photo_url} className="w-full h-full object-cover" />
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
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Home Address</label>
                        <input 
                            type="text" 
                            value={editForm.home_address}
                            onChange={(e) => setEditForm({...editForm, home_address: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>

                    <button 
                        type="submit" 
                        className="w-full py-4 mt-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98]"
                    >
                        Save Changes
                    </button>
                </form>
            </div>
        </div>
      )}

      {/* Link Child Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-8 shadow-2xl border border-slate-100 dark:border-slate-800">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Link Child to Parent</h3>
                    <button onClick={() => setShowLinkModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-red-50 hover:text-red-500 transition-colors">
                        <i className="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <form onSubmit={handleLinkSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Select Child</label>
                        <select 
                            required
                            value={linkData.child_id}
                            onChange={(e) => setLinkData({...linkData, child_id: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white appearance-none"
                        >
                            <option value="">Choose a child...</option>
                            {availableChildren.map(c => (
                                <option key={c.child_id} value={c.child_id}>{c.first_name} {c.last_name} ({c.age_label})</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Relationship Type</label>
                        <input 
                            type="text" 
                            required
                            value={linkData.relationship_type}
                            onChange={(e) => setLinkData({...linkData, relationship_type: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 dark:text-white"
                            placeholder="e.g. Mother, Father, Guardian"
                        />
                    </div>
                    <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Emergency Contact</span>
                        <button 
                            type="button"
                            onClick={() => setLinkData({...linkData, is_emergency_contact: !linkData.is_emergency_contact})}
                            className={`w-12 h-6 rounded-full transition-colors relative ${linkData.is_emergency_contact ? 'bg-emerald-500' : 'bg-slate-300'}`}
                        >
                            <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${linkData.is_emergency_contact ? 'left-7' : 'left-1'}`}></div>
                        </button>
                    </div>

                    <button 
                        type="submit" 
                        className="w-full py-4 mt-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98]"
                    >
                        Create Relationship
                    </button>
                </form>
            </div>
        </div>
      )}
    </div>
  );
}
