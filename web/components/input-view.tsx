"use client";

import React from "react";
import { Search } from "lucide-react";

// ------------------------------------------------------------------
// InputView 组件
// ------------------------------------------------------------------
interface InputViewProps {
  url: string;
  onUrlChange: (url: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export const InputView: React.FC<InputViewProps> = ({ url, onUrlChange, onSubmit }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8 animate-in fade-in zoom-in duration-500">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold text-gray-800 tracking-tight">Japanese Learning AI</h1>
        <p className="text-gray-500">Paste a YouTube URL to generate interactive subtitles.</p>
      </div>

      <form onSubmit={onSubmit} className="w-full max-w-lg relative flex items-center">
        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <Search className="w-5 h-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full p-4 pl-10 text-sm text-gray-900 border border-gray-200 rounded-full bg-white shadow-sm focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => onUrlChange(e.target.value)}
            required
          />
          <button
            type="submit"
            className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-full px-6 text-sm transition-colors"
          >
            Analyze
          </button>
        </div>
      </form>
    </div>
  );
};

