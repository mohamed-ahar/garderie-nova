"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import api from "../../../lib/axios";

interface Group {
  group_id: string;
  name: string;
  ratio_category: string;
  ratio_category_display: string;
  room: string | null;
  room_name: string;
  current_occupancy: number;
  current_educators: number;
  is_compliant: boolean;
}

interface Room {
  room_id: string;
  name: string;
}

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    ratio_category: "UNDER_24M",
    room: "",
  });

  const fetchGroups = async () => {
    try {
      const response = await api.get("/api/groups/");
      setGroups(response.data);
    } catch (error) {
      console.error("Error fetching groups:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRooms = async () => {
    try {
      const response = await api.get("/api/rooms/");
      setRooms(response.data);
    } catch (error) {
      console.error("Error fetching rooms:", error);
    }
  };

  useEffect(() => {
    fetchGroups();
    fetchRooms();
  }, []);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        name: formData.name,
        ratio_category: formData.ratio_category,
      };
      if (formData.room) {
        payload.room = formData.room;
      }

      await api.post("/api/groups/", payload);
      setShowForm(false);
      setFormData({ name: "", ratio_category: "UNDER_24M", room: "" });
      fetchGroups();
    } catch (error) {
      console.error("Error creating group:", error);
      alert("Failed to create group");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-black text-emerald-600 dark:text-white tracking-tighter">
            Group Management
          </h1>
          <p className="text-slate-500 text-sm dark:text-slate-400 font-medium">
            Manage daycare groups and ratios.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-2xl text-sm font-bold hover:bg-emerald-700 transition-all shadow-lg shadow-emerald-500/25 active:scale-95"
        >
          <i className={`fa-solid ${showForm ? "fa-minus" : "fa-plus"}`}></i>
          {showForm ? "Cancel" : "Add Group"}
        </button>
      </div>

      {showForm && (
        <div className="mb-8 bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-100 dark:border-slate-800 shadow-xl p-8 animate-in fade-in slide-in-from-top-4">
          <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-6">
            Create New Group
          </h2>
          <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2"
              >
                Group Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all dark:text-white"
                placeholder="e.g., Tiny Turtles"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label
                  htmlFor="ratio_category"
                  className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2"
                >
                  Ratio Category
                </label>
                <select
                  id="ratio_category"
                  name="ratio_category"
                  value={formData.ratio_category}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all dark:text-white"
                >
                  <option value="UNDER_24M">Under 24 Months</option>
                  <option value="MIXED_2_TO_4">Mixed 2-4 Years</option>
                  <option value="SCHOOL_AGE_5_PLUS">School Age 5+</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="room"
                  className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2"
                >
                  Assigned Room
                </label>
                <select
                  id="room"
                  name="room"
                  value={formData.room}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none transition-all dark:text-white"
                >
                  <option value="">-- Select Room --</option>
                  {rooms.map((room) => (
                    <option key={room.room_id} value={room.room_id}>
                      {room.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                className="px-8 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/25 transition-all active:scale-95"
              >
                Create Group
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white dark:bg-slate-900 rounded-[0.5rem] border border-slate-100 dark:border-slate-800 shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800">
                <th className="px-8 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                  Group Name
                </th>
                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                  Category
                </th>
                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                  Room
                </th>
                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                  Occupancy
                </th>
                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">
                  Status
                </th>
                <th className="px-6 py-5 text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-8 py-8 text-center text-slate-500"
                  >
                    Loading groups...
                  </td>
                </tr>
              ) : groups.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-8 py-8 text-center text-slate-500"
                  >
                    No groups found. Create one to get started.
                  </td>
                </tr>
              ) : (
                groups.map((group) => (
                  <tr
                    key={group.group_id}
                    className="group hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="px-8 py-5">
                      <a
                        key={group.group_id}
                        href={`/dashboard/groups/${group.group_id}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-bold text-lg">
                            {group.name.charAt(0)}
                          </div>
                          <span className="text-sm font-bold text-slate-900 dark:text-white">
                            {group.name}
                          </span>
                        </div>
                      </a>
                    </td>
                    <td className="px-6 py-5">
                      <span className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] font-bold rounded-lg uppercase">
                        {group.ratio_category_display}
                      </span>
                    </td>
                    <td className="px-6 py-5">
                      <span className="text-sm font-medium text-slate-600 dark:text-slate-300">
                        {group.room_name || "Unassigned"}
                      </span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-900 dark:text-white">
                          {group.current_occupancy}
                        </span>
                        <span className="text-xs text-slate-400">Children</span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            group.is_compliant ? "bg-emerald-500" : "bg-red-500"
                          } animate-pulse`}
                        ></span>
                        <span
                          className={`text-xs font-bold ${
                            group.is_compliant
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-red-600 dark:text-red-400"
                          }`}
                        >
                          {group.is_compliant ? "Compliant" : "Issue"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <Link
                        href={`/dashboard/groups/${group.group_id}`}
                        className="inline-flex items-center justify-center px-4 py-2 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-bold rounded-xl hover:bg-emerald-100 dark:hover:bg-emerald-500/20 transition-colors"
                      >
                        Manage
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
