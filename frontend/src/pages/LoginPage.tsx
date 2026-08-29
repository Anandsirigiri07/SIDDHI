import React, { useState } from 'react';
import { api } from '../utils/api';
import { setSession } from '../utils/auth';
import { ShieldAlert, KeyRound, User, Loader2, ChevronDown } from 'lucide-react';

const DEMO_ROLES = [
  { label: '👮 Investigator — Field Case Officer', username: 'investigator', password: 'password123', color: 'text-blue-400' },
  { label: '📊 Analyst — Crime Pattern Analyst', username: 'analyst', password: 'password123', color: 'text-emerald-400' },
  { label: '🏛️ Supervisor — District Supervisor', username: 'supervisor', password: 'password123', color: 'text-amber-400' },
  { label: '🏢 Policymaker — DGP Command', username: 'policymaker', password: 'password123', color: 'text-rose-400' },
];

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('investigator');
  const [password, setPassword] = useState('password123');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/auth/login', { username, password });
      const { access_token, user } = response.data;
      setSession(access_token, user);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#03060f] flex items-center justify-center p-4 relative overflow-hidden font-sans">
      {/* Decorative Cybernetic Grid lines */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#090e1a_1px,transparent_1px),linear-gradient(to_bottom,#090e1a_1px,transparent_1px)] bg-[size:40px_40px] opacity-30 pointer-events-none" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-rose-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Glass login panel card */}
      <div className="w-full max-w-md glass-panel-glow rounded-xl p-8 z-10 shadow-2xl relative">
        {/* Shield Logo */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-14 h-14 bg-cyan-500/10 border border-cyan-500/40 rounded-xl flex items-center justify-center mb-4 filter drop-shadow-[0_0_8px_rgba(6,182,212,0.2)]">
            <ShieldAlert className="w-7 h-7 text-cyan-400" />
          </div>
          <h1 className="text-xl font-bold tracking-widest text-slate-100 uppercase font-mono">
            SIDDHI TERMINAL
          </h1>
          <p className="text-[10px] text-cyan-500 font-bold uppercase tracking-widest mt-1">
            Situational Intelligence Dashboard
          </p>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-lg bg-rose-950/40 border border-rose-800/40 text-rose-300 text-xs text-center font-medium tracking-wide">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">
              Operator Username
            </label>
            <div className="relative flex items-center w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 focus-within:border-cyan-500 transition-colors duration-200">
              <User className="w-4 h-4 text-slate-500 ml-1.5 flex-shrink-0" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
                placeholder="Enter username..."
                className="flex-1 bg-transparent px-3 text-sm text-slate-100 placeholder-slate-600 border-none outline-none focus:ring-0"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">
              Access Code
            </label>
            <div className="relative flex items-center w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 focus-within:border-cyan-500 transition-colors duration-200">
              <KeyRound className="w-4 h-4 text-slate-500 ml-1.5 flex-shrink-0" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                placeholder="Enter password..."
                className="flex-1 bg-transparent px-3 text-sm text-slate-100 placeholder-slate-600 border-none outline-none focus:ring-0"
              />
            </div>
          </div>

          {/* Demo Access Dropdown for Judges */}
          <div className="mt-2 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest">🔍 Demo Access — For Evaluators</span>
            </div>
            <div className="relative">
              <select
                value={username}
                onChange={(e) => {
                  const role = DEMO_ROLES.find(r => r.username === e.target.value);
                  if (role) {
                    setUsername(role.username);
                    setPassword(role.password);
                  } else {
                    setUsername(e.target.value);
                  }
                }}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 pr-8 appearance-none cursor-pointer focus:outline-none focus:border-amber-500/60 transition-colors"
              >
                <option value="" disabled>— Select a role to auto-fill credentials —</option>
                {DEMO_ROLES.map((role) => (
                  <option key={role.username} value={role.username}>
                    {role.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
            </div>
            <p className="mt-2 text-[9px] text-slate-500 text-center tracking-wide">
              ⚠ These credentials are for demonstration purposes only. All data is synthetic.
            </p>
          </div>

          <button
            type="submit"
            disabled={isLoading || !username || !password}
            className={`mt-4 w-full py-3 rounded-lg font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-2 transition-all duration-200 cursor-pointer ${
              isLoading || !username || !password
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-900'
                : 'bg-cyan-500 text-slate-950 hover:bg-cyan-400 shadow-md shadow-cyan-500/15'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authorizing Link...</span>
              </>
            ) : (
              <span>Initiate Link</span>
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-[10px] text-slate-600 uppercase tracking-wider font-mono">
          Secured RBAC Terminal // Karnataka State Police
        </div>
      </div>
    </div>
  );
};
export default LoginPage;
