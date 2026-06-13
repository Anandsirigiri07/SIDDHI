import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Brain, X, Loader2 } from 'lucide-react';

interface DossierModalProps {
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
  content: string;
  onFirClick: (firNumber: string) => void;
}

export const DossierModal: React.FC<DossierModalProps> = ({
  isOpen,
  onClose,
  isLoading,
  content,
  onFirClick
}) => {
  if (!isOpen) return null;

  const processMarkdown = (text: string): string => {
    return text.replace(/\[(FIR-(\d{4})-([A-Za-z0-9]+))\]/g, '[$1](fir://$2-$3)');
  };

  const markdownComponents = {
    a: ({ href, children }: any) => {
      if (href && href.startsWith('fir://')) {
        const firNum = 'FIR-' + href.substring(6);
        return (
          <button
            type="button"
            onClick={() => onFirClick(firNum)}
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/35 transition-colors cursor-pointer align-middle"
          >
            {firNum}
          </button>
        );
      }
      return (
        <a href={href} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">
          {children}
        </a>
      );
    },
    p: ({ children }: any) => (
      <p className="mb-2 last:mb-0 leading-relaxed text-xs text-slate-200">
        {children}
      </p>
    ),
    h1: ({ children }: any) => (
      <h1 className="text-sm font-bold text-cyan-400 mt-4 mb-2">
        {children}
      </h1>
    ),
    h2: ({ children }: any) => (
      <h2 className="text-xs font-bold text-cyan-500 mt-3 mb-1.5">
        {children}
      </h2>
    ),
    ul: ({ children }: any) => (
      <ul className="list-disc pl-5 mb-2 text-xs text-slate-300">
        {children}
      </ul>
    ),
    li: ({ children }: any) => <li className="mb-1">{children}</li>,
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-[99999] p-4 animate-fadeIn">
      <div className="bg-[#050914] border border-purple-900/40 rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-purple-900/30 flex items-center justify-between bg-purple-950/15">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            <h3 className="font-bold text-sm uppercase tracking-widest text-purple-300 text-left">
              AI Prosecutorial Dossier Narrative
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-500 hover:text-slate-200 hover:bg-slate-900 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto max-h-[60vh] text-slate-300">
          {isLoading ? (
            <div className="h-48 flex flex-col items-center justify-center text-slate-500 gap-2">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
              <span className="text-xs uppercase tracking-widest">Constructing Evidence Dossier Narrative...</span>
            </div>
          ) : (
            <div className="prose prose-invert max-w-none text-xs leading-relaxed flex flex-col gap-4 text-left">
              <ReactMarkdown components={markdownComponents}>
                {processMarkdown(content)}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 bg-slate-950/80 border-t border-purple-900/30 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-xs font-semibold rounded-lg cursor-pointer"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
};
