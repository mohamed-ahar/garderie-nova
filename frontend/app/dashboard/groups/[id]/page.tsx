"use client";

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import api from '../../../../lib/axios';

interface Room {
  room_id: string;
  name: string;
  fire_capacity: number;
  assigned_group_id: string | null;
  assigned_group_name: string | null;
}

interface Group {
  group_id: string;
  name: string;
  room: string | null; // Room ID
  room_name: string | null;
  current_occupancy: number;
  current_educators: number;
  current_total_points: number;
  required_educators: number;
  is_compliant: boolean;
  calculated_max_capacity: number;
}

interface Child {
  child_id: string;
  first_name: string;
  last_name: string;
  profile_photo_url: string;
  age_label: string;
  assigned_educator: string | null;
  educator_name: string | null;
  assigned_group: string | null;
  group_name: string | null;
}

interface Educator {
  user_id: string;
  full_name: string;
  qualification_level: string;
  current_group_id: string | null;
  current_group_name: string | null;
}

export default function GroupManagePage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const groupId = unwrappedParams.id;
  const [group, setGroup] = useState<Group | null>(null);
  const [assignedChildren, setAssignedChildren] = useState<Child[]>([]);
  const [assignedEducators, setAssignedEducators] = useState<Educator[]>([]);
  
  const [allChildren, setAllChildren] = useState<Child[]>([]);
  const [allEducators, setAllEducators] = useState<Educator[]>([]);
  const [allRooms, setAllRooms] = useState<Room[]>([]);
  
  const [showChildModal, setShowChildModal] = useState(false);
  const [showEducatorModal, setShowEducatorModal] = useState(false);
  const [showRoomModal, setShowRoomModal] = useState(false);

  useEffect(() => {
    fetchGroupDetails();
    fetchAssignedChildren();
    fetchAssignedEducators();
    fetchAllChildren();
    fetchAllEducators();
    fetchAllRooms();
  }, [groupId]);

  const fetchGroupDetails = async () => {
    try {
      const response = await api.get(`/api/groups/${groupId}/`);
      setGroup(response.data);
    } catch (error) {
      console.error('Error fetching group:', error);
    }
  };

  const fetchAssignedChildren = async () => {
    try {
      const response = await api.get(`/api/groups/${groupId}/children/`);
      setAssignedChildren(response.data);
    } catch (error) {
        console.error('Error fetching assigned children', error);
    }
  };

  const fetchAssignedEducators = async () => {
     try {
        const response = await api.get(`/api/groups/${groupId}/educators/`);
        setAssignedEducators(response.data);
     } catch (error) {
         console.error('Error fetching assigned educators', error);
     }
  };
  
  const fetchAllChildren = async () => {
      try {
          const response = await api.get('/api/children/available/');
          setAllChildren(response.data);
      } catch (error) {
          console.error('Error fetching all children', error);
      }
  };

  const fetchAllEducators = async () => {
      try {
          const response = await api.get('/api/educators/available/');
          setAllEducators(response.data);
      } catch (error) {
          console.error('Error fetching all educators', error);
      }
  };

  const fetchAllRooms = async () => {
      try {
          const response = await api.get('/api/rooms/');
          setAllRooms(response.data);
      } catch (error) {
          console.error('Error fetching rooms', error);
      }
  };

  const assignChild = async (child: Child) => {
      if (child.assigned_group && child.assigned_group !== groupId) {
          if (!confirm(`This child is currently assigned to ${child.group_name}. Do you want to move them here?`)) {
              return;
          }
      }

      try {
          await api.post(`/api/groups/${groupId}/assign_child/`, { child_id: child.child_id });
          fetchAssignedChildren();
          fetchGroupDetails(); 
          fetchAllChildren(); // Refresh available list status
          setShowChildModal(false);
      } catch (error) {
          console.error('Error assigning child', error);
      }
  };

  const removeChild = async (childId: string) => {
      try {
           await api.post(`/api/groups/${groupId}/remove_child/`, { child_id: childId });
           fetchAssignedChildren();
           fetchGroupDetails();
           fetchAllChildren();
      } catch (error) {
          console.error('Error removing child', error);
      }
  };

  const assignEducator = async (educator: Educator) => {
      if (educator.current_group_id && educator.current_group_id !== groupId) {
           if (!confirm(`This educator is currently assigned to ${educator.current_group_name}. Do you want to move them here?`)) {
               return;
           }
      }

      try {
          await api.post(`/api/groups/${groupId}/assign_educator/`, { user_id: educator.user_id });
          fetchAssignedEducators();
          fetchGroupDetails();
          fetchAllEducators(); // Refresh status
          setShowEducatorModal(false);
      } catch (error) {
          console.error('Error assigning educator', error);
      }
  };

  const removeEducator = async (userId: string) => {
      try {
          await api.post(`/api/groups/${groupId}/remove_educator/`, { user_id: userId });
          fetchAssignedEducators();
          fetchGroupDetails();
          fetchAllEducators();
      } catch (error) {
          console.error('Error removing educator', error);
      }
  };

  const assignEducatorToChild = async (childId: string, educatorId: string) => {
      try {
          await api.post(`/api/groups/${groupId}/assign_educator_to_child/`, { 
              child_id: childId, 
              user_id: educatorId || null 
          });
          fetchAssignedChildren(); 
      } catch (error) {
          console.error('Error assigning educator to child', error);
      }
  };
  
  const updateGroupRoom = async (roomId: string) => {
      const room = allRooms.find(r => r.room_id === roomId);
      if (room && room.assigned_group_id && room.assigned_group_id !== groupId) {
           if (!confirm(`Room ${room.name} is currently occupied by ${room.assigned_group_name}. Do you want to reassign it to this group?`)) {
               return;
           }
      }
      
      try {
          await api.post(`/api/groups/${groupId}/update_room/`, { room_id: roomId });
          fetchGroupDetails();
          fetchAllRooms();
          setShowRoomModal(false);
      } catch (error) {
          console.error('Error updating room', error);
      }
  };

  if (!group) return <div className="p-8 text-center">Loading...</div>;

  // Filter out children/educators already in THIS group to avoid duplicate addition in modal
  const candidatesChildren = allChildren.filter(c => c.assigned_group !== groupId);
  const candidatesEducators = allEducators.filter(e => e.current_group_id !== groupId);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link href="/dashboard/groups" className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-emerald-600 mb-6 transition-colors">
         <i className="fa-solid fa-arrow-left"></i> Back to Groups
      </Link>

      <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 shadow-xl border border-slate-100 dark:border-slate-800 mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                  <div className="flex items-center gap-4 mb-2">
                    <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">{group.name}</h1>
                    <button 
                        onClick={() => setShowRoomModal(true)}
                        className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors text-xs font-bold text-slate-600 dark:text-slate-300"
                    >
                        <i className="fa-solid fa-door-open"></i>
                        {group.room_name || "Assign Room"}
                    </button>
                  </div>
                  <p className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mt-1">
                      Capacité Max: <span className="text-emerald-600 dark:text-emerald-400">{group.calculated_max_capacity} enfants</span>
                  </p>
                  <div className="mt-4 flex items-center gap-3">
                      <span className={`px-4 py-1.5 rounded-xl text-xs font-bold uppercase tracking-wider ${group.is_compliant ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'}`}>
                          {group.is_compliant ? 'Conforme' : 'Non Conforme'}
                      </span>
                      {!group.is_compliant && (
                          <span className="text-xs font-bold text-red-500">
                             {group.current_educators < group.required_educators ? `Besoin de ${group.required_educators} éducateurs` : 'Vérifiez le mixage ou la capacité'}
                          </span>
                      )}
                  </div>
              </div>
              <div className="flex gap-4">
                  <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 text-center min-w-[100px]">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Ratio Total</p>
                      <p className="text-2xl font-black text-slate-900 dark:text-white">{(group.current_total_points / 1000).toFixed(3)}</p>
                      <p className="text-[10px] text-slate-500 font-bold">Points</p>
                  </div>
                   <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 text-center min-w-[100px]">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Requis</p>
                      <p className="text-2xl font-black text-slate-900 dark:text-white">{group.required_educators}</p>
                      <p className="text-[10px] text-slate-500 font-bold">Éducateurs</p>
                  </div>
                  <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 text-center min-w-[100px]">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Présents</p>
                      <p className={`text-2xl font-black ${group.current_educators < group.required_educators ? 'text-red-500' : 'text-emerald-500'}`}>{group.current_educators}</p>
                      <p className="text-[10px] text-slate-500 font-bold">Éducateurs</p>
                  </div>
              </div>
          </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* EDUCATORS SECTION */}
          <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-100 dark:border-slate-800 shadow-xl overflow-hidden flex flex-col">
              <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-950/50">
                  <h2 className="text-lg font-black text-slate-800 dark:text-white flex items-center gap-2">
                      <i className="fa-solid fa-user-tie text-emerald-500"></i> Éducateurs
                  </h2>
                  <button onClick={() => setShowEducatorModal(true)} className="w-8 h-8 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-colors shadow-sm">
                      <i className="fa-solid fa-plus text-xs"></i>
                  </button>
              </div>
              <div className="p-4 flex-1 overflow-y-auto max-h-[500px]">
                  {assignedEducators.length === 0 ? (
                      <p className="text-center text-slate-400 py-8 text-sm">Aucun éducateur assigné.</p>
                  ) : (
                      <div className="space-y-3">
                          {assignedEducators.map(educator => (
                              <div key={educator.user_id} className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                                  <div className="flex items-center gap-3">
                                      <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold">
                                          {educator.full_name.charAt(0)}
                                      </div>
                                      <div>
                                          <p className="text-sm font-bold text-slate-900 dark:text-white">{educator.full_name}</p>
                                          <p className="text-[10px] text-slate-500 uppercase font-bold">{educator.qualification_level}</p>
                                      </div>
                                  </div>
                                  <button onClick={() => removeEducator(educator.user_id)} className="text-slate-400 hover:text-red-500 transition-colors p-2">
                                      <i className="fa-solid fa-xmark"></i>
                                  </button>
                              </div>
                          ))}
                      </div>
                  )}
              </div>
          </div>

          {/* CHILDREN SECTION */}
          <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-100 dark:border-slate-800 shadow-xl overflow-hidden flex flex-col">
              <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-950/50">
                  <h2 className="text-lg font-black text-slate-800 dark:text-white flex items-center gap-2">
                      <i className="fa-solid fa-children text-rose-500"></i> Enfants <span className="text-xs text-slate-400 ml-2">({group.current_occupancy}/{group.calculated_max_capacity})</span>
                  </h2>
                  <button onClick={() => setShowChildModal(true)} className="w-8 h-8 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-colors shadow-sm">
                      <i className="fa-solid fa-plus text-xs"></i>
                  </button>
              </div>
              <div className="p-4 flex-1 overflow-y-auto max-h-[500px]">
                  {assignedChildren.length === 0 ? (
                      <p className="text-center text-slate-400 py-8 text-sm">Aucun enfant inscrit.</p>
                  ) : (
                      <div className="space-y-3">
                          {assignedChildren.map(child => (
                              <div key={child.child_id} className="flex flex-col gap-2 p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                                  <div className="flex items-center justify-between">
                                      <div className="flex items-center gap-3">
                                          <div className="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400 font-bold overflow-hidden">
                                              {child.profile_photo_url ? <img src={child.profile_photo_url} alt="" className="w-full h-full object-cover" /> : child.first_name.charAt(0)}
                                          </div>
                                          <div>
                                              <p className="text-sm font-bold text-slate-900 dark:text-white">{child.first_name} {child.last_name}</p>
                                              <div className="flex items-center gap-2 mt-0.5">
                                                 <span className="text-[10px] font-bold text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-lg">{child.age_label}</span>
                                              </div>
                                          </div>
                                      </div>
                                      <button onClick={() => removeChild(child.child_id)} className="text-slate-400 hover:text-red-500 transition-colors p-2">
                                          <i className="fa-solid fa-xmark"></i>
                                      </button>
                                  </div>
                                  
                                  {/* Educator Assignment */}
                                  <div className="mt-2 pl-12 flex items-center gap-2">
                                      <i className="fa-solid fa-chalkboard-user text-slate-400 text-xs"></i>
                                      <select 
                                          value={child.assigned_educator || ""} 
                                          onChange={(e) => assignEducatorToChild(child.child_id, e.target.value)}
                                          className="text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 text-slate-600 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                      >
                                          <option value="">Aucun éducateur</option>
                                          {assignedEducators.map(edu => (
                                              <option key={edu.user_id} value={edu.user_id}>{edu.full_name}</option>
                                          ))}
                                      </select>
                                  </div>
                              </div>
                          ))}
                      </div>
                  )}
              </div>
          </div>
      </div>

      {/* MODALS */}
      {showEducatorModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
              <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-6 shadow-2xl">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-black text-slate-900 dark:text-white">Assign Educator</h3>
                      <button onClick={() => setShowEducatorModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                          <i className="fa-solid fa-xmark"></i>
                      </button>
                  </div>
                  <div className="max-h-80 overflow-y-auto space-y-2">
                      {candidatesEducators.length === 0 ? <p className="text-slate-500 text-center">No available educators found.</p> : 
                        candidatesEducators.map(e => (
                          <button key={e.user_id} onClick={() => assignEducator(e)} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left group">
                              <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 font-bold">
                                  {e.full_name.charAt(0)}
                              </div>
                              <div className="flex-1">
                                  <div className="flex justify-between items-center">
                                    <p className="font-bold text-slate-800 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400">{e.full_name}</p>
                                    {e.current_group_name && (
                                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                                            In: {e.current_group_name}
                                        </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-500">{e.qualification_level || "No Qual."}</p>
                              </div>
                          </button>
                        ))
                      }
                  </div>
              </div>
          </div>
      )}

      {showChildModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
              <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-6 shadow-2xl">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-black text-slate-900 dark:text-white">Enroll Child</h3>
                      <button onClick={() => setShowChildModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                          <i className="fa-solid fa-xmark"></i>
                      </button>
                  </div>
                  <div className="max-h-80 overflow-y-auto space-y-2">
                      {candidatesChildren.length === 0 ? <p className="text-slate-500 text-center">No available children found.</p> : 
                        candidatesChildren.map(c => (
                          <button key={c.child_id} onClick={() => assignChild(c)} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left group">
                              <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 font-bold overflow-hidden">
                                   {c.profile_photo_url ? <img src={c.profile_photo_url} alt="" className="w-full h-full object-cover" /> : c.first_name.charAt(0)}
                              </div>
                              <div className="flex-1">
                                  <div className="flex justify-between items-center">
                                      <p className="font-bold text-slate-800 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400">{c.first_name} {c.last_name}</p>
                                      {c.group_name && (
                                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                                                In: {c.group_name}
                                            </span>
                                      )}
                                  </div>
                                  <p className="text-xs text-slate-500">{c.age_label}</p>
                              </div>
                          </button>
                        ))
                      }
                  </div>
              </div>
          </div>
      )}

      {showRoomModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
              <div className="bg-white dark:bg-slate-900 rounded-[2rem] w-full max-w-md p-6 shadow-2xl">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-black text-slate-900 dark:text-white">Change Room</h3>
                      <button onClick={() => setShowRoomModal(false)} className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                          <i className="fa-solid fa-xmark"></i>
                      </button>
                  </div>
                  <div className="max-h-80 overflow-y-auto space-y-2">
                      {allRooms.length === 0 ? <p className="text-slate-500 text-center">No rooms found.</p> : 
                        allRooms.map(r => {
                            const isCurrent = r.room_id === group.room;
                            const isOccupied = r.assigned_group_id && !isCurrent;
                            
                            return (
                                <button 
                                    key={r.room_id} 
                                    onClick={() => !isCurrent && updateGroupRoom(r.room_id)} 
                                    disabled={isCurrent}
                                    className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors text-left group border ${isCurrent ? 'bg-emerald-50 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-800' : 'border-transparent hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                                >
                                    <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 font-bold">
                                        <i className="fa-solid fa-door-closed"></i>
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-center">
                                            <p className={`font-bold ${isCurrent ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-800 dark:text-white'}`}>{r.name}</p>
                                            {isOccupied && (
                                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                                                    Occupied: {r.assigned_group_name}
                                                </span>
                                            )}
                                            {isCurrent && (
                                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                                                    Current
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-xs text-slate-500">Capacity: {r.fire_capacity}</p>
                                    </div>
                                </button>
                            );
                        })
                      }
                  </div>
              </div>
          </div>
      )}
    </div>
  );
}