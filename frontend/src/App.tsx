import React, { useState, useEffect } from 'react';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { isAuthenticated } from './utils/auth';

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };
    
    // Add popstate listener for browser back/forward buttons
    window.addEventListener('popstate', handleLocationChange);
    return () => {
      window.removeEventListener('popstate', handleLocationChange);
    };
  }, []);

  // Security Gate / Route Protection
  if (currentPath === '/login') {
    return <LoginPage />;
  }

  if (!isAuthenticated()) {
    // Force redirect to login page
    window.history.pushState({}, '', '/login');
    return <LoginPage />;
  }

  // Default route - Dashboard Workspace
  return <DashboardPage />;
};

export default App;
