// frontend/src/contexts/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  created_at: string;
  last_login?: string;
  position_limit: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    username: string,
    password: string,
    fullName?: string,
    positionLimit?: number
  ) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = '/api/v1';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Al cargar la app, verificar si hay token guardado
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      fetchUserProfile(savedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUserProfile = async (authToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token inválido, limpiar
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
  setIsLoading(true);
  console.log('🔄 Attempting login...', { email }); // DEBUG

  try {
    console.log('📡 Making request to:', `${API_BASE_URL}/auth/login`); // DEBUG

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
      signal: controller.signal,  // Add timeout
    });

    clearTimeout(timeoutId);

    console.log('📨 Response status:', response.status); // DEBUG
    console.log('📨 Response ok:', response.ok); // DEBUG

    if (!response.ok) {
      const errorData = await response.json();
      console.error('❌ Login error:', errorData); // DEBUG
      throw new Error(errorData.detail || 'Login failed');
    }

    const data = await response.json();
    console.log('✅ Login success:', data); // DEBUG

    const { access_token, user: userData } = data;

    setToken(access_token);
    setUser(userData);
    localStorage.setItem('token', access_token);

    console.log('✅ Login completed successfully'); // DEBUG

  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('💥 Login timeout after 10 seconds'); // DEBUG
      throw new Error('Login request timed out. Please check your connection.');
    }
    console.error('💥 Login error:', error); // DEBUG
    throw error;
  } finally {
    setIsLoading(false);
  }
};

  const register = async (
    email: string,
    username: string,
    password: string,
    fullName?: string,
    positionLimit: number = 7
  ) => {
  setIsLoading(true);
  console.log('🔄 Attempting registration...', { email, username, fullName }); // DEBUG

  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        username,
        password,
        full_name: fullName,
        position_limit: positionLimit,
      }),
    });

    console.log('📨 Registration response status:', response.status); // DEBUG

    if (!response.ok) {
      const errorData = await response.json();
      console.error('❌ Registration error details:', errorData); // DEBUG

      // Mostrar el error específico
      if (errorData.detail && Array.isArray(errorData.detail)) {
        // Error de validación de Pydantic
        const errors = errorData.detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`);
        throw new Error(errors.join(', '));
      } else {
        throw new Error(errorData.detail?.message || errorData.detail || 'Registration failed');
      }
    }

    const data = await response.json();
    console.log('✅ Registration success:', data); // DEBUG
    return data;
  } catch (error) {
    console.error('💥 Registration error:', error); // DEBUG
    throw error;
  } finally {
    setIsLoading(false);
  }
};

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  const value = {
    user,
    token,
    login,
    register,
    logout,
    isLoading,
    isAuthenticated: !!user && !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};