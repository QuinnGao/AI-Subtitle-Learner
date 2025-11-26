import { useEffect, useRef, useState } from "react";
import {
  subscribeTaskStatus,
  type AnalyzeResponse,
} from "@/lib/api";

interface UseTaskStatusStreamOptions {
  taskId: string | null;
  enabled?: boolean;
  onComplete?: (data: AnalyzeResponse) => void;
  onError?: (error: Error) => void;
}

interface UseTaskStatusStreamResult {
  status: AnalyzeResponse | null;
  isConnected: boolean;
  error: Error | null;
}

/**
 * Hook for streaming task status updates via Server-Sent Events (SSE)
 * 
 * @example
 * ```tsx
 * const { status, isConnected } = useTaskStatusStream({
 *   taskId: "task-123",
 *   enabled: true,
 *   onComplete: (data) => {
 *     console.log("Task completed:", data);
 *   }
 * });
 * ```
 */
export function useTaskStatusStream({
  taskId,
  enabled = true,
  onComplete,
  onError,
}: UseTaskStatusStreamOptions): UseTaskStatusStreamResult {
  const [status, setStatus] = useState<AnalyzeResponse | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const closeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!taskId || !enabled) {
      return;
    }

    setIsConnected(true);
    setError(null);

    const close = subscribeTaskStatus(
      taskId,
      (data) => {
        setStatus(data);
        
        // 如果任务完成或失败，调用完成回调
        if (
          data.status === "completed" ||
          data.status === "failed" ||
          data.status === "cancelled"
        ) {
          setIsConnected(false);
          onComplete?.(data);
          close();
        }
      },
      (err) => {
        setError(err);
        setIsConnected(false);
        onError?.(err);
      }
    );

    closeRef.current = close;

    return () => {
      close();
      closeRef.current = null;
    };
    // 注意：onComplete 和 onError 应该由调用方使用 useCallback 包装
    // 这里不将它们加入依赖项，避免不必要的重新连接
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId, enabled]);

  return {
    status,
    isConnected,
    error,
  };
}

