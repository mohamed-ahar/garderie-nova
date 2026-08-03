"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api from '../lib/axios';

export interface User {
  user_id: string;
  email: string;
  full_name: string;
  role_type: 'owner' | 'director' | 'vice_director' | 'educator' | 'parent';
  role_display: string;
  profile_photo_url: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  logout: () => void;
  hasRole: (roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Check if we have a token
    const token = localStorage.getItem('access_token');
    if (!token) {
        setLoading(false);
        // If we are in a protected route, redirect to login is handled by the page or middleware usually, 
        // but here we just ensure we know we aren't logged in.
        return;
    }

    const fetchUser = async () => {
      try {
        const response = await api.get('/api/me/');
        setUser(response.data);
      } catch (error) {
        console.error('Error fetching user:', error);
        // If error (e.g. 401), the axios interceptor might handle redirect, 
        // but we should update state.
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []); // Run once on mount

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    router.push('/login');
  };

  const hasRole = (roles: string[]) => {
    if (!user) return false;
    return roles.includes(user.role_type);
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
