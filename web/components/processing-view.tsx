"use client";

import React from "react";

// ------------------------------------------------------------------
// ProcessingView 组件
// ------------------------------------------------------------------
interface ProcessingViewProps {
  progress: number;
  statusMessage: string;
}

export const ProcessingView: React.FC<ProcessingViewProps> = ({ progress, statusMessage }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
      <div className="relative">
        <div className="w-16 h-16 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-bold text-blue-600">{Math.round(progress)}%</span>
        </div>
      </div>
      <div className="text-center space-y-1">
        <h3 className="text-lg font-semibold text-gray-800">Analyzing Video</h3>
        <p className="text-sm text-gray-500">{statusMessage}</p>
      </div>
      {/* Shadcn style progress bar */}
      <div className="w-64 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full bg-blue-600 transition-all duration-500 ease-out" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
};

