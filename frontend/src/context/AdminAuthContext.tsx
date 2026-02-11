import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { adminMe, adminLogin as apiAdminLogin, adminLogout as apiAdminLogout } from '../api/admin';

interface AdminAuthContextType {
  isAdmin: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthContextType>({
  isAdmin: false,
  loading: true,
  login: async () => {},
  logout: async () => {},
});

export const useAdminAuth = () => useContext(AdminAuthContext);

export const AdminAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  const checkAdmin = useCallback(async () => {
    try {
      await adminMe();
      setIsAdmin(true);
    } catch {
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAdmin();
  }, [checkAdmin]);

  const login = async (username: string, password: string) => {
    await apiAdminLogin(username, password);
    setIsAdmin(true);
  };

  const logout = async () => {
    try {
      await apiAdminLogout();
    } catch {
      // ignore
    }
    setIsAdmin(false);
  };

  return (
    <AdminAuthContext.Provider value={{ isAdmin, loading, login, logout }}>
      {children}
    </AdminAuthContext.Provider>
  );
};
