import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface RoleWidgetProps {
  role: string;
  onFIRClick: (firId: number) => void;
  onAsk: (query: string) => void;
}

export const RoleWidget: React.FC<RoleWidgetProps> = ({
  role,
  onFIRClick,
  onAsk
}) => {
  if (role === 'Policymaker') {
    return (
      <div className="mb-4 p-4 rounded-xl border border-blue-900/40 bg-gradient-to-r from-blue-950/40 to-indigo-950/20 backdrop-blur-md flex flex-col gap-3">
        <div className="flex items-center justify-between border-b border-blue-900/30 pb-2">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-indigo-400" />
            <h4 className="text-xs font-bold uppercase tracking-widest text-indigo-300">
              Policymaker Command Dashboard
            </h4>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 uppercase tracking-wider">
            District Aggregates Mode
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Total Offenses</p>
            <p className="text-lg font-black text-slate-200">503</p>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Active Hotspots</p>
            <p className="text-lg font-black text-rose-400">8</p>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Baseline Spike Threshold</p>
            <p className="text-lg font-black text-cyan-400">1.8x</p>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Jurisdictions Monitored</p>
            <p className="text-lg font-black text-slate-200">10 Districts</p>
          </div>
        </div>
      </div>
    );
  }

  if (role === 'Investigator') {
    return (
      <div className="mb-4 p-4 rounded-xl border border-rose-900/40 bg-gradient-to-r from-rose-950/40 to-slate-950/20 backdrop-blur-md flex flex-col gap-3">
        <div className="flex items-center justify-between border-b border-rose-900/30 pb-2">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <h4 className="text-xs font-bold uppercase tracking-widest text-rose-300">
              Investigator Active Case Briefings
            </h4>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 uppercase tracking-wider">
            Active Case Files
          </span>
        </div>
        <div className="flex flex-wrap gap-2.5 items-center">
          <div className="text-[11px] font-semibold text-slate-400">Click to load case:</div>
          <button
            onClick={() => onFIRClick(501)}
            className="px-2.5 py-1 text-xs bg-slate-900 hover:bg-rose-950/30 text-rose-400 hover:text-rose-300 rounded-lg border border-slate-800 hover:border-rose-900/50 transition-all cursor-pointer font-bold animate-fadeIn"
          >
            [FIR-2025-09901] Chain Snatching Indiranagar
          </button>
          <button
            onClick={() => onFIRClick(502)}
            className="px-2.5 py-1 text-xs bg-slate-900 hover:bg-rose-950/30 text-rose-400 hover:text-rose-300 rounded-lg border border-slate-800 hover:border-rose-900/50 transition-all cursor-pointer font-bold animate-fadeIn"
          >
            [FIR-2025-09902] Burglary Whitefield
          </button>
          <button
            onClick={() => onFIRClick(503)}
            className="px-2.5 py-1 text-xs bg-slate-900 hover:bg-rose-950/30 text-rose-400 hover:text-rose-300 rounded-lg border border-slate-800 hover:border-rose-900/50 transition-all cursor-pointer font-bold animate-fadeIn"
          >
            [FIR-2026-09903] Robbery Koramangala
          </button>
        </div>
      </div>
    );
  }

  if (role === 'Analyst') {
    return (
      <div className="mb-4 p-4 rounded-xl border border-cyan-900/40 bg-gradient-to-r from-cyan-950/40 to-slate-950/20 backdrop-blur-md flex flex-col gap-3">
        <div className="flex items-center justify-between border-b border-cyan-900/30 pb-2">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold uppercase tracking-widest text-cyan-300">
              Crime Analyst Centrality Controls
            </h4>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 uppercase tracking-wider">
            Network Modularity Active
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Louvain Communities</p>
            <p className="text-lg font-black text-cyan-400">3 Clusters</p>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Graph suspect count</p>
            <p className="text-lg font-black text-slate-200">76 Accused</p>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Max Suspect Risk Score</p>
            <p className="text-lg font-black text-rose-400">106.5</p>
          </div>
          <div className="bg-slate-950/50 p-2.5 rounded-lg border border-slate-900/60">
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Target Accused Hub</p>
            <p className="text-lg font-black text-cyan-400 hover:underline cursor-pointer" onClick={() => {
              onAsk("Analyze co-accused network for Rajesh");
            }}>Rajesh Kumar</p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};
