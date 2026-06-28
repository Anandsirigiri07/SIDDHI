import React, { useState, useEffect } from 'react';
import { fetchFIRDetails, api } from '../utils/api';
import { X, FileText, Calendar, ShieldAlert, MapPin, Users, Loader2, BrainCircuit, Hourglass, HelpCircle, UserCheck } from 'lucide-react';

interface FIRDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  firId: number | null;
  onAccusedClick: (accusedId: number) => void;
}

export const FIRDrawer: React.FC<FIRDrawerProps> = ({ isOpen, onClose, firId, onAccusedClick }) => {
  const [firData, setFirData] = useState<any>(null);
  const [intelData, setIntelData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingIntel, setIsLoadingIntel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !firId) {
      setFirData(null);
      setIntelData(null);
      return;
    }

    const loadDetails = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchFIRDetails(firId);
        setFirData(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to retrieve FIR details');
      } finally {
        setIsLoading(false);
      }
    };

    const loadIntel = async () => {
      setIsLoadingIntel(true);
      try {
        const res = await api.post(`/api/v2/intelligence/dossier/case/${firId}`);
        setIntelData(res.data.structured_data);
      } catch (err) {
        console.error("Failed to load case priority intelligence:", err);
        setIntelData(null);
      } finally {
        setIsLoadingIntel(false);
      }
    };

    loadDetails();
    loadIntel();
  }, [isOpen, firId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-[420px] bg-slate-950 border-l border-slate-800/90 shadow-2xl z-[1200] flex flex-col transition-all duration-300">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-cyan-500 animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-widest text-slate-300">
            Case Folder Investigation
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body Content */}
      <div className="flex-1 p-5 overflow-y-auto flex flex-col gap-5">
        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-12">
            <Loader2 className="w-8 h-8 animate-spin text-cyan-500 mb-2" />
            <span className="text-xs uppercase tracking-widest font-semibold">Retrieving Case Details...</span>
          </div>
        ) : error ? (
          <div className="text-rose-400 text-xs uppercase tracking-widest p-4 border border-rose-950/40 bg-rose-950/10 rounded-lg">
            Error: {error}
          </div>
        ) : !firData ? (
          <div className="text-slate-500 text-xs uppercase tracking-widest text-center">No case details loaded.</div>
        ) : (
          <>
            {/* Case Reference & Crime Header */}
            <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-lg flex flex-col gap-2 relative">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">FIR CASE DOSSIER</div>
              <div className="text-xl font-mono font-bold text-cyan-400">{firData.fir_number}</div>
              
              <div className="flex flex-wrap gap-2 mt-2">
                <span className="text-[10px] font-bold uppercase tracking-wider bg-cyan-950/50 text-cyan-400 border border-cyan-800/30 px-2 py-0.5 rounded">
                  {firData.crime_type.replace('_', ' ')}
                </span>
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                  firData.status === 'Open' || firData.status === 'Under Investigation'
                    ? 'bg-amber-950/50 text-amber-400 border-amber-800/30'
                    : 'bg-emerald-950/50 text-emerald-400 border-emerald-800/30'
                }`}>
                  {firData.status}
                </span>
              </div>
            </div>

            {/* Predictive Intelligence Panel */}
            {isLoadingIntel ? (
              <div className="py-6 flex flex-col items-center justify-center text-slate-500 gap-2 border border-slate-900 bg-slate-950/30 rounded-lg">
                <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
                <span className="text-[9px] uppercase tracking-widest font-semibold">Running Priority & Delay Forecasts...</span>
              </div>
            ) : intelData ? (
              <div className="bg-slate-900/20 border border-slate-900 p-4 rounded-lg flex flex-col gap-4">
                <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-1.5 border-b border-slate-800/60 pb-1">
                  <BrainCircuit className="w-3.5 h-3.5 animate-pulse" />
                  Predictive Case priority
                </div>

                {/* Priority Score Gauge */}
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400 font-semibold">Priority Severity Index:</span>
                    <span className={`font-mono font-bold px-2 py-0.5 rounded text-[10px] ${
                      intelData.priority_assessment.risk_category === 'CRITICAL' || intelData.priority_assessment.risk_category === 'HIGH' 
                        ? 'bg-rose-950/40 text-rose-400 border border-rose-900/30 animate-pulse' 
                        : 'bg-slate-950 text-slate-400'
                    }`}>
                      {intelData.priority_assessment.priority_score.toFixed(1)}/100 ({intelData.priority_assessment.risk_category})
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div 
                      className={`h-full rounded-full ${
                        intelData.priority_assessment.risk_category === 'CRITICAL' ? 'bg-red-500' :
                        intelData.priority_assessment.risk_category === 'HIGH' ? 'bg-orange-500' :
                        'bg-cyan-500'
                      }`}
                      style={{ width: `${intelData.priority_assessment.priority_score}%` }}
                    />
                  </div>
                </div>

                {/* Delay Forecast & Confidence Intervals */}
                <div className="grid grid-cols-2 gap-3 mt-1">
                  <div className="bg-slate-950 border border-slate-900 p-2.5 rounded flex flex-col gap-0.5">
                    <span className="text-[9px] uppercase font-bold text-slate-500 tracking-wider flex items-center gap-1">
                      <Hourglass className="w-3 h-3 text-cyan-500" />
                      Delay Forecast
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-200">
                      {intelData.chargesheet_delay_forecast.predicted_days.toFixed(1)} Days
                    </span>
                  </div>

                  <div className="bg-slate-950 border border-slate-900 p-2.5 rounded flex flex-col gap-0.5">
                    <span className="text-[9px] uppercase font-bold text-slate-500 tracking-wider">
                      95% Confidence Bounds
                    </span>
                    <span className="font-mono text-[10px] font-bold text-slate-400">
                      [{intelData.chargesheet_delay_forecast.confidence_interval_95.lower_bound.toFixed(1)} - {intelData.chargesheet_delay_forecast.confidence_interval_95.upper_bound.toFixed(1)}]
                    </span>
                  </div>
                </div>

                {/* Backlog Indicators */}
                <div className="flex justify-between items-center text-[10px] uppercase font-bold bg-slate-950/40 p-2 rounded border border-slate-900/60 px-3">
                  <div className="flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-cyan-500" />
                    <span>Officer Caseload:</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-300">{intelData.officer_backlog_indicators.officer_load} cases</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] border ${
                      intelData.officer_backlog_indicators.officer_backlog_status === 'OVERLOADED' 
                        ? 'bg-rose-950/40 text-rose-400 border-rose-850'
                        : 'bg-emerald-950/40 text-emerald-400 border-emerald-850'
                    }`}>
                      {intelData.officer_backlog_indicators.officer_backlog_status}
                    </span>
                  </div>
                </div>

                {/* Confidence score indicator */}
                <div className="flex justify-between items-center text-[9px] uppercase font-bold text-slate-500 tracking-wider">
                  <span>Forecast Confidence Score:</span>
                  <span className="font-mono text-emerald-400">{(intelData.confidence_score * 100).toFixed(1)}%</span>
                </div>
              </div>
            ) : null}

            {/* Recommendations Panel */}
            {intelData?.recommendations && intelData.recommendations.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-900 pb-1 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-cyan-500" />
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
            )}

            {/* Case Parameters */}
            <div className="flex flex-col gap-3.5 text-xs bg-slate-900/10 border border-slate-900 p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <Calendar className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <div className="flex flex-col">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Incident Date</span>
                  <span className="text-slate-300 font-medium">{firData.date}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <MapPin className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <div className="flex flex-col">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Incident Location</span>
                  <span className="text-slate-300 font-medium">
                    {firData.location ? `${firData.location.name}, ${firData.location.district}` : 'Unknown Location'}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Users className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <div className="flex flex-col">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Investigating Officer</span>
                  <span className="text-slate-300 font-medium">
                    {firData.officer ? `${firData.officer.name} (${firData.officer.rank})` : 'Unassigned'}
                  </span>
                </div>
              </div>
            </div>

            {/* Crime Description */}
            <div className="flex flex-col gap-1.5">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-900 pb-1">
                Incident Description
              </div>
              <p className="text-xs text-slate-300 leading-relaxed text-justify mt-1">
                {firData.description}
              </p>
            </div>

            {/* Accused & Suspects List */}
            <div className="flex flex-col gap-2">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-900 pb-1 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-500" />
                Accused / Suspect Mapping
              </div>
              
              {firData.accused && firData.accused.length === 0 ? (
                <span className="text-xs text-slate-600 italic">No accused persons logged.</span>
              ) : (
                <div className="flex flex-col gap-2 mt-1">
                  {firData.accused?.map((acc: any, idx: number) => (
                    <button
                      key={idx}
                      onClick={() => onAccusedClick(acc.accused_id)}
                      className="w-full flex items-center justify-between p-2.5 bg-slate-900/30 hover:bg-slate-900/60 border border-slate-800/80 rounded transition-all cursor-pointer text-left text-xs"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold text-slate-200">{acc.name}</span>
                        <span className="text-[9px] text-slate-500 uppercase tracking-wider">{acc.occupation} | Age: {acc.age}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] uppercase font-bold text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-900/30">
                          {acc.role}
                        </span>
                        <span className="text-[9px] font-bold text-slate-300 font-mono bg-slate-950 border border-slate-800 px-1.5 py-0.5 rounded">
                          Risk: {acc.risk_score}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Victims List */}
            <div className="flex flex-col gap-2">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-900 pb-1 flex items-center gap-1.5">
                <Users className="w-4 h-4 text-cyan-500" />
                Complainants & Victims
              </div>
              
              {firData.victims && firData.victims.length === 0 ? (
                <span className="text-xs text-slate-600 italic">No victims logged.</span>
              ) : (
                <div className="flex flex-col gap-1.5 mt-1">
                  {firData.victims?.map((vic: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-2 px-3 bg-slate-900/20 border border-slate-900 rounded flex justify-between text-xs"
                    >
                      <span className="font-semibold text-slate-300">{vic.name}</span>
                      <span className="text-slate-500 text-[10px]">{vic.gender} | Age: {vic.age}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
export default FIRDrawer;
