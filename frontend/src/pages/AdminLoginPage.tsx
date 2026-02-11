import React, { useState } from 'react';
import { useAdminAuth } from '../context/AdminAuthContext';
import { HiLockClosed, HiShieldCheck } from 'react-icons/hi2';

const AdminLoginPage: React.FC = () => {
  const { login } = useAdminAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-black">
      <div className="w-full max-w-sm mx-auto px-6">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0A84FF] to-[#5E5CE6] flex items-center justify-center mb-4 shadow-2xl shadow-apple-accent/20">
            <HiShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
          <p className="text-apple-secondary text-sm mt-1">Alice Chatbot Management</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-apple-secondary mb-1.5">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-apple-surface border border-apple-border text-white text-sm focus:outline-none focus:border-apple-accent/50 transition-colors"
              placeholder="admin"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-apple-secondary mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-apple-surface border border-apple-border text-white text-sm focus:outline-none focus:border-apple-accent/50 transition-colors"
              placeholder="********"
              required
            />
          </div>

          {error && (
            <div className="px-4 py-2 rounded-xl bg-apple-red/10 border border-apple-red/20 text-apple-red text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-[#0A84FF] to-[#5E5CE6] text-white font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <HiLockClosed className="w-4 h-4" />
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <a href="/" className="text-xs text-apple-tertiary hover:text-apple-secondary transition-colors">
            Back to Chat
          </a>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;
