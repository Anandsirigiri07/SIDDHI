import React, { useState, useEffect } from 'react';
import { X, User, Award, Hash, Link as LinkIcon, FileText, BrainCircuit, Activity, HelpCircle } from 'lucide-react';
import { api } from '../utils/api';

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
  const [intelData, setIntelData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen && accusedId) {
      setIsLoading(true);
      api.post(`/api/v2/intelligence/dossier/suspect/${accusedId}`)
        .then((res) => {
          setIntelData(res.data.structured_data);
        })
        .catch((err) => {
          console.error("Failed to fetch suspect intelligence dossier:", err);
          setIntelData(null);
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIntelData(null);
    }
  }, [isOpen, accusedId]);

  if (!isOpen || !accusedId) return null;

  const nodeId = `accused-${accusedId}`;
  let accusedNode = graphData ? graphData.nodes.find((n: any) => n.id === nodeId) : null;

  if (!accusedNode && !intelData && isLoading) {
    return (
      <div className="fixed inset-y-0 right-0 w-96 bg-slate-950 border-l border-slate-800/90 shadow-2xl z-[1100] flex flex-col items-center justify-center text-slate-500">
        <Activity className="w-8 h-8 animate-spin text-cyan-500 mb-2" />
        <span className="text-xs uppercase tracking-widest font-semibold">Loading Profile...</span>
      </div>
    );
  }

  if (!accusedNode && intelData) {
    accusedNode = {
      id: nodeId,
      label: intelData.name,
      type: 'Accused',
      occupation: intelData.demographics.occupation,
      age: intelData.demographics.age,
      risk_score: intelData.predictions.repeat_offender_probability * 100,
      pagerank: intelData.network_metrics.pagerank_score,
      betweenness: intelData.network_metrics.betweenness_score,
      community: intelData.network_metrics.community_id
    };
  }

  if (!accusedNode) {
    return (
      <div className="fixed inset-y-0 right-0 w-80 bg-slate-900 border-l border-slate-800 p-4 text-slate-400 z-[1000] flex items-center justify-center">
        <span>Accused details could not be resolved.</span>
      </div>
    );
  }

  // Parse connections from D3 links
  const links = graphData ? (graphData.links || []) : [];
  const connectedFIRs: any[] = [];
  const coAccused: Set<string> = new Set();
  const locations: Set<string> = new Set();

  if (graphData) {
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

    // Find co-accused
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
  } else if (intelData && intelData.linked_cases) {
    intelData.linked_cases.forEach((c: any) => {
      connectedFIRs.push({
        id: `fir-${c.CaseMasterID || 1}`,
        label: c.fir_number,
        type: 'FIR',
        crime_type: c.crime_type
      });
    });
  }

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
        
        {/* Name Card */}
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-lg flex flex-col gap-2">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Target Profile</div>
          <div className="text-lg font-bold text-slate-200">{accusedNode.label}</div>
          <div className="text-xs text-slate-400">
            {intelData?.demographics?.occupation || accusedNode.occupation || 'Occupation N/A'} • Age: {intelData?.demographics?.age || accusedNode.age || 'N/A'}
          </div>
        </div>

        {isLoading ? (
          <div className="py-8 flex flex-col items-center justify-center text-slate-500 gap-2">
            <Activity className="w-6 h-6 animate-pulse text-cyan-500" />
            <span className="text-[10px] uppercase tracking-widest font-semibold">Running ML Recidivism Models...</span>
          </div>
        ) : intelData ? (
          <>
            {/* Predictive Intelligence Panel */}
            <div className="bg-slate-900/20 border border-slate-900 p-4 rounded-lg flex flex-col gap-3">
              <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-1.5 border-b border-slate-800/60 pb-1">
                <BrainCircuit className="w-3.5 h-3.5" />
                Predictive Risk Dossier
              </div>

              {/* Recidivism risk bar */}
              <div className="flex flex-col gap-1.5 mt-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-semibold">Recidivism Probability:</span>
                  <span className={`font-mono font-bold px-2 py-0.5 rounded text-[10px] ${
                    intelData.predictions.risk_band === 'CRITICAL' ? 'bg-red-950/40 text-red-400 border border-red-900/30 animate-pulse' :
                    intelData.predictions.risk_band === 'HIGH' ? 'bg-orange-950/40 text-orange-400 border border-orange-900/30' :
                    'bg-slate-950 text-slate-400'
                  }`}>
                    {(intelData.predictions.repeat_offender_probability * 100).toFixed(1)}% ({intelData.predictions.risk_band})
                  </span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div 
                    className={`h-full rounded-full ${
                      intelData.predictions.risk_band === 'CRITICAL' ? 'bg-red-500' :
                      intelData.predictions.risk_band === 'HIGH' ? 'bg-orange-500' :
                      'bg-cyan-500'
                    }`}
                    style={{ width: `${intelData.predictions.repeat_offender_probability * 100}%` }}
                  />
                </div>
              </div>

              {/* Confidence score indicator */}
              <div className="flex justify-between items-center text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                <span>Intelligence Confidence:</span>
                <span className="font-mono text-emerald-400">{intelData.confidence_score.toFixed(1)}%</span>
              </div>

              {/* Risk Attributions */}
              {intelData.predictions.risk_explanations && intelData.predictions.risk_explanations.length > 0 && (
                <div className="flex flex-col gap-1.5 mt-1">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Attribution Explanations:</span>
                  <div className="grid grid-cols-1 gap-1 text-[11px]">
                    {intelData.predictions.risk_explanations.map((exp: any, idx: number) => (
                      <div key={idx} className="flex justify-between font-mono p-1 bg-slate-950/50 rounded px-2 text-[10px] text-slate-400">
                        <span>{exp.feature.replace('_', ' ')}</span>
                        <span className={exp.contribution >= 0 ? 'text-rose-400' : 'text-emerald-400'}>
                          {exp.contribution >= 0 ? '+' : ''}{exp.contribution.toFixed(3)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Recommendations Panel */}
            <div className="flex flex-col gap-2">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
                Investigative Recommendation Panel
              </div>
              <div className="flex flex-col gap-1.5 mt-1">
                {intelData.recommendations.map((rec: string, idx: number) => (
                  <div key={idx} className="text-xs text-slate-300 bg-cyan-950/10 border border-cyan-900/20 p-2.5 rounded-lg leading-relaxed border-l-2 border-l-cyan-500">
                    {rec}
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : null}

        {/* Network Metrics */}
        <div className="flex flex-col gap-2">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
            <Hash className="w-3.5 h-3.5 text-cyan-500" />
            Network Centrality Metrics
          </div>
          
          <div className="grid grid-cols-2 gap-3 mt-1 text-xs">
            <div className="bg-slate-900/40 border border-slate-900 p-2.5 rounded">
              <div className="text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[9px]">PageRank</div>
              <div className="font-mono text-cyan-400 font-bold text-sm">
                {(intelData?.network_metrics?.pagerank_score || accusedNode.pagerank || 0).toFixed(4)}
              </div>
            </div>
            <div className="bg-slate-900/40 border border-slate-900 p-2.5 rounded">
              <div className="text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[9px]">Betweenness</div>
              <div className="font-mono text-cyan-400 font-bold text-sm">
                {(intelData?.network_metrics?.betweenness_score || accusedNode.betweenness || 0).toFixed(4)}
              </div>
            </div>
            <div className="bg-slate-900/40 border border-slate-900 p-2.5 rounded col-span-2 flex justify-between items-center px-3">
              <div>
                <div className="text-slate-500 font-semibold mb-0.5 uppercase tracking-wider text-[9px]">Louvain Community</div>
                <div className="font-bold text-slate-300">Community Sector #{intelData?.network_metrics?.community_id || accusedNode.community}</div>
              </div>
              <Award className="w-5 h-5 text-amber-500/80" />
            </div>
          </div>
        </div>

        {/* Connected Cases */}
        <div className="flex flex-col gap-2">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
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
                    <span className="text-slate-400 uppercase text-[9px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
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
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-1 flex items-center gap-1.5">
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
                  className="text-[10px] font-medium bg-rose-950/30 text-rose-300 border border-rose-900/30 px-2 py-1 rounded"
                >
                  {name}
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
