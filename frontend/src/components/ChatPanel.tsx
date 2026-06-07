import React, { useRef, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, BrainCircuit, Volume2, VolumeX } from 'lucide-react';

export interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  intent?: string;
  confidence?: number;
  citations?: string[];
  executionMode?: string;
}

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onFIRClick: (firNumber: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, isLoading, onFIRClick }) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleSpeak = (text: string, index: number) => {
    if (!window.speechSynthesis) return;

    if (speakingIndex === index) {
      window.speechSynthesis.cancel();
      setSpeakingIndex(null);
      return;
    }

    window.speechSynthesis.cancel();

    // Clean text: strip markdown characters and citations like [FIR-2025-00129]
    const cleanText = text
      .replace(/\[FIR-\d{4}-\w+\]/g, '') // remove citations
      .replace(/[*#_`\-]/g, '') // remove markdown structures
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);

    // Detect language
    const isKannada = /[\u0c80-\u0cff]/.test(cleanText);
    utterance.lang = isKannada ? 'kn-IN' : 'en-IN';

    // Find and assign proper voice
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((v) =>
      v.lang.toLowerCase().startsWith(isKannada ? 'kn' : 'en')
    );
    if (voice) {
      utterance.voice = voice;
    }

    utterance.onend = () => {
      setSpeakingIndex(null);
    };
    utterance.onerror = () => {
      setSpeakingIndex(null);
    };

    setSpeakingIndex(index);
    window.speechSynthesis.speak(utterance);
  };

  const processMarkdown = (text: string) => {
    // Map [FIR-2025-09901] to [FIR-2025-09901](fir://2025-09901)
    return text.replace(/\[(FIR-(\d{4})-([A-Za-z0-9]+))\]/g, '[$1](fir://$2-$3)');
  };

  const markdownComponents = {
    a: ({ href, children }: any) => {
      if (href && href.startsWith('fir://')) {
        const firNum = 'FIR-' + href.substring(6);
        return (
          <button
            type="button"
            onClick={() => onFIRClick(firNum)}
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/35 transition-colors cursor-pointer align-middle"
          >
            {firNum}
          </button>
        );
      }
      return <a href={href} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">{children}</a>;
    },
    p: ({ children }: any) => <p className="mb-2 last:mb-0 leading-relaxed text-sm text-slate-200">{children}</p>,
    h1: ({ children }: any) => <h1 className="text-lg font-bold text-cyan-400 mt-4 mb-2">{children}</h1>,
    h2: ({ children }: any) => <h2 className="text-md font-bold text-cyan-500 mt-3 mb-1.5">{children}</h2>,
    ul: ({ children }: any) => <ul className="list-disc pl-5 mb-2 text-sm text-slate-300">{children}</ul>,
    li: ({ children }: any) => <li className="mb-1">{children}</li>,
  };

  return (
    <div className="glass-panel w-full rounded-lg flex flex-col h-[520px] shadow-2xl">
      <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-cyan-500 animate-pulse" />
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-300">
            Conversational Analysis Lens
          </h3>
        </div>
        <span className="text-[10px] text-cyan-500/80 font-mono uppercase bg-cyan-950/40 border border-cyan-800/40 px-2 py-0.5 rounded">
          Live Connection
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <Bot className="w-12 h-12 text-slate-700 mb-3" />
            <p className="text-xs max-w-xs leading-relaxed uppercase tracking-wider">
              Awaiting query execution. Submit an inquiry through the command bar to load situational intelligence.
            </p>
          </div>
        )}

        {messages.map((msg, index) => {
          const isUser = msg.sender === 'user';
          
          return (
            <div
              key={index}
              className={`flex gap-3 max-w-[90%] ${isUser ? 'self-end flex-row-reverse' : 'self-start'}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border flex-shrink-0 ${
                isUser
                  ? 'bg-cyan-500/10 border-cyan-500 text-cyan-400'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}>
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className="flex flex-col gap-1.5">
                <div className={`p-3 rounded-lg border text-sm ${
                  isUser
                    ? 'bg-cyan-950/20 border-cyan-900/40 text-cyan-100 rounded-tr-none'
                    : 'bg-slate-900/60 border-slate-800/80 text-slate-200 rounded-tl-none'
                }`}>
                  {isUser ? (
                    <p className="leading-relaxed text-sm">{msg.text}</p>
                  ) : (
                    <ReactMarkdown components={markdownComponents}>
                      {processMarkdown(msg.text)}
                    </ReactMarkdown>
                  )}
                </div>

                {/* AI Meta Metadata Bar */}
                {!isUser && msg.intent && (
                  <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-500 bg-slate-950/40 p-1.5 px-2.5 rounded border border-slate-900 w-fit">
                    <span className="font-semibold text-cyan-500">INTENT:</span>
                    <span>{msg.intent}</span>
                    <span className="text-slate-800">|</span>
                    <span className="font-semibold text-cyan-500">CONFIDENCE:</span>
                    <span>{((msg.confidence || 0) * 100).toFixed(0)}%</span>
                    {msg.executionMode && (
                      <>
                        <span className="text-slate-800">|</span>
                        <span className="font-semibold text-cyan-500">MODE:</span>
                        <span className="uppercase">{msg.executionMode}</span>
                      </>
                    )}
                    <span className="text-slate-800">|</span>
                    <button
                      type="button"
                      onClick={() => handleSpeak(msg.text, index)}
                      className={`flex items-center gap-1 font-semibold transition-colors duration-200 cursor-pointer ${
                        speakingIndex === index
                          ? 'text-rose-400 hover:text-rose-300'
                          : 'text-cyan-500 hover:text-cyan-400'
                      }`}
                    >
                      {speakingIndex === index ? (
                        <>
                          <VolumeX className="w-3 h-3 text-rose-400" />
                          <span className="uppercase text-[9px]">Stop Reading</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3 h-3 text-cyan-500" />
                          <span className="uppercase text-[9px]">Read Aloud</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 self-start max-w-[80%]">
            <div className="w-8 h-8 rounded-full flex items-center justify-center border bg-slate-900 border-slate-800 text-slate-400">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-900/60 border border-slate-800/80 p-3 rounded-lg rounded-tl-none flex items-center gap-1.5 h-10">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
export default ChatPanel;
