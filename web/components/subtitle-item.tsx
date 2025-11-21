"use client";

import React from "react";

// ------------------------------------------------------------------
// 类型定义
// ------------------------------------------------------------------

type TokenType = "noun" | "verb" | "particle" | "other" | "group";

interface WordToken {
  text: string;
  furigana?: string;
  romaji: string;
  type: TokenType;
}

interface SentenceData {
  startTime: number; // 秒
  endTime: number; // 秒
  text: string; // 完整句子
  translation: string;
  tokens: WordToken[]; // NLP拆分后的Token
}

// ------------------------------------------------------------------
// 颜色映射逻辑
// ------------------------------------------------------------------
const getTokenColorClass = (type: TokenType) => {
  switch (type) {
    case "noun":
      return "bg-yellow-100/80 text-yellow-900";
    case "particle":
      return "bg-cyan-100 text-cyan-900";
    case "verb":
      return "bg-green-100 text-green-900";
    default:
      return "text-gray-900";
  }
};

// ------------------------------------------------------------------
// WordToken 组件
// ------------------------------------------------------------------
interface WordTokenProps {
  token: WordToken;
}

const WordTokenComponent: React.FC<WordTokenProps> = ({ token }) => {
  const showFurigana = token.furigana && token.furigana !== token.text;

  return (
    <div className="flex flex-col items-center group/word">
      {/* 假名 */}
      <span className="text-[10px] text-gray-500 h-4 leading-none mb-0.5 opacity-0 group-hover/word:opacity-100 transition-opacity select-none">
        {showFurigana ? token.furigana : ""}
      </span>

      {/* 汉字/原文 */}
      <div className={`px-1.5 py-0.5 rounded ${getTokenColorClass(token.type)}`}>
        <span className="text-lg font-bold leading-none">{token.text}</span>
      </div>

      {/* 罗马音 */}
      <span className="text-[10px] text-gray-400 font-mono mt-1 h-3 leading-none">{token.romaji}</span>
    </div>
  );
};

// ------------------------------------------------------------------
// SubtitleItem 组件
// ------------------------------------------------------------------
interface SubtitleItemProps {
  sentence: SentenceData;
  isActive: boolean;
  onClick: () => void;
  innerRef?: React.Ref<HTMLDivElement>;
}

export const SubtitleItem: React.FC<SubtitleItemProps> = ({ sentence, isActive, onClick, innerRef }) => {
  return (
    <div
      ref={innerRef}
      onClick={onClick}
      className={`
        transition-all duration-300 cursor-pointer rounded-xl border m-5
        ${
          isActive
            ? "bg-blue-50 border-blue-500 shadow-lg ring-2 ring-blue-200 scale-[1.02] opacity-100"
            : "bg-gray-50/50 border-transparent hover:bg-white hover:border-gray-200 hover:shadow-sm opacity-60 hover:opacity-100"
        }
      `}
    >
      {/* 单词块布局 */}
      <div className="flex flex-wrap gap-x-1 gap-y-3 items-end mb-1 mx-4">
        {sentence.tokens.map((token, tIdx) => (
          <WordTokenComponent key={tIdx} token={token} />
        ))}
      </div>

      {/* 翻译 */}
      <div
        className={`
          text-sm pt-1 border-t border-dashed transition-colors
          ${isActive ? "text-gray-700 border-blue-100" : "text-gray-500 border-gray-200"}
        `}
      >
        {sentence.translation}
      </div>
    </div>
  );
};

// 导出类型供其他组件使用
export type { SentenceData, WordToken, TokenType };
