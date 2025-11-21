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
  start_time?: number; // 毫秒
  end_time?: number; // 毫秒
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
  currentTime: number; // 当前播放时间（毫秒）
  onTokenClick?: (startTime: number) => void; // token 点击回调，参数为开始时间（秒）
}

const WordTokenComponent: React.FC<WordTokenProps> = ({ token, currentTime, onTokenClick }) => {
  const showFurigana = token.furigana && token.furigana !== token.text;

  // 判断当前 token 是否应该高亮
  const isHighlighted =
    token.start_time !== undefined && token.end_time !== undefined && currentTime >= token.start_time && currentTime < token.end_time;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止事件冒泡到 SubtitleItem
    if (onTokenClick && token.start_time !== undefined) {
      onTokenClick(token.start_time / 1000); // 转换为秒
    }
  };

  return (
    <div className="flex flex-col items-center group/word cursor-pointer" onClick={handleClick}>
      {/* 假名 */}
      <span className="text-[10px] text-gray-500 h-4 leading-none mb-0.5 opacity-0 group-hover/word:opacity-100 transition-opacity select-none">
        {showFurigana ? token.furigana : ""}
      </span>

      {/* 汉字/原文 */}
      <div
        className={`
        px-1.5 py-0.5 rounded transition-all duration-200 ${getTokenColorClass(token.type)}
        ${isHighlighted && "border-blue-400 border-2"}
      `}
      >
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
  onTokenClick?: (startTime: number) => void; // token 点击回调，参数为开始时间（秒）
  currentTime: number; // 当前播放时间（毫秒）
  innerRef?: React.Ref<HTMLDivElement>;
}

export const SubtitleItem: React.FC<SubtitleItemProps> = ({ sentence, isActive, onClick, onTokenClick, currentTime, innerRef }) => {
  return (
    <div
      ref={innerRef}
      onClick={onClick}
      className={`
        transition-all duration-300 cursor-pointer rounded-xl border m-5
        ${
          isActive
            ? "scale-[1.02] opacity-100"
            : "bg-gray-50/50 border-transparent hover:bg-white hover:border-gray-200 opacity-60 hover:opacity-100"
        }
      `}
    >
      {/* 单词块布局 */}
      <div className="flex flex-wrap gap-x-1 gap-y-3 items-end mb-1 mx-4">
        {sentence.tokens.map((token, tIdx) => (
          <WordTokenComponent key={tIdx} token={token} currentTime={currentTime} onTokenClick={onTokenClick} />
        ))}
      </div>

      {/* 翻译 */}
      <div
        className={`
          text-sm pt-1 mx-4 border-t border-dashed transition-colors
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
