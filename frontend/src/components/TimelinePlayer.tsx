import React from 'react';
import { Play, Pause } from 'lucide-react';

interface TimelinePlayerProps {
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  playbackDate: string;
  setPlaybackDate: (date: string) => void;
  playbackSpeed: number;
  setPlaybackSpeed: (speed: number) => void;
  allDates: string[];
  accumulatedCount: number;
}

export const TimelinePlayer: React.FC<TimelinePlayerProps> = ({
  isPlaying,
  setIsPlaying,
  playbackDate,
  setPlaybackDate,
  playbackSpeed,
  setPlaybackSpeed,
  allDates,
  accumulatedCount
}) => {
  if (allDates.length <= 1) return null;

  return (
    <div className="mt-4 p-4 rounded-xl border border-slate-800 bg-slate-950/60 backdrop-blur flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-2 bg-cyan-600 hover:bg-cyan-500 text-slate-950 rounded-lg cursor-pointer transition-colors shadow-md"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <div className="text-left">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Spatio-Temporal Playback slider
            </span>
            <div className="text-[10px] text-slate-500 font-semibold font-mono">
              Current Date: {playbackDate} | Accumulated Crime Count: {accumulatedCount}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Speed:</span>
          <select
            value={playbackSpeed}
            onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
            className="bg-slate-900 border border-slate-800 text-[10px] text-slate-300 rounded px-1.5 py-0.5"
          >
            <option value={2000}>Slow (2s)</option>
            <option value={1000}>Normal (1s)</option>
            <option value={500}>Fast (0.5s)</option>
          </select>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <span className="text-[10px] text-slate-500 font-bold font-mono">{allDates[0]}</span>
        <input
          type="range"
          min={0}
          max={allDates.length - 1}
          value={allDates.indexOf(playbackDate)}
          onChange={(e) => setPlaybackDate(allDates[Number(e.target.value)])}
          className="flex-1 accent-cyan-400 bg-slate-900 cursor-pointer rounded-lg h-1.5"
        />
        <span className="text-[10px] text-slate-500 font-bold font-mono">{allDates[allDates.length - 1]}</span>
      </div>
    </div>
  );
};
