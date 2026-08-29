import React, { useState, useEffect } from 'react';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { isAuthenticated } from './utils/auth';

export const App: React.FC = () => {
  const [authed, setAuthed] = useState<boolean>(isAuthenticated());

  useEffect(() => {
    const handleAuthChange = () => {
      setAuthed(isAuthenticated());
    };
    
    window.addEventListener('storage', handleAuthChange);
    window.addEventListener('auth_state_change', handleAuthChange);
    return () => {
      window.removeEventListener('storage', handleAuthChange);
      window.removeEventListener('auth_state_change', handleAuthChange);
    };
  }, []);

  if (!authed) {
    return <LoginPage />;
  }

  return <DashboardPage />;
};

export default App;
