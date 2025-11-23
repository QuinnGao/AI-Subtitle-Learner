import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

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

export interface VideoDownloadResponse {
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

export const getSubtitleTaskStatus = async (taskId: string): Promise<SubtitleResponse> => {
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

export const getSubtitleContent = async (taskId: string): Promise<{ task_id: string; content: SubtitleContentItem[] }> => {
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

export const queryDictionary = async (request: DictionaryQueryRequest): Promise<DictionaryQueryResponse> => {
  const response = await api.post<DictionaryQueryResponse>("/subtitle/dictionary/query", request);
  return response.data;
};

export const downloadVideoByUrl = async (url: string): Promise<VideoDownloadResponse> => {
  const response = await api.post<VideoDownloadResponse>(`/video/analyze?url=${encodeURIComponent(url)}`, {});
  return response.data;
};

export const getVideoDownloadTaskStatus = async (taskId: string): Promise<VideoDownloadResponse> => {
  const response = await api.get<VideoDownloadResponse>(`/video/download/${taskId}`);
  return response.data;
};
