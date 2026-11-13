import React, { createContext, useContext, useState, useEffect } from 'react';
import { getCurrentUser, loginUser, registerUser, logoutUser } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);   // { student_id } or null
  const [loading, setLoading] = useState(true);

  // On mount, probe the backend to verify session
  useEffect(() => {
    getCurrentUser()
      .then(res => {
        if (res.data && res.data.student_id) {
          setUser({ student_id: res.data.student_id });
          sessionStorage.setItem('cs_student_id', res.data.student_id);
        } else {
          setUser(null);
        }
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (student_id, password) => {
    await loginUser(student_id, password);
    sessionStorage.setItem('cs_student_id', student_id);
    setUser({ student_id });
  };

  const register = async (student_id, password, confirm_password) => {
    await registerUser(student_id, password, confirm_password);
    sessionStorage.setItem('cs_student_id', student_id);
    setUser({ student_id });
  };

  const logout = async () => {
    await logoutUser().catch(() => {});
    sessionStorage.removeItem('cs_student_id');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      loading,
      login,
      register,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

