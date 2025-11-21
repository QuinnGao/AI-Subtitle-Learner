"use client";

import React, { RefObject, useEffect } from "react";
import { SubtitleItem, type SentenceData } from "./subtitle-item";

// ------------------------------------------------------------------
// SubtitleList 组件
// ------------------------------------------------------------------
interface SubtitleListProps {
  subtitleData: SentenceData[];
  activeIndex: number;
  onSeek: (seconds: number) => void;
  subtitleListRef: RefObject<HTMLDivElement>;
  activeSubtitleRef: RefObject<HTMLDivElement>;
}

export const SubtitleList: React.FC<SubtitleListProps> = ({ subtitleData, activeIndex, onSeek, subtitleListRef, activeSubtitleRef }) => {
  // 当激活的字幕索引变化时，自动滚动到该字幕
  useEffect(() => {
    if (activeSubtitleRef.current && subtitleListRef.current && activeIndex >= 0) {
      const container = subtitleListRef.current;
      const activeElement = activeSubtitleRef.current;

      // 计算元素相对于容器的位置
      const containerRect = container.getBoundingClientRect();
      const elementRect = activeElement.getBoundingClientRect();

      // 如果元素不在可视区域内，滚动到它
      if (elementRect.top < containerRect.top || elementRect.bottom > containerRect.bottom) {
        activeElement.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }
  }, [activeIndex, subtitleListRef, activeSubtitleRef]);

  return (
    <div ref={subtitleListRef} className="flex-1 overflow-y-auto pr-2 space-y-6  min-h-0" style={{ scrollBehavior: "smooth" }}>
      {subtitleData.map((sentence, idx) => {
        const isActive = idx === activeIndex;

        return (
          <SubtitleItem
            key={idx}
            sentence={sentence}
            isActive={isActive}
            onClick={() => onSeek(sentence.startTime)}
            innerRef={isActive ? activeSubtitleRef : undefined}
          />
        );
      })}
    </div>
  );
};
