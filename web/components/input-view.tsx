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
  hasError?: boolean;
  shouldShake?: boolean;
}

export const InputView: React.FC<InputViewProps> = ({
  url,
  onUrlChange,
  onSubmit,
  hasError = false,
  shouldShake = false,
}) => {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-8 duration-500 animate-in fade-in zoom-in">
      <div className="space-y-2 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-800">
          Japanese Learning AI
        </h1>
        <p className="text-gray-500">
          Paste a YouTube URL to generate interactive subtitles.
        </p>
      </div>
      <form
        onSubmit={onSubmit}
        className="relative flex w-full max-w-lg items-center"
      >
        <div className="relative w-full">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search
              className={`h-5 w-5 ${hasError ? "text-red-400" : "text-gray-400"}`}
            />
          </div>
          <input
            type="text"
            className={`
              block w-full rounded-full border bg-white p-4 pl-10 text-sm text-gray-900 shadow-sm outline-none transition-all
              ${
                hasError
                  ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                  : "border-gray-200 focus:border-blue-500 focus:ring-blue-500"
              }
              ${shouldShake ? "animate-shake" : ""}
            `}
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => onUrlChange(e.target.value)}
            required
          />
          <button
            type="submit"
            className={`
              absolute bottom-2 right-2 top-2 rounded-full px-6 text-sm font-medium text-white transition-colors
              ${
                hasError
                  ? "bg-red-500 hover:bg-red-600"
                  : "bg-blue-600 hover:bg-blue-700"
              }
              ${shouldShake ? "animate-shake" : ""}
            `}
          >
            Analyze
          </button>
        </div>
      </form>
    </div>
  );
};
