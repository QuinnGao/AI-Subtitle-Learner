"use client";

import React from "react";
import { RotateCcw } from "lucide-react";

// ------------------------------------------------------------------
// AnalysisHeader 组件
// ------------------------------------------------------------------
interface AnalysisHeaderProps {
  onAnalyzeAnother: () => void;
}

export const AnalysisHeader: React.FC<AnalysisHeaderProps> = ({ onAnalyzeAnother }) => {
  return (
    <div className="flex items-center justify-between mb-4 flex-shrink-0">
      <button
        onClick={onAnalyzeAnother}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <RotateCcw size={16} /> Analyze Another
      </button>
      <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">AI Analysis Ready</span>
    </div>
  );
};

