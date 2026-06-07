import React from 'react';
import { X, User, ShieldAlert, Award, Hash, Link as LinkIcon, FileText } from 'lucide-react';

interface ProfileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  accusedId: number | null;
  graphData: any;
  onFIRClick: (firId: number) => void;
}

export const ProfileDrawer: React.FC<ProfileDrawerProps> = ({
  isOpen,
  onClose,
  accusedId,
  graphData,
  onFIRClick,
}) => {
  if (!isOpen || !accusedId || !graphData) return null;

  const nodeId = `accused-${accusedId}`;
  const accusedNode = graphData.nodes.find((n: any) => n.id === nodeId);

  if (!accusedNode) {
    return (
      <div className="fixed inset-y-0 right-0 w-80 bg-slate-900 border-l border-slate-800 p-4 text-slate-400 z-[1000] flex items-center justify-center">
        <span>Accused node details not found in active workspace.</span>
      </div>
    );
  }

  // Parse connections from D3 links
  const links = graphData.links || [];
  const connectedFIRs: any[] = [];
  const coAccused: Set<string> = new Set();
  const locations: Set<string> = new Set();

  links.forEach((link: any) => {
    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' ? link.target.id : link.target;

    if (sourceId === nodeId || targetId === nodeId) {
      const peerId = sourceId === nodeId ? targetId : sourceId;
      const peerNode = graphData.nodes.find((n: any) => n.id === peerId);
      
      if (peerNode) {
        if (peerNode.type === 'FIR') {
          connectedFIRs.push(peerNode);
        } else if (peerNode.type === 'Location') {
          locations.add(peerNode.label);
        }
      }
    }
  });

  // Find co-accused (accused sharing the same FIRs)
  connectedFIRs.forEach((fir) => {
    links.forEach((link: any) => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;

      if (sourceId === fir.id || targetId === fir.id) {
        const peerId = sourceId === fir.id ? targetId : sourceId;
        if (peerId !== nodeId && peerId.startsWith('accused-')) {
          const coNode = graphData.nodes.find((n: any) => n.id === peerId);
          if (coNode) {
            coAccused.add(coNode.label);
          }
        }
      }
    });
  });

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-slate-950 border-l border-slate-800/90 shadow-2xl z-[1100] flex flex-col transition-all duration-300">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center gap-2">
          <User className="w-5 h-5 text-rose-500" />
          <span className="text-xs font-bold uppercase tracking-widest text-slate-300">
            Criminal Profile Lens
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 p-5 overflow-y-auto flex flex-col gap-5">
        {/* Name and Risk Card */}
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-lg flex flex-col gap-2">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Target Profile</div>
          <div className="text-lg font-bold text-slate-200">{accusedNode.label}</div>
          <div className="flex items-center gap-2 mt-2">
            <ShieldAlert className="w-4 h-4 text-rose-500" />
            <span className="text-xs font-semibold text-slate-400">Threat Risk Score:</span>
            <span className="text-xs font-bold text-rose-400 bg-rose-950/40 border border-rose-800/30 px-2 py-0.5 rounded">
              {accusedNode.risk_score || 'N/A'}
            </span>
          </div>
        </div>

        {/* Network Metrics */}
        <div className="flex flex-col gap-2">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
            <Hash className="w-3.5 h-3.5 text-cyan-500" />
            Network Centrality Metrics
          </div>
          
          <div className="grid grid-cols-2 gap-3 mt-1 text-xs">
            <div className="bg-slate-900/40 border border-slate-900 p-2.5 rounded">
              <div className="text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[10px]">PageRank</div>
              <div className="font-mono text-cyan-400 font-bold text-sm">
                {(accusedNode.pagerank || 0).toFixed(4)}
              </div>
            </div>
            <div className="bg-slate-900/40 border border-slate-900 p-2.5 rounded">
              <div className="text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[10px]">Betweenness</div>
              <div className="font-mono text-cyan-400 font-bold text-sm">
                {(accusedNode.betweenness || 0).toFixed(4)}
              </div>
            </div>
            <div className="bg-slate-900/40 border border-slate-900 p-2.5 rounded col-span-2 flex justify-between items-center px-3">
              <div>
                <div className="text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[10px]">Louvain Community</div>
                <div className="font-bold text-slate-300">Community Sector #{accusedNode.community}</div>
              </div>
              <Award className="w-5 h-5 text-amber-500/80" />
            </div>
          </div>
        </div>

        {/* Connected Cases */}
        <div className="flex flex-col gap-2">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-cyan-500" />
            Linked Cases (FIRs)
          </div>
          
          {connectedFIRs.length === 0 ? (
            <span className="text-xs text-slate-600 italic">No linked cases in active graph scope.</span>
          ) : (
            <div className="flex flex-col gap-2 mt-1">
              {connectedFIRs.map((fir, idx) => {
                const numericId = parseInt(fir.id.split('-')[1], 10);
                return (
                  <button
                    key={idx}
                    onClick={() => onFIRClick(numericId)}
                    className="w-full flex items-center justify-between p-2.5 bg-slate-900/30 hover:bg-slate-900/60 border border-slate-800/80 rounded transition-all cursor-pointer text-left text-xs"
                  >
                    <span className="font-mono font-bold text-cyan-400">{fir.label}</span>
                    <span className="text-slate-400 uppercase text-[10px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {fir.crime_type?.replace('_', ' ')}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Co-Accused & Gangs */}
        <div className="flex flex-col gap-2">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
            <LinkIcon className="w-3.5 h-3.5 text-cyan-500" />
            Co-Offenders / Associates
          </div>
          
          {coAccused.size === 0 ? (
            <span className="text-xs text-slate-600 italic">No co-offenders linked in graph.</span>
          ) : (
            <div className="flex flex-wrap gap-1.5 mt-1">
              {Array.from(coAccused).map((name, idx) => (
                <span
                  key={idx}
                  className="text-[11px] font-medium bg-rose-950/30 text-rose-300 border border-rose-900/30 px-2 py-1 rounded"
                >
                  {name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Active Locations */}
        <div className="flex flex-col gap-2">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-cyan-500" />
            Primary Action Sectors
          </div>
          
          {locations.size === 0 ? (
            <span className="text-xs text-slate-600 italic">No locations mapped.</span>
          ) : (
            <div className="flex flex-wrap gap-1.5 mt-1">
              {Array.from(locations).map((loc, idx) => (
                <span
                  key={idx}
                  className="text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800 px-2 py-0.5 rounded"
                >
                  {loc}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default ProfileDrawer;
