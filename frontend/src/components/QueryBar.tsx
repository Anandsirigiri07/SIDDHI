import React, { useState, useEffect } from 'react';
import { Send, Mic, MicOff, Search } from 'lucide-react';

interface QueryBarProps {
  onAsk: (query: string) => void;
  isLoading: boolean;
}

export const QueryBar: React.FC<QueryBarProps> = ({ onAsk, isLoading }) => {
  const [query, setQuery] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [speechLang, setSpeechLang] = useState<'en-IN' | 'kn-IN'>('en-IN');
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = speechLang;

      rec.onstart = () => setIsListening(true);
      rec.onend = () => setIsListening(false);
      rec.onerror = () => setIsListening(false);
      rec.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        if (text) {
          setQuery(text);
        }
      };
      setRecognition(rec);
    }
  }, []);

  useEffect(() => {
    if (recognition) {
      recognition.lang = speechLang;
    }
  }, [speechLang, recognition]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onAsk(query.trim());
    }
  };

  const handleMicClick = () => {
    if (!recognition) {
      alert("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full mb-4">
      <div className="relative flex items-center w-full rounded-lg border border-slate-800 bg-slate-900/90 p-1.5 focus-within:border-cyan-500 focus-within:ring-1 focus-within:ring-cyan-500/20 transition-all duration-300 shadow-lg shadow-cyan-950/5">
        <Search className="w-5 h-5 text-slate-500 ml-3 flex-shrink-0" />
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
          placeholder="Ask SIDDHI about crimes, suspects, hotspots, or criminal networks..."
          className="flex-1 bg-transparent px-3 text-slate-100 placeholder-slate-500 border-none outline-none text-sm focus:ring-0 focus:border-none"
        />

        <div className="flex items-center gap-1.5 mr-1.5">
          <button
            type="button"
            onClick={() => setSpeechLang(prev => prev === 'en-IN' ? 'kn-IN' : 'en-IN')}
            disabled={isLoading || isListening}
            className={`px-2 py-1.5 rounded text-[10px] font-bold border transition-all duration-200 cursor-pointer ${
              speechLang === 'kn-IN'
                ? 'bg-purple-500/10 border-purple-500/30 text-purple-400 hover:bg-purple-500/20'
                : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20'
            }`}
            title={`Voice Input: ${speechLang === 'kn-IN' ? 'Kannada' : 'English'}. Click to toggle.`}
          >
            {speechLang === 'kn-IN' ? 'ಕನ್ನಡ (KN)' : 'EN-IN'}
          </button>

          <button
            type="button"
            onClick={handleMicClick}
            disabled={isLoading}
            className={`p-2 rounded-md transition-colors duration-200 cursor-pointer ${
              isListening
                ? 'bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 animate-pulse'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
            title={isListening ? "Listening... click to stop" : "Voice input"}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
          
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className={`p-2 px-4 rounded-md font-semibold text-xs tracking-wider uppercase flex items-center gap-2 transition-all duration-200 cursor-pointer ${
              query.trim() && !isLoading
                ? 'bg-cyan-500 text-slate-950 hover:bg-cyan-400 shadow-md shadow-cyan-500/10'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            <span>Ask</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </form>
  );
};
export default QueryBar;
