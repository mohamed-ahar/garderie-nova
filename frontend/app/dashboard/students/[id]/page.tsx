"use client";

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import api from '../../../../lib/axios';

interface Parent {
  full_name: string;
  relationship_type: string;
  is_emergency_contact: boolean;
  phone: string;
}

interface ChildDetail {
  child_id: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  profile_photo_url: string;
  age_label: string;
  group_name: string | null;
  assigned_group: string | null;
  educator_name: string | null;
  status: string;
  medical_info: any;
  parents: Parent[];
}

export default function StudentProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const childId = unwrappedParams.id;
  const [child, setChild] = useState<ChildDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Edit State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState<{
      first_name: string;
      last_name: string;
      birth_date: string;
      status: string;
      medical_info_str: string;
      profile_photo: File | null;
  }>({
      first_name: '',
      last_name: '',
      birth_date: '',
      status: 'active',
      medical_info_str: '{}',
      profile_photo: null
  });

  useEffect(() => {
    fetchChildDetails();
  }, [childId]);

  const fetchChildDetails = async () => {
    try {
      const response = await api.get(`/api/children/${childId}/`);
      setChild(response.data);
      // Initialize edit form
      setEditForm({
          first_name: response.data.first_name,
          last_name: response.data.last_name,
          birth_date: response.data.birth_date,
          status: response.data.status,
          medical_info_str: JSON.stringify(response.data.medical_info, null, 2),
          profile_photo: null
      });
    } catch (error) {
      console.error('Error fetching child details', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
          let parsedMedicalInfo = {};
          try {
              parsedMedicalInfo = JSON.parse(editForm.medical_info_str);
          } catch (e) {
              alert("Invalid JSON in Medical Info");
              return;
          }

          const formData = new FormData();
          formData.append('first_name', editForm.first_name);
          formData.append('last_name', editForm.last_name);
          formData.append('birth_date', editForm.birth_date);
          formData.append('status', editForm.status);
          formData.append('medical_info', JSON.stringify(parsedMedicalInfo)); // Model expects JSONField, but standard form data sends string. DRF should parse it if configured or we send application/json. 
          // Wait, sending FormData means 'multipart/form-data'. 
          // DRF's JSONField might not automatically parse a string from form-data if the serializer field is JSONField. 
          // Usually better to use 'api.patch' with JSON if no file, but with file we must use FormData.
          // To send JSON in FormData for DRF, it's often tricky. 
          // However, 'medical_info' is a JSONField. sending a string usually works if DRF matches it. 
          // Let's try sending the stringified JSON.
          
          if (editForm.profile_photo) {
              formData.append('profile_photo', editForm.profile_photo);
          }

          // We need to set content-type to multipart/form-data explicitly or let axios do it
          const response = await api.patch(`/api/children/${childId}/`, formData, {
              headers: {
                  'Content-Type': 'multipart/form-data',
              },
          });
          setChild(response.data);
          setShowEditModal(false);
      } catch (error) {
          console.error('Error updating child', error);
          alert('Failed to update child.');
      }
  };

  if (loading) return <div className="p-12 text-center"><i className="fa-solid fa-circle-notch fa-spin text-emerald-500 text-3xl"></i></div>;
  if (!child) return <div className="p-12 text-center text-slate-500">Child not found</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
       <Link href="/dashboard/students" className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-emerald-600 mb-6 transition-colors">
         <i className="fa-solid fa-arrow-left"></i> Back to Students
      </Link>

      {/* Header Card */}
      <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800 mb-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5">
              <i className="fa-solid fa-child-reaching text-9xl"></i>
          </div>
          
          <div className="flex flex-col md:flex-row gap-8 relative z-10">
              <div className="w-32 h-32 rounded-[2rem] bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400 text-4xl font-black shadow-lg">
                  {child.profile_photo_url ? (
                      <img src={child.profile_photo_url} alt={child.first_name} className="w-full h-full object-cover rounded-[2rem]" />
                  ) : (
                      child.first_name.charAt(0)
                  )}
              </div>
              
              <div className="flex-1">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                      <div>
                          <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tighter mb-1">
                              {child.first_name} {child.last_name}
                          </h1>
                          <p className="text-slate-500 font-bold flex items-center gap-2">
                              <i className="fa-solid fa-cake-candles text-rose-400"></i>
                              {child.birth_date} 
                              <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs text-slate-600 dark:text-slate-300 ml-2">
                                  {child.age_label} old
                              </span>
                          </p>
                      </div>
                      <div className="flex gap-2">
                          <button 
                            onClick={() => {
                                setEditForm({
                                    first_name: child.first_name,
                                    last_name: child.last_name,
                                    birth_date: child.birth_date,
                                    status: child.status,
                                    medical_info_str: JSON.stringify(child.medical_info, null, 2),
                                    profile_photo: null
                                });
                                setShowEditModal(true);
                            }}
                            className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-200 transition-colors text-sm"
                          >
                              <i className="fa-solid fa-pen-to-square mr-2"></i> Edit
                          </button>
                      </div>
                  </div>

                  <div className="flex flex-wrap gap-4">
                       <div className="px-4 py-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex items-center gap-3">
                           <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center">
                               <i className="fa-solid fa-users-rectangle text-xs"></i>
                           </div>
                           <div>
                               <p className="text-[10px] font-bold text-slate-400 uppercase">Group</p>
                               <p className="text-sm font-bold text-slate-800 dark:text-white">
                                   {child.group_name ? (
                                       <Link href={`/dashboard/groups/${child.assigned_group}`} className="hover:text-emerald-500 underline decoration-dotted">
                                           {child.group_name}
                                       </Link>
                                   ) : 'Unassigned'}
                               </p>
                           </div>
                       </div>

                       <div className="px-4 py-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex items-center gap-3">
                           <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
                               <i className="fa-solid fa-chalkboard-user text-xs"></i>
                           </div>
                           <div>
                               <p className="text-[10px] font-bold text-slate-400 uppercase">Educator</p>
                               <p className="text-sm font-bold text-slate-800 dark:text-white">{child.educator_name || 'None'}</p>
                           </div>
                       </div>

                       <div className="px-4 py-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex items-center gap-3">
                           <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center">
                               <i className="fa-solid fa-circle-info text-xs"></i>
                           </div>
                           <div>
                               <p className="text-[10px] font-bold text-slate-400 uppercase">Status</p>
                               <p className="text-sm font-bold text-slate-800 dark:text-white capitalize">{child.status}</p>
                           </div>
                       </div>
                  </div>
              </div>
          </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Medical Info */}
          <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800">
              <h2 className="text-xl font-black text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                  <i className="fa-solid fa-notes-medical text-rose-500"></i> Medical Info
              </h2>
              
              {Object.keys(child.medical_info).length > 0 ? (
                  <div className="space-y-4">
                      <pre className="text-xs bg-slate-50 dark:bg-slate-950 p-4 rounded-xl overflow-x-auto text-slate-600 dark:text-slate-400 whitespace-pre-wrap">
                          {JSON.stringify(child.medical_info, null, 2)}
                      </pre>
                  </div>
              ) : (
                  <p className="text-slate-400 text-center py-8 italic">No medical information recorded.</p>
              )}
          </div>

          {/* Family / Parents */}
          <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800">
              <h2 className="text-xl font-black text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                  <i className="fa-solid fa-house-user text-indigo-500"></i> Family & Contacts
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {child.parents.length > 0 ? child.parents.map((parent, index) => (
                      <div key={index} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex items-center gap-4">
                          <div className="w-12 h-12 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-lg">
                              {parent.full_name.charAt(0)}
                          </div>
                          <div>
                              <p className="font-bold text-slate-900 dark:text-white">{parent.full_name}</p>
                              <p className="text-xs font-bold text-slate-500 uppercase">{parent.relationship_type}</p>
                              <div className="flex items-center gap-3 mt-1">
                                  <a href={`tel:${parent.phone}`} className="text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-2 py-1 rounded-lg text-slate-600 hover:text-emerald-600 transition-colors">
                                      <i className="fa-solid fa-phone mr-1"></i> {parent.phone}
                                  </a>
                                  {parent.is_emergency_contact && (
                                      <span className="text-[10px] bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-bold uppercase">
                                          Emergency
                                      </span>
                                  )}
                              </div>
                          </div>
                      </div>
                  )) : (
                      <p className="text-slate-400 italic">No parent profiles linked.</p>
                  )}
              </div>
          </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-lg p-8 shadow-2xl border border-slate-100 dark:border-slate-800 max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white">Edit Student Profile</h3>
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
                                    child.profile_photo_url ? (
                                        <img src={child.profile_photo_url} className="w-full h-full object-cover" />
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

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">First Name</label>
                            <input 
                                type="text" 
                                required
                                value={editForm.first_name}
                                onChange={(e) => setEditForm({...editForm, first_name: e.target.value})}
                                className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Last Name</label>
                            <input 
                                type="text" 
                                required
                                value={editForm.last_name}
                                onChange={(e) => setEditForm({...editForm, last_name: e.target.value})}
                                className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Date of Birth</label>
                        <input 
                            type="date" 
                            required
                            value={editForm.birth_date}
                            onChange={(e) => setEditForm({...editForm, birth_date: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Status</label>
                        <select 
                            value={editForm.status}
                            onChange={(e) => setEditForm({...editForm, status: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-bold text-slate-700 dark:text-white"
                        >
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="pending">Pending</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Medical Info (JSON)</label>
                        <textarea 
                            rows={5}
                            value={editForm.medical_info_str}
                            onChange={(e) => setEditForm({...editForm, medical_info_str: e.target.value})}
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none focus:ring-2 focus:ring-emerald-500 outline-none font-mono text-xs text-slate-700 dark:text-white"
                        />
                        <p className="text-[10px] text-slate-400 mt-1">Must be valid JSON. e.g. {"{\"allergies\": \"Peanuts\"}"}</p>
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