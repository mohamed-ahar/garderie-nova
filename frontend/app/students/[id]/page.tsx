"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { use, useEffect, useState } from 'react';
import api from '@/lib/axios';

interface Parent {
    full_name: string;
    relationship_type: string;
    is_emergency_contact: boolean;
    phone: string;
}

interface Child {
    child_id: string;
    first_name: string;
    last_name: string;
    birth_date: string;
    profile_photo_url: string | null;
    assigned_group: string | null;
    group_name: string | null;
    age_label: string;
    medical_info: Record<string, any>;
    status: string;
    parents: Parent[];
}

export default function StudentProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  // Unwrap params using React.use()
  const { id } = use(params);

  const [student, setStudent] = useState<Child | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
      const fetchStudent = async () => {
          try {
              const response = await api.get(`/api/children/${id}/`);
              setStudent(response.data);
          } catch (err) {
              console.error("Failed to fetch student:", err);
              setError("Impossible de charger les données de l'enfant.");
          } finally {
              setLoading(false);
          }
      };

      if (id) {
          fetchStudent();
      }
  }, [id]);

  if (loading) {
      return <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
      </div>;
  }

  if (error || !student) {
      return <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
          <div className="text-center">
              <p className="text-red-500 font-bold mb-4">{error || "Enfant introuvable"}</p>
              <Link href="/dashboard" className="px-4 py-2 bg-emerald-500 text-white rounded-xl">Retour au tableau de bord</Link>
          </div>
      </div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans"
         style={{
             backgroundImage: `radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent), radial-gradient(circle at bottom left, rgba(5, 150, 105, 0.05), transparent)`
         }}>
        
        <nav className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
            <Link href="/dashboard" className="group flex items-center gap-3 px-4 py-2 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800 transition-all hover:pr-6">
                <i className="fa-solid fa-chevron-left text-xs group-hover:-translate-x-1 transition-transform"></i>
                <span className="text-sm font-bold tracking-tight">Tableau de bord</span>
            </Link>
            
            <div className="flex gap-4">
                <button className="w-11 h-11 flex items-center justify-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-slate-500 hover:text-premium-600 transition-all">
                    <i className="fa-solid fa-share-nodes"></i>
                </button>
                <button className="flex items-center gap-2 px-6 py-2.5 bg-premium-900 dark:bg-white text-white dark:text-premium-900 rounded-2xl font-bold text-sm shadow-xl transition-all hover:scale-[1.02]">
                    <i className="fa-solid fa-file-pdf"></i>
                    Exporter Dossier
                </button>
            </div>
        </nav>

        <main className="max-w-7xl mx-auto px-6 pb-20">
            
            {/* Header Profile Card */}
            <div className="bg-white/70 dark:bg-slate-900/80 backdrop-blur-xl border border-white/80 dark:border-white/5 rounded-[3rem] p-10 mb-8 relative overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.04)]">
                <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full -mr-20 -mt-20 blur-3xl"></div>
                
                <div className="flex flex-col lg:flex-row items-center lg:items-end gap-10 relative">
                    <div className="relative">
                        <div className="w-40 h-40 rounded-[2.5rem] bg-gradient-to-tr from-emerald-500 to-blue-500 p-1 shadow-2xl overflow-hidden">
                            <img className="w-full h-full object-cover rounded-[2.3rem] bg-white" 
                                 src={student.profile_photo_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${student.first_name}`} 
                                 alt="Student" />
                        </div>
                        <div className="absolute -bottom-3 -right-3 bg-white dark:bg-slate-900 p-3 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800">
                            <i className="fa-solid fa-camera text-emerald-600"></i>
                        </div>
                    </div>

                    <div className="flex-1 text-center lg:text-left">
                        <div className="flex flex-col lg:flex-row lg:items-center gap-4 mb-4">
                            <h1 className="text-5xl font-black tracking-tighter capitalize">{student.first_name} {student.last_name}</h1>
                            <span className="inline-flex px-4 py-1.5 rounded-xl bg-emerald-100 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-xs font-black uppercase tracking-widest">
                                {student.status}
                            </span>
                        </div>
                        <div className="flex flex-wrap justify-center lg:justify-start gap-6 text-slate-500 dark:text-slate-400 font-medium">
                            <div className="flex items-center gap-2"><i className="fa-solid fa-calendar-day text-premium-600"></i> {student.age_label}</div>
                            <div className="flex items-center gap-2"><i className="fa-solid fa-id-card text-premium-600"></i> ID: {student.child_id.slice(0, 8).toUpperCase()}</div>
                            <div className="flex items-center gap-2"><i className="fa-solid fa-door-open text-premium-600"></i> Groupe: {student.group_name || "Non assigné"}</div>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button className="w-14 h-14 flex items-center justify-center rounded-3xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 border border-emerald-100 dark:border-emerald-500/20 hover:bg-emerald-600 hover:text-white transition-all">
                            <i className="fa-solid fa-phone"></i>
                        </button>
                        <button className="w-14 h-14 flex items-center justify-center rounded-3xl bg-blue-50 dark:bg-blue-500/10 text-blue-600 border border-blue-100 dark:border-blue-500/20 hover:bg-blue-600 hover:text-white transition-all">
                            <i className="fa-solid fa-envelope"></i>
                        </button>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                {/* Left Column Info */}
                <div className="lg:col-span-7 space-y-8">
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white/70 dark:bg-slate-900/80 backdrop-blur-xl border border-white/80 dark:border-white/5 p-8 rounded-[2.5rem] hover:shadow-2xl transition-all group shadow-[0_20px_50px_rgba(0,0,0,0.04)]">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="w-12 h-12 rounded-2xl bg-orange-100 dark:bg-orange-500/10 text-orange-600 flex items-center justify-center text-xl shadow-inner group-hover:scale-110 transition-transform">
                                    <i className="fa-solid fa-hand-dots"></i>
                                </div>
                                <h3 className="font-black text-lg tracking-tight">Santé & Alertes</h3>
                            </div>
                            <ul className="space-y-3">
                                {Object.keys(student.medical_info).length > 0 ? (
                                    Object.entries(student.medical_info).map(([key, value]) => (
                                        <li key={key} className="flex items-center gap-3 text-sm font-bold text-slate-600 dark:text-slate-300">
                                            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span> {key}: {String(value)}
                                        </li>
                                    ))
                                ) : (
                                    <li className="text-sm text-slate-400 italic">Aucune information médicale.</li>
                                )}
                            </ul>
                        </div>

                        <div className="bg-white/70 dark:bg-slate-900/80 backdrop-blur-xl border border-white/80 dark:border-white/5 p-8 rounded-[2.5rem] hover:shadow-2xl transition-all group shadow-[0_20px_50px_rgba(0,0,0,0.04)]">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-500/10 text-blue-600 flex items-center justify-center text-xl shadow-inner group-hover:scale-110 transition-transform">
                                    <i className="fa-solid fa-shield-heart"></i>
                                </div>
                                <h3 className="font-black text-lg tracking-tight">Garde & Parents</h3>
                            </div>
                            <div className="space-y-3">
                                {student.parents.length > 0 ? (
                                    student.parents.map((parent, idx) => (
                                        <div key={idx} className="border-b border-slate-100 dark:border-slate-800 pb-2 last:border-0 last:pb-0">
                                            <p className="text-sm font-black text-slate-900 dark:text-white">{parent.full_name}</p>
                                            <p className="text-[11px] font-bold text-slate-400 uppercase">{parent.relationship_type} {parent.is_emergency_contact && "(Urgence)"}</p>
                                            {parent.phone && <p className="text-xs text-slate-500">{parent.phone}</p>}
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-sm text-slate-400 italic">Aucun parent associé.</p>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="bg-white/70 dark:bg-slate-900/80 backdrop-blur-xl border border-white/80 dark:border-white/5 p-8 rounded-[3rem] shadow-[0_20px_50px_rgba(0,0,0,0.04)]">
                        <div className="flex justify-between items-center mb-10">
                            <h3 className="text-xl font-black tracking-tight">Performances & Éveil</h3>
                            <select className="bg-slate-50 dark:bg-slate-800 border-none text-xs font-bold rounded-xl px-4 py-2 outline-none">
                                <option>Derniers 30 jours</option>
                                <option>Dernier trimestre</option>
                            </select>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="h-32 bg-emerald-500/20 rounded-2xl border-b-4 border-emerald-500 flex flex-col items-center justify-center gap-2">
                                <span className="text-[10px] font-black text-emerald-700 uppercase">Social</span>
                                <span className="text-xl font-black text-emerald-900 dark:text-emerald-400">N/A</span>
                            </div>
                            <div className="h-32 bg-blue-500/20 rounded-2xl border-b-4 border-blue-500 flex flex-col items-center justify-center gap-2">
                                <span className="text-[10px] font-black text-blue-700 uppercase">Langue</span>
                                <span className="text-xl font-black text-blue-900 dark:text-blue-400">N/A</span>
                            </div>
                            <div className="h-32 bg-purple-500/20 rounded-2xl border-b-4 border-purple-500 flex flex-col items-center justify-center gap-2">
                                <span className="text-[10px] font-black text-purple-700 uppercase">Motricité</span>
                                <span className="text-xl font-black text-purple-900 dark:text-purple-400">N/A</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column Feed */}
                <div className="lg:col-span-5">
                    <div className="bg-white/70 dark:bg-slate-900/80 backdrop-blur-xl border border-white/80 dark:border-white/5 rounded-[3rem] p-10 h-full shadow-[0_20px_50px_rgba(0,0,0,0.04)]">
                        <h3 className="text-2xl font-black tracking-tighter mb-8">Flux d'Activité <span className="text-slate-300 ml-2">Live</span></h3>
                        
                        <div className="space-y-10 relative">
                            <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-emerald-500 via-slate-200 to-transparent dark:via-slate-800"></div>
                            
                            <div className="relative flex gap-8 group">
                                <div className="w-12 h-12 rounded-2xl bg-white dark:bg-slate-900 shadow-xl flex items-center justify-center text-emerald-600 z-10 border border-slate-100 dark:border-slate-800 transition-all group-hover:scale-110">
                                    <i className="fa-solid fa-utensils"></i>
                                </div>
                                <div>
                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Aujourd'hui, 12:30</span>
                                    <h4 className="font-bold text-slate-900 dark:text-white text-md">Repas terminé</h4>
                                    <p className="text-sm text-slate-500 mt-1">A mangé 100% de son plat de pâtes et légumes. Très enthousiaste.</p>
                                </div>
                            </div>

                            <div className="relative flex gap-8 group">
                                <div className="w-12 h-12 rounded-2xl bg-white dark:bg-slate-900 shadow-xl flex items-center justify-center text-blue-600 z-10 border border-slate-100 dark:border-slate-800 transition-all group-hover:scale-110">
                                    <i className="fa-solid fa-moon"></i>
                                </div>
                                <div>
                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Aujourd'hui, 13:45</span>
                                    <h4 className="font-bold text-slate-900 dark:text-white text-md">Début de sieste</h4>
                                    <p className="text-sm text-slate-500 mt-1">S'est endormi calmement après l'histoire.</p>
                                </div>
                            </div>

                            <div className="mt-12 p-6 bg-slate-50 dark:bg-slate-800/50 rounded-3xl border border-dashed border-slate-200 dark:border-slate-700">
                                <p className="text-xs font-bold text-slate-400 uppercase mb-4 text-center">Ajouter une note rapide</p>
                                <div className="flex gap-2">
                                    <button className="flex-1 p-3 bg-white dark:bg-slate-900 rounded-xl shadow-sm hover:border-emerald-500 border border-transparent transition-all"><i className="fa-solid fa-smile text-emerald-500"></i></button>
                                    <button className="flex-1 p-3 bg-white dark:bg-slate-900 rounded-xl shadow-sm hover:border-red-500 border border-transparent transition-all"><i className="fa-solid fa-frown text-red-500"></i></button>
                                    <button className="flex-1 p-3 bg-white dark:bg-slate-900 rounded-xl shadow-sm hover:border-blue-500 border border-transparent transition-all"><i className="fa-solid fa-bed text-blue-500"></i></button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>
  );
}