import React from 'react';

export interface ToastAlert {
  id: string;
  message: string;
  severity: string;
  timestamp: string;
}

interface ToastNotificationContainerProps {
  toastAlerts: ToastAlert[];
}

export const ToastNotificationContainer: React.FC<ToastNotificationContainerProps> = ({
  toastAlerts
}) => {
  return (
    <div className="fixed bottom-5 right-5 flex flex-col gap-2.5 z-[9999] max-w-sm pointer-events-none">
      {toastAlerts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto p-4 rounded-xl border shadow-2xl backdrop-blur-md flex flex-col gap-1.5 transition-all duration-300 ${
            toast.severity === 'CRITICAL'
              ? 'border-rose-900/60 bg-rose-950/80 text-rose-100'
              : 'border-amber-900/60 bg-amber-950/80 text-amber-100'
          }`}
        >
          <div className="flex items-center justify-between gap-4">
            <span className="text-[9px] font-bold font-mono tracking-widest uppercase opacity-75">
              🚨 Real-time alert
            </span>
            <span className="text-[9px] font-mono opacity-50">
              {toast.timestamp}
            </span>
          </div>
          <p className="text-xs font-semibold text-left">{toast.message}</p>
        </div>
      ))}
    </div>
  );
};
