import React, { useState } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext';
import { ThemeProvider } from './context/ThemeContext';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminDashboard from './pages/AdminDashboard';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

// Check if current URL is /admin
const isAdminRoute = () => window.location.pathname.startsWith('/admin');

const UserApp: React.FC = () => {
  const { user, loading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);

  if (loading) {
    return <LoadingScreen />;
  }

  // If user is authenticated, show chat
  if (user) {
    return <ChatPage />;
  }

  // If user clicked login, show login page
  if (showLogin) {
    return <LoginPage onBack={() => setShowLogin(false)} />;
  }

  // Otherwise show landing page
  return <LandingPage onLoginClick={() => setShowLogin(true)} />;
};

const AdminApp: React.FC = () => {
  const { isAdmin, loading } = useAdminAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!isAdmin) {
    return <AdminLoginPage />;
  }

  return <AdminDashboard />;
};

const LoadingScreen: React.FC = () => (
  <div className="h-screen w-screen flex items-center justify-center bg-black">
    <div className="flex flex-col items-center gap-4">
      <div className="w-12 h-12 rounded-full border-2 border-apple-accent border-t-transparent animate-spin" />
      <p className="text-apple-secondary text-sm">Loading...</p>
    </div>
  </div>
);

const App: React.FC = () => {
  if (isAdminRoute()) {
    return (
      <ThemeProvider>
        <AdminAuthProvider>
          <AdminApp />
        </AdminAuthProvider>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <AuthProvider>
          <UserApp />
        </AuthProvider>
      </GoogleOAuthProvider>
    </ThemeProvider>
  );
};

export default App;
