import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface SubtitleResponse {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  queued_at?: string;
  started_at?: string;
  completed_at?: string;
  progress: number;
  message: string;
  error?: string;
  output_path?: string;
}

export interface SubtitleTaskInfo {
  task_id?: string;
  status?: string;
  progress?: number;
  message?: string;
  output_path?: string;
}

export interface AnalyzeResponse {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  queued_at?: string;
  started_at?: string;
  completed_at?: string;
  progress: number;
  message: string;
  error?: string;
  output_path?: string;
  video_path?: string;
  subtitle_path?: string;
  thumbnail_path?: string;
  subtitle_task?: SubtitleTaskInfo;
}

export const getSubtitleTaskStatus = async (
  taskId: string
): Promise<SubtitleResponse> => {
  const response = await api.get<SubtitleResponse>(`/subtitle/${taskId}`);
  return response.data;
};

export interface SubtitleContentItem {
  start_time: number; // 毫秒
  end_time: number; // 毫秒
  original_text: string;
  translation: string;
  tokens?: Array<{
    text: string;
    furigana?: string;
    romaji?: string;
    type?: string;
    start_time?: number; // 毫秒
    end_time?: number; // 毫秒
  }>;
}

export const getSubtitleContent = async (
  taskId: string
): Promise<{ task_id: string; content: SubtitleContentItem[] }> => {
  const response = await api.get(`/subtitle/${taskId}/content`);
  return response.data;
};

export interface DictionaryQueryRequest {
  word: string;
  furigana?: string;
  romaji?: string;
  part_of_speech?: string;
}

export interface DictionaryMeaning {
  meaning: string;
  example?: string;
  example_translation?: string;
}

export interface DictionaryQueryResponse {
  word: string;
  pronunciation: {
    furigana: string;
    romaji: string;
  };
  part_of_speech: string;
  meanings: DictionaryMeaning[];
  usage_notes?: string;
  error?: string;
}

export const queryDictionary = async (
  request: DictionaryQueryRequest
): Promise<DictionaryQueryResponse> => {
  const response = await api.post<DictionaryQueryResponse>(
    "/dictionary/query",
    request
  );
  return response.data;
};

/**
 * 开始视频分析任务
 * 从 YouTube URL 创建分析任务（下载音频、转录、处理字幕）
 *
 * @param url YouTube 视频 URL
 * @returns 任务响应，包含 task_id 和初始状态
 */
export const startVideoAnalysis = async (
  url: string
): Promise<AnalyzeResponse> => {
  const response = await api.post<AnalyzeResponse>(
    `/video/analyze?url=${encodeURIComponent(url)}`,
    {}
  );
  return response.data;
};

/**
 * 订阅任务状态更新（使用 Server-Sent Events）
 * 通过 SSE 实时接收任务状态变化，比轮询更高效
 *
 * @param taskId 任务ID
 * @param onMessage 接收到状态更新时的回调
 * @param onError 连接错误时的回调
 * @returns 关闭订阅的函数
 */
export const subscribeTaskStatus = (
  taskId: string,
  onMessage: (data: AnalyzeResponse) => void,
  onError?: (error: Error) => void
): (() => void) => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";
  const eventSource = new EventSource(
    `${API_BASE_URL}/video/analyze/${taskId}/stream`
  );

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as AnalyzeResponse;
      onMessage(data);
    } catch (error) {
      console.error("Failed to parse SSE message:", error);
      onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  };

  eventSource.onerror = (error) => {
    // EventSource 在连接关闭时会触发 onerror
    // 只有当 readyState 为 CLOSED (2) 时才认为是真正的错误
    if (eventSource.readyState === EventSource.CLOSED) {
      console.error("SSE connection closed:", error);
      onError?.(new Error("SSE connection closed"));
      eventSource.close();
    } else if (eventSource.readyState === EventSource.CONNECTING) {
      // 连接中，可能是网络问题，但不立即关闭
      console.warn("SSE connection issue, retrying...");
    }
    // EventSource.CONNECTING (0) 或 EventSource.OPEN (1) 时不处理
  };

  // 返回关闭函数
  return () => {
    eventSource.close();
  };
};
