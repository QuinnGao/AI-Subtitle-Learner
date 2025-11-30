import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 验证是否是有效的 YouTube URL
 * 支持以下格式：
 * - https://www.youtube.com/watch?v=VIDEO_ID
 * - https://youtube.com/watch?v=VIDEO_ID
 * - https://youtu.be/VIDEO_ID
 * - https://www.youtube.com/embed/VIDEO_ID
 * - https://m.youtube.com/watch?v=VIDEO_ID
 * - https://youtube.com/watch?v=VIDEO_ID&list=...
 * - https://www.youtube.com/shorts/VIDEO_ID
 * - https://youtube.com/shorts/VIDEO_ID
 */
export function isValidYouTubeUrl(url: string): boolean {
  if (!url || typeof url !== "string") {
    return false
  }

  try {
    // 移除首尾空格
    const trimmedUrl = url.trim()

    // YouTube URL 正则表达式模式
    const youtubePatterns = [
      // 标准格式: https://www.youtube.com/watch?v=VIDEO_ID
      /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/watch\?v=[\w-]+/i,
      // 短链接格式: https://youtu.be/VIDEO_ID
      /^https?:\/\/(www\.)?youtu\.be\/[\w-]+/i,
      // 嵌入格式: https://www.youtube.com/embed/VIDEO_ID
      /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/i,
      // Shorts 格式: https://www.youtube.com/shorts/VIDEO_ID
      /^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+/i,
      // 移动端格式: https://m.youtube.com/watch?v=VIDEO_ID
      /^https?:\/\/m\.youtube\.com\/watch\?v=[\w-]+/i,
    ]

    // 检查是否匹配任一模式
    return youtubePatterns.some((pattern) => pattern.test(trimmedUrl))
  } catch (error) {
    // 如果 URL 解析失败，返回 false
    return false
  }
}
