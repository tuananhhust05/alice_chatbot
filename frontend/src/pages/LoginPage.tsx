import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import { HiSparkles } from 'react-icons/hi2';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSuccess = async (credentialResponse: any) => {
    if (!credentialResponse.credential) {
      setError('Login failed. Please try again.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await login(credentialResponse.credential);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen h-[100dvh] w-screen flex items-center justify-center bg-black relative overflow-hidden safe-area-inset">
      {/* Background gradient orbs */}
      <div className="absolute top-1/4 -left-32 w-64 sm:w-96 h-64 sm:h-96 bg-blue-600/20 rounded-full blur-[80px] sm:blur-[120px]" />
      <div className="absolute bottom-1/4 -right-32 w-64 sm:w-96 h-64 sm:h-96 bg-purple-600/20 rounded-full blur-[80px] sm:blur-[120px]" />

      <div className="relative z-10 flex flex-col items-center gap-6 sm:gap-8 px-4 sm:px-6 w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3 sm:gap-4 animate-fade-in">
          <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-[18px] sm:rounded-[22px] bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6] flex items-center justify-center shadow-2xl shadow-blue-500/25">
            <HiSparkles className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
          </div>
          <div className="text-center">
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
              Alice
            </h1>
            <p className="text-apple-secondary text-sm sm:text-base mt-1.5 sm:mt-2">
              Your intelligent AI assistant
            </p>
          </div>
        </div>

        {/* Login card */}
        <div className="glass-effect glass-border rounded-2xl p-6 sm:p-8 w-full animate-slide-up">
          <div className="flex flex-col items-center gap-5 sm:gap-6">
            <div className="text-center">
              <h2 className="text-base sm:text-lg font-semibold text-white">Welcome</h2>
              <p className="text-apple-secondary text-xs sm:text-sm mt-1">
                Sign in with your Google account to continue
              </p>
            </div>

            {loading ? (
              <div className="flex items-center gap-3 py-3">
                <div className="w-5 h-5 rounded-full border-2 border-apple-accent border-t-transparent animate-spin" />
                <span className="text-apple-secondary text-sm">Signing in...</span>
              </div>
            ) : (
              <div className="flex justify-center w-full">
                <GoogleLogin
                  onSuccess={handleSuccess}
                  onError={() => setError('Login failed. Please try again.')}
                  theme="filled_black"
                  shape="pill"
                  size="large"
                  width="280"
                  text="signin_with"
                />
              </div>
            )}

            {error && (
              <p className="text-apple-red text-xs sm:text-sm text-center animate-fade-in">
                {error}
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <p className="text-apple-tertiary text-[10px] sm:text-xs animate-fade-in">
          Powered by Groq &middot; Llama 3.3 70B
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
