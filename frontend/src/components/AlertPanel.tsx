import React from 'react';
import { ShieldAlert, AlertTriangle, Info, BellRing } from 'lucide-react';

export interface AlertItem {
  type: string;
  message: string;
  severity: string;
}

interface AlertPanelProps {
  alerts: AlertItem[];
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="glass-panel w-full p-3 px-4 rounded-lg flex items-center gap-3 text-slate-400 text-sm mb-4">
        <BellRing className="w-4 h-4 text-cyan-500 animate-pulse" />
        <span>No critical intelligence alerts active. System monitoring normal.</span>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-2 mb-4">
      {alerts.map((alert, index) => {
        const severity = alert.severity.toLowerCase();
        let bgStyle = 'bg-rose-950/40 border-rose-800/60 text-rose-300';
        let icon = <ShieldAlert className="w-5 h-5 text-rose-500 flex-shrink-0" />;
        
        if (severity === 'amber' || severity === 'medium') {
          bgStyle = 'bg-amber-950/40 border-amber-800/60 text-amber-300';
          icon = <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />;
        } else if (severity === 'low' || severity === 'green') {
          bgStyle = 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300';
          icon = <Info className="w-5 h-5 text-emerald-500 flex-shrink-0" />;
        }

        return (
          <div
            key={index}
            className={`flex items-center gap-3 p-3 px-4 rounded-lg border glass-panel transition-all duration-300 hover:shadow-md hover:scale-[1.002] ${bgStyle}`}
          >
            {icon}
            <div className="flex-1 text-sm font-medium tracking-wide">
              <span className="font-bold text-xs uppercase tracking-widest bg-black/40 px-2 py-0.5 rounded border border-current mr-2">
                {alert.type}
              </span>
              {alert.message}
            </div>
          </div>
        );
      })}
    </div>
  );
};
export default AlertPanel;
