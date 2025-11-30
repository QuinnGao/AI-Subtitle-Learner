"use client";

import React, { RefObject, useEffect } from "react";
import { SubtitleItem, WordToken, type SentenceData } from "./subtitle-item";

// ------------------------------------------------------------------
// SubtitleList 组件
// ------------------------------------------------------------------
interface SubtitleListProps {
  subtitleData: SentenceData[];
  activeIndex: number;
  onSeek: (seconds: number) => void; // 跳转到指定时间（秒）
  onTokenDictionaryClick?: (token: WordToken) => void; // token 字典查询回调
  onPause?: () => void; // 暂停播放回调
  currentTime: number; // 当前播放时间（毫秒）
  subtitleListRef: RefObject<HTMLDivElement | null>;
  activeSubtitleRef: RefObject<HTMLDivElement | null>;
}

export const SubtitleList: React.FC<SubtitleListProps> = ({
  subtitleData,
  activeIndex,
  onSeek,
  onTokenDictionaryClick,
  onPause,
  currentTime,
  subtitleListRef,
  activeSubtitleRef,
}) => {
  // 当激活的字幕索引变化时，自动滚动到该字幕
  useEffect(() => {
    if (
      activeSubtitleRef.current &&
      subtitleListRef.current &&
      activeIndex >= 0
    ) {
      const container = subtitleListRef.current;
      const activeElement = activeSubtitleRef.current;

      // 计算元素相对于容器的位置
      const containerRect = container.getBoundingClientRect();
      const elementRect = activeElement.getBoundingClientRect();

      // 如果元素不在可视区域内，滚动到它
      if (
        elementRect.top < containerRect.top ||
        elementRect.bottom > containerRect.bottom
      ) {
        activeElement.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }
  }, [activeIndex, subtitleListRef, activeSubtitleRef]);

  return (
    <div
      ref={subtitleListRef}
      className="min-h-0 flex-1 space-y-6 overflow-y-auto  pr-2"
      style={{ scrollBehavior: "smooth" }}
    >
      {subtitleData.map((sentence, idx) => {
        const isActive = idx === activeIndex;

        return (
          <SubtitleItem
            key={idx}
            sentence={sentence}
            isActive={isActive}
            onClick={() => onSeek(sentence.startTime)}
            onTokenClick={onSeek}
            onTokenDictionaryClick={onTokenDictionaryClick}
            onPause={onPause}
            currentTime={currentTime}
            innerRef={isActive ? activeSubtitleRef : undefined}
          />
        );
      })}
    </div>
  );
};
