"use client";

import React, { useEffect, useState } from "react";
import { X, Loader2 } from "lucide-react";
import type { WordToken } from "./subtitle-item";
import { queryDictionary, type DictionaryQueryResponse } from "@/lib/api";

interface DictionaryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  word: WordToken | null;
}

export const DictionaryDrawer: React.FC<DictionaryDrawerProps> = ({ isOpen, onClose, word }) => {
  // 检测屏幕宽度
  const [isMobile, setIsMobile] = React.useState(false);
  const [dictionaryData, setDictionaryData] = useState<DictionaryQueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768); // md breakpoint
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // 当单词变化时查询词典
  useEffect(() => {
    if (isOpen && word) {
      setIsLoading(true);
      setError(null);
      setDictionaryData(null);

      queryDictionary({
        word: word.text,
        furigana: word.furigana,
        romaji: word.romaji,
        part_of_speech: word.type,
      })
        .then((data) => {
          setDictionaryData(data);
          setIsLoading(false);
        })
        .catch((err) => {
          setError(err.message || "查询词典失败");
          setIsLoading(false);
        });
    }
  }, [isOpen, word]);

  // 阻止背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen || !word) return null;

  return (
    <>
      {/* 背景遮罩 */}
      <div className="fixed inset-0 bg-black/50 z-40 transition-opacity" onClick={onClose} style={{ opacity: isOpen ? 1 : 0 }} />

      {/* 抽屉/弹出内容 */}
      <div
        className={`
          fixed z-50 bg-white shadow-xl transition-transform duration-300 ease-out
          ${isMobile ? "bottom-0 left-0 right-0 max-h-[80vh] rounded-t-2xl" : "top-0 right-0 h-full w-96"}
          ${isOpen ? (isMobile ? "translate-y-0" : "translate-x-0") : isMobile ? "translate-y-full" : "translate-x-full"}
        `}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">单词详情</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="overflow-y-auto h-[calc(100%-64px)] p-6">
          {word && (
            <div className="space-y-6">
              {/* 单词文本 */}
              <div>
                <div className="text-3xl font-bold text-gray-900 mb-2">{word.text}</div>
                {word.furigana && word.furigana !== word.text && <div className="text-lg text-gray-600 mb-1">{word.furigana}</div>}
                {word.romaji && <div className="text-sm text-gray-500 font-mono">{word.romaji}</div>}
              </div>

              {/* 加载状态 */}
              {isLoading && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                  <span className="ml-2 text-gray-600">查询中...</span>
                </div>
              )}

              {/* 错误状态 */}
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              {/* 词典内容 */}
              {dictionaryData && !isLoading && (
                <>
                  {/* 发音信息 */}
                  {(dictionaryData.pronunciation.furigana || dictionaryData.pronunciation.romaji) && (
                    <div>
                      <div className="text-sm font-medium text-gray-500 mb-1">发音</div>
                      <div className="text-base text-gray-900">
                        {dictionaryData.pronunciation.furigana && <div className="mb-1">{dictionaryData.pronunciation.furigana}</div>}
                        {dictionaryData.pronunciation.romaji && (
                          <div className="text-sm text-gray-600 font-mono">{dictionaryData.pronunciation.romaji}</div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 词性 */}
                  {dictionaryData.part_of_speech && (
                    <div>
                      <div className="text-sm font-medium text-gray-500 mb-1">词性</div>
                      <div className="text-base text-gray-900">{dictionaryData.part_of_speech}</div>
                    </div>
                  )}

                  {/* 释义 */}
                  {dictionaryData.meanings && dictionaryData.meanings.length > 0 && (
                    <div>
                      <div className="text-sm font-medium text-gray-500 mb-2">释义</div>
                      <div className="space-y-4">
                        {dictionaryData.meanings.map((meaning, idx) => (
                          <div key={idx} className="border-l-2 border-blue-200 pl-4">
                            <div className="text-base text-gray-900 font-medium mb-1">{meaning.meaning}</div>
                            {meaning.example && (
                              <div className="text-sm text-gray-700 mt-2">
                                <div className="font-medium mb-1">例句：</div>
                                <div className="text-gray-900">{meaning.example}</div>
                                {meaning.example_translation && <div className="text-gray-600 mt-1">{meaning.example_translation}</div>}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 使用说明 */}
                  {dictionaryData.usage_notes && (
                    <div>
                      <div className="text-sm font-medium text-gray-500 mb-1">使用说明</div>
                      <div className="text-base text-gray-700">{dictionaryData.usage_notes}</div>
                    </div>
                  )}

                  {/* 无释义提示 */}
                  {(!dictionaryData.meanings || dictionaryData.meanings.length === 0) && !error && (
                    <div className="text-center py-8 text-gray-400">
                      <p>未找到该单词的词典信息</p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
};
