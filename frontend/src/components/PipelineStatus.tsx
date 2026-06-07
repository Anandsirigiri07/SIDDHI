import React, { useState, useEffect } from 'react';
import { Check, Loader2 } from 'lucide-react';

interface PipelineStatusProps {
  isLoading: boolean;
  hasResult: boolean;
}

const PIPELINE_STEPS = [
  'Detect Language',
  'Classify Intent',
  'Generate SQL',
  'Execute Query',
  'Build Graph',
  'Detect Hotspots',
  'Assemble Evidence',
  'Generate Response'
];

export const PipelineStatus: React.FC<PipelineStatusProps> = ({ isLoading, hasResult }) => {
  const [currentStep, setCurrentStep] = useState(-1);

  useEffect(() => {
    if (isLoading) {
      setCurrentStep(0);
      const interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev < PIPELINE_STEPS.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 700); // Progress animation timing

      return () => clearInterval(interval);
    } else {
      setCurrentStep(hasResult ? PIPELINE_STEPS.length : -1);
    }
  }, [isLoading, hasResult]);

  return (
    <div className="glass-panel w-full p-4 rounded-lg flex flex-col gap-3 h-full justify-between">
      <h3 className="text-xs font-bold uppercase tracking-widest text-cyan-500 border-b border-slate-800 pb-2">
        Pipeline Execution Status
      </h3>
      
      <div className="flex flex-col gap-2.5 my-2">
        {PIPELINE_STEPS.map((step, idx) => {
          const isCompleted = currentStep > idx;
          const isActive = currentStep === idx;
          
          return (
            <div key={idx} className="flex items-center gap-3 transition-opacity duration-300">
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center border text-[10px] transition-all duration-300 ${
                  isCompleted
                    ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400'
                    : isActive
                    ? 'bg-cyan-500/10 border-cyan-500 text-cyan-400 animate-pulse'
                    : 'bg-slate-950 border-slate-800 text-slate-500'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-3 h-3 stroke-[3]" />
                ) : isActive ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <span>{idx + 1}</span>
                )}
              </div>
              
              <span
                className={`text-xs font-medium tracking-wide transition-colors duration-300 ${
                  isCompleted || isActive ? 'text-slate-200' : 'text-slate-500'
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>

      <div className="text-[10px] text-slate-500 uppercase tracking-widest text-center border-t border-slate-800 pt-2 animate-pulse">
        {isLoading ? 'Processing Query Cycle...' : hasResult ? 'Pipeline Cycle Verified' : 'Idle System'}
      </div>
    </div>
  );
};
export default PipelineStatus;
