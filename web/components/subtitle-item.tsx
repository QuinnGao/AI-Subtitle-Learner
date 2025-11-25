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
  onTokenDictionaryClick?: (token: WordToken) => void; // token 字典查询回调
  onPause?: () => void; // 暂停播放回调
}

const WordTokenComponent: React.FC<WordTokenProps> = ({
  token,
  currentTime,
  onTokenClick,
  onTokenDictionaryClick,
  onPause,
}) => {
  const showFurigana = token.furigana && token.furigana !== token.text;

  // 判断当前 token 是否应该高亮
  const isHighlighted =
    token.start_time !== undefined &&
    token.end_time !== undefined &&
    currentTime >= token.start_time &&
    currentTime < token.end_time;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止事件冒泡到 SubtitleItem
    if (onTokenClick && token.start_time !== undefined) {
      onTokenClick(token.start_time / 1000); // 转换为秒
    }
  };

  const handleRightClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // 暂停播放
    if (onPause) {
      onPause();
    }
    // 打开字典
    if (onTokenDictionaryClick) {
      onTokenDictionaryClick(token);
    }
  };

  return (
    <div
      className="group/word flex cursor-pointer flex-col items-center"
      onClick={handleClick}
      onContextMenu={handleRightClick}
      onDoubleClick={() => onTokenDictionaryClick?.(token)}
    >
      {/* 假名 */}
      <span className="mb-0.5 h-4 select-none text-[10px] leading-none text-gray-500 opacity-0 transition-opacity group-hover/word:opacity-100">
        {showFurigana ? token.furigana : ""}
      </span>

      {/* 汉字/原文 */}
      <div
        className={`
        rounded border-2 px-1.5 py-0.5 transition-all duration-200 ${getTokenColorClass(token.type)}
        ${isHighlighted ? "border-blue-400" : "border-transparent"}
      `}
      >
        <span className="text-lg font-bold leading-none">{token.text}</span>
      </div>

      {/* 罗马音 */}
      <span className="mt-1 h-3 font-mono text-[10px] leading-none text-gray-400">
        {token.romaji}
      </span>
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
  onTokenDictionaryClick?: (token: WordToken) => void; // token 字典查询回调
  onPause?: () => void; // 暂停播放回调
  currentTime: number; // 当前播放时间（毫秒）
  innerRef?: React.Ref<HTMLDivElement>;
}

export const SubtitleItem: React.FC<SubtitleItemProps> = ({
  sentence,
  isActive,
  onClick,
  onTokenClick,
  onTokenDictionaryClick,
  onPause,
  currentTime,
  innerRef,
}) => {
  return (
    <div
      ref={innerRef}
      onClick={onClick}
      className={`
        m-5 cursor-pointer rounded-xl border transition-all duration-300
        ${
          isActive
            ? "opacity-100"
            : "border-transparent bg-gray-50/50 opacity-60 hover:border-gray-200 hover:bg-white hover:opacity-100"
        }
      `}
    >
      {/* 单词块布局 */}
      <div className="mx-4 mb-1 flex flex-wrap items-end gap-x-1 gap-y-3">
        {sentence.tokens.map((token, tIdx) => (
          <WordTokenComponent
            key={tIdx}
            token={token}
            currentTime={currentTime}
            onTokenClick={onTokenClick}
            onTokenDictionaryClick={onTokenDictionaryClick}
            onPause={onPause}
          />
        ))}
      </div>

      {/* 翻译 */}
      <div
        className={`
          mx-4 border-t border-dashed pt-1 text-sm transition-colors
          ${isActive ? "border-blue-100 text-gray-700" : "border-gray-200 text-gray-500"}
        `}
      >
        {sentence.translation}
      </div>
    </div>
  );
};

// 导出类型供其他组件使用
export type { SentenceData, WordToken, TokenType };
