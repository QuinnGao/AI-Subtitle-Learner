"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { AlertCircle, Play, Pause } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  startVideoAnalysis,
  getSubtitleContent,
  type AnalyzeResponse,
  type SubtitleContentItem,
} from "@/lib/api";
import { isValidYouTubeUrl } from "@/lib/utils";
import { useTaskStatusStream } from "@/hooks/useTaskStatusStream";
import { toast } from "sonner";
import ReactPlayer from "react-player";
import { SubtitleList } from "@/components/subtitle-list";
import { AnalysisHeader } from "@/components/analysis-header";
import { InputView } from "@/components/input-view";
import { ProcessingView } from "@/components/processing-view";
import { DictionaryDrawer } from "@/components/dictionary-drawer";
import type {
  SentenceData,
  TokenType,
  WordToken,
} from "@/components/subtitle-item";

// ------------------------------------------------------------------
// 类型定义：UI展示用的富文本结构
// ------------------------------------------------------------------
// 类型定义已移至 @/components/subtitle-item

type AppState = "idle" | "processing" | "completed" | "error";

// ------------------------------------------------------------------
// 将后端返回的 JSON 数据转换为前端需要的格式
// ------------------------------------------------------------------
const convertSubtitleData = (
  backendData: SubtitleContentItem[]
): SentenceData[] => {
  return backendData.map((item) => {
    // 转换 tokens，如果没有 tokens 则从 original_text 创建简单的 tokens
    let tokens: WordToken[] = [];

    if (item.tokens && item.tokens.length > 0) {
      // 使用后端返回的 tokens
      tokens = item.tokens.map((token) => ({
        text: token.text,
        furigana: token.furigana || "",
        romaji: token.romaji || "",
        type: (token.type as TokenType) || "other",
        start_time: token.start_time,
        end_time: token.end_time,
      }));
    } else {
      // 如果没有 tokens，将 original_text 按字符分割作为简单的 tokens
      tokens = item.original_text.split("").map((char) => ({
        text: char,
        furigana: "",
        romaji: "",
        type: "other" as TokenType,
      }));
    }

    return {
      startTime: item.start_time / 1000, // 转换为秒
      endTime: item.end_time / 1000, // 转换为秒
      text: item.original_text,
      translation: item.translation || "",
      tokens: tokens,
    };
  });
};

// 颜色映射逻辑已移至 @/components/subtitle-item

// ------------------------------------------------------------------
// 主组件
// ------------------------------------------------------------------

export default function VideoLearningPage() {
  // State
  const [url, setUrl] = useState("");
  const [appState, setAppState] = useState<AppState>("idle");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [hasUrlError, setHasUrlError] = useState(false);
  const [shouldShake, setShouldShake] = useState(false);

  // Data State
  const [subtitleData, setSubtitleData] = useState<SentenceData[]>([]);

  // i18n
  const { t } = useTranslation();

  // 抖动动画结束后重置
  useEffect(() => {
    if (shouldShake) {
      const timer = setTimeout(() => {
        setShouldShake(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [shouldShake]);

  // 使用 useCallback 包装回调函数，避免 useEffect 重复执行
  const handleTaskComplete = useCallback(
    async (data: AnalyzeResponse) => {
      if (data.status === "completed") {
        // 获取字幕内容
        if (data.subtitle_task?.task_id) {
          try {
            const subContent = await getSubtitleContent(
              data.subtitle_task.task_id
            );

            // 转换后端返回的 JSON 数据
            if (Array.isArray(subContent.content)) {
              const parsedData = convertSubtitleData(subContent.content);
              setSubtitleData(parsedData);
              setAppState("completed");
            } else {
              const errorMessage = "Invalid subtitle data format";
              toast.error(t("toast.dataFormatError"), {
                description: errorMessage,
              });
              setAppState("error");
              setErrorMsg(errorMessage);
            }
          } catch (err: any) {
            const errorMessage = err.message || "Failed to fetch subtitles";
            toast.error(t("toast.fetchSubtitleFailed"), {
              description: errorMessage,
            });
            setAppState("error");
            setErrorMsg(errorMessage);
          }
        } else {
          const errorMessage = "No subtitle generated";
          toast.error(t("toast.subtitleGenerationFailed"), {
            description: errorMessage,
          });
          setAppState("error");
          setErrorMsg(errorMessage);
        }
      } else if (data.status === "failed" || data.status === "cancelled") {
        // 显示失败 toast
        const errorMessage = data.error || data.message || "Task failed";
        toast.error(t("toast.taskFailed"), {
          description: errorMessage,
        });
        setAppState("error");
        setErrorMsg(errorMessage);
      }
    },
    [t]
  );

  const handleTaskError = useCallback(
    (err: Error) => {
      const errorMessage = err.message || "Connection error";
      toast.error(t("toast.connectionError"), {
        description: errorMessage,
      });
      setAppState("error");
      setErrorMsg(errorMessage);
    },
    [t]
  );

  // 使用 SSE 监听任务状态
  const { status, isConnected } = useTaskStatusStream({
    taskId,
    enabled: appState === "processing" && taskId !== null,
    onComplete: handleTaskComplete,
    onError: handleTaskError,
  });

  // 从 SSE 状态更新 UI
  const progress = status?.progress || 0;
  const statusMessage = status?.message || "Processing video...";

  // Player State
  const playerRef = useRef<any>(null);
  const subtitleListRef = useRef<HTMLDivElement>(null);
  const activeSubtitleRef = useRef<HTMLDivElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Dictionary State
  const [dictionaryWord, setDictionaryWord] = useState<WordToken | null>(null);
  const [isDictionaryOpen, setIsDictionaryOpen] = useState(false);

  const setPlayerRef = useCallback((player: HTMLVideoElement) => {
    if (!player) return;
    playerRef.current = player;
  }, []);

  // 1. 处理开始分析
  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) {
      setHasUrlError(true);
      setShouldShake(true);
      return;
    }

    // 验证是否是有效的 YouTube URL
    if (!isValidYouTubeUrl(url)) {
      const errorMessage = "Please enter a valid YouTube URL";
      setHasUrlError(true);
      setShouldShake(true);
      toast.error(t("toast.startTaskFailed"), {
        description: errorMessage,
      });
      return;
    }

    setHasUrlError(false);
    setAppState("processing");
    setErrorMsg("");

    try {
      // 创建视频分析任务
      const initRes = await startVideoAnalysis(url);
      setTaskId(initRes.task_id);
      // SSE 会自动开始监听任务状态更新
    } catch (err: any) {
      const errorMessage = err.message || "Failed to start task";
      toast.error(t("toast.startTaskFailed"), {
        description: errorMessage,
      });
      setAppState("error");
      setErrorMsg(errorMessage);
      setTaskId(null);
    }
  };

  // 2. 播放器时间更新回调
  const handleTimeUpdate = () => {
    const currentTime = playerRef.current?.currentTime ?? 0;
    setCurrentTime(currentTime);
  };

  // 3. 点击句子跳转视频
  const seekTo = (seconds: number) => {
    const player = playerRef.current;
    if (!player) return;
    player?.api?.seekTo(seconds);
    setIsPlaying(true); // Auto play on seek
  };

  // 4. 点击单词查询字典
  const handleTokenDictionaryClick = (token: WordToken) => {
    setDictionaryWord(token);
    setIsDictionaryOpen(true);
  };

  // ----------------------------------------------------------------
  // UI Renderers
  // ----------------------------------------------------------------

  // 输入界面和处理中界面已移至独立组件

  // 结果界面 (播放器 + 截图还原的卡片)
  const renderCompletedView = () => {
    // 找到当前正在播放的句子索引
    const currentTimeMs = currentTime * 1000; // 转换为毫秒
    const activeIndex = subtitleData.findIndex(
      (s) => currentTime >= s.startTime && currentTime < s.endTime
    );

    return (
      <div className="flex h-screen flex-col px-4 pb-4 pt-4">
        {/* Header */}
        <AnalysisHeader onAnalyzeAnother={() => setAppState("idle")} />

        {/* 视频和字幕上下结构 */}
        <div className="flex min-h-0 flex-1 flex-col gap-4">
          {/* 1. 视频播放器区域 */}
          <div className="group relative aspect-video flex-shrink-0 overflow-hidden rounded-2xl bg-black shadow-lg ring-1 ring-gray-900/5">
            {url && (
              <>
                <ReactPlayer
                  ref={playerRef}
                  src={url}
                  width="100%"
                  height="100%"
                  playing={isPlaying}
                  controls={false}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onTimeUpdate={handleTimeUpdate}
                  crossOrigin="anonymous"
                  config={{
                    youtube: {
                      playerVars: {
                        controls: 0,
                        rel: 0,
                        enablejsapi: 1,
                        cc_load_policy: 0, // 默认关闭字幕
                        iv_load_policy: 3, // 关闭视频注释
                      },
                    } as any,
                  }}
                />
                {/* 自定义播放/暂停按钮 */}
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-all duration-200 hover:bg-black/30 group-hover:opacity-100"
                >
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white/90 shadow-lg transition-all duration-200 hover:scale-110 hover:bg-white">
                    {isPlaying ? (
                      <Pause
                        className="ml-1 h-10 w-10 text-gray-900"
                        fill="currentColor"
                      />
                    ) : (
                      <Play
                        className="ml-1 h-10 w-10 text-gray-900"
                        fill="currentColor"
                      />
                    )}
                  </div>
                </button>
              </>
            )}
          </div>

          {/* 2. 字幕列表 (滚动区域) */}
          <SubtitleList
            subtitleData={subtitleData}
            activeIndex={activeIndex}
            onSeek={seekTo}
            onTokenDictionaryClick={handleTokenDictionaryClick}
            onPause={() => setIsPlaying(false)}
            currentTime={currentTimeMs}
            subtitleListRef={subtitleListRef}
            activeSubtitleRef={activeSubtitleRef}
          />
        </div>

        {/* 字典抽屉/弹出框 */}
        <DictionaryDrawer
          isOpen={isDictionaryOpen}
          onClose={() => setIsDictionaryOpen(false)}
          word={dictionaryWord}
        />
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 selection:bg-blue-100">
      <div className="mx-auto max-w-screen-md">
        {appState === "idle" && (
          <InputView
            url={url}
            onUrlChange={setUrl}
            onSubmit={handleAnalyze}
            hasError={hasUrlError}
            shouldShake={shouldShake}
          />
        )}
        {appState === "processing" && (
          <ProcessingView progress={progress} statusMessage={statusMessage} />
        )}
        {appState === "completed" && renderCompletedView()}

        {appState === "error" && (
          <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-4 text-red-600 animate-in zoom-in">
            <AlertCircle size={48} />
            <h3 className="text-xl font-semibold">Something went wrong</h3>
            <button
              onClick={() => setAppState("idle")}
              className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm text-white transition-colors hover:bg-gray-800"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
