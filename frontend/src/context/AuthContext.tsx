// frontend/src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getCurrentUser, User, checkAuthStorage, logout as serviceLogout } from '../services/authService';

interface AuthContextType {
  isAuthenticated: boolean;
  currentUser: User | null;
  login: (userData: User) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true); // 처음엔 로딩 상태

  useEffect(() => {
    const authStatus = checkAuthStorage();
    setIsAuthenticated(authStatus);
    if (authStatus) {
      const user = getCurrentUser();
      setCurrentUser(user);
    }
    setLoading(false); // 로딩 완료
  }, []);

  const login = (userData: User) => {
    setIsAuthenticated(true);
    setCurrentUser(userData);
  };

  const logout = () => {
    serviceLogout();
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  if (loading) {
    return <div>Loading authentication status...</div>;
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, currentUser, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};