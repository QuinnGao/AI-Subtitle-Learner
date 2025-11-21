"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { AlertCircle, Play, Pause } from "lucide-react";
import { downloadVideoByUrl, getVideoDownloadTaskStatus, getSubtitleContent, type VideoDownloadResponse } from "@/lib/api";
import ReactPlayer from "react-player";
import { SubtitleList } from "@/components/subtitle-list";
import { AnalysisHeader } from "@/components/analysis-header";
import { InputView } from "@/components/input-view";
import { ProcessingView } from "@/components/processing-view";
import type { SentenceData, TokenType, WordToken } from "@/components/subtitle-item";

// ------------------------------------------------------------------
// 类型定义：UI展示用的富文本结构
// ------------------------------------------------------------------
// 类型定义已移至 @/components/subtitle-item

type AppState = "idle" | "processing" | "completed" | "error";

// ------------------------------------------------------------------
// 将后端返回的 JSON 数据转换为前端需要的格式
// ------------------------------------------------------------------
interface BackendSubtitleItem {
  start: number; // 秒
  end: number; // 秒
  original_text: string;
  translation: string;
  tokens?: Array<{
    text: string;
    furigana?: string;
    romaji?: string;
    type?: string;
  }>;
}

const convertSubtitleData = (backendData: BackendSubtitleItem[]): SentenceData[] => {
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
      startTime: item.start,
      endTime: item.end,
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
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Data State
  const [subtitleData, setSubtitleData] = useState<SentenceData[]>([]);

  // Player State
  const playerRef = useRef<any>(null);
  const subtitleListRef = useRef<HTMLDivElement>(null);
  const activeSubtitleRef = useRef<HTMLDivElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const setPlayerRef = useCallback((player: HTMLVideoElement) => {
    if (!player) return;
    debugger;
    playerRef.current = player;
    console.log(player);
  }, []);

  // 1. 处理开始分析
  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setAppState("processing");
    setProgress(5);
    setStatusMessage("Initializing task...");
    setErrorMsg("");

    try {
      // 发起下载任务
      const initRes = await downloadVideoByUrl(url);
      const taskId = initRes.task_id;

      // 开始轮询
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await getVideoDownloadTaskStatus(taskId);

          setProgress(statusRes.progress);
          setStatusMessage(statusRes.message || "Processing video...");

          if (statusRes.status === "failed" || statusRes.status === "cancelled") {
            clearInterval(pollInterval);
            setAppState("error");
            setErrorMsg(statusRes.error || "Task failed");
          }

          if (statusRes.status === "completed") {
            clearInterval(pollInterval);
            setStatusMessage("Fetching subtitles...");

            // 获取字幕内容
            // 注意：如果 subtitle_task 也是异步的，这里可能还需要一层轮询 subtitle status
            // 假设此时 video task completed 意味着字幕也准备好了
            if (statusRes.subtitle_task?.task_id) {
              const subContent = await getSubtitleContent(statusRes.subtitle_task.task_id);

              // 转换后端返回的 JSON 数据
              if (Array.isArray(subContent.content)) {
                const parsedData = convertSubtitleData(subContent.content);
                setSubtitleData(parsedData);
                setAppState("completed");
              } else {
                setAppState("error");
                setErrorMsg("Invalid subtitle data format");
              }
            } else {
              // Fallback handling if no subtitle task
              setAppState("error");
              setErrorMsg("No subtitle generated");
            }
          }
        } catch (err) {
          console.error(err);
          // Continue polling even if one request fails, unless it's critical
        }
      }, 2000); // 每2秒轮询一次
    } catch (err: any) {
      setAppState("error");
      setErrorMsg(err.message || "Failed to start task");
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

  // ----------------------------------------------------------------
  // UI Renderers
  // ----------------------------------------------------------------

  // 输入界面和处理中界面已移至独立组件

  // 结果界面 (播放器 + 截图还原的卡片)
  const renderCompletedView = () => {
    // 找到当前正在播放的句子索引
    const activeIndex = subtitleData.findIndex((s) => currentTime >= s.startTime && currentTime < s.endTime);

    return (
      <div className="h-screen flex flex-col pt-4 pb-4 px-4">
        {/* Header */}
        <AnalysisHeader onAnalyzeAnother={() => setAppState("idle")} />

        {/* 视频和字幕上下结构 */}
        <div className="flex-1 flex flex-col gap-4 min-h-0">
          {/* 1. 视频播放器区域 */}
          <div className="relative aspect-video bg-black rounded-2xl overflow-hidden shadow-lg ring-1 ring-gray-900/5 group flex-shrink-0">
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
                  className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/30 transition-all duration-200 opacity-0 group-hover:opacity-100"
                >
                  <div className="w-20 h-20 rounded-full bg-white/90 hover:bg-white flex items-center justify-center shadow-lg transition-all duration-200 hover:scale-110">
                    {isPlaying ? (
                      <Pause className="w-10 h-10 text-gray-900 ml-1" fill="currentColor" />
                    ) : (
                      <Play className="w-10 h-10 text-gray-900 ml-1" fill="currentColor" />
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
            subtitleListRef={subtitleListRef}
            activeSubtitleRef={activeSubtitleRef}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 selection:bg-blue-100">
      {appState === "idle" && <InputView url={url} onUrlChange={setUrl} onSubmit={handleAnalyze} />}
      {appState === "processing" && <ProcessingView progress={progress} statusMessage={statusMessage} />}
      {appState === "completed" && renderCompletedView()}

      {appState === "error" && (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4 text-red-600 animate-in zoom-in">
          <AlertCircle size={48} />
          <h3 className="text-xl font-semibold">Something went wrong</h3>
          <p className="text-gray-600">{errorMsg}</p>
          <button
            onClick={() => setAppState("idle")}
            className="mt-4 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
