import { useState, useEffect, useRef, useCallback } from "react";

export interface PollingOptions<T> {
  /** 轮询函数，返回 Promise */
  pollFn: () => Promise<T>;
  /** 轮询间隔（毫秒），默认 2000 */
  interval?: number;
  /** 是否启用轮询 */
  enabled?: boolean;
  /** 判断是否应该停止轮询的函数 */
  shouldStop?: (data: T) => boolean;
  /** 轮询成功回调 */
  onSuccess?: (data: T) => void;
  /** 轮询失败回调 */
  onError?: (error: Error) => void;
  /** 轮询完成回调（无论成功或失败） */
  onComplete?: (data: T | null) => void;
}

export interface PollingResult<T> {
  /** 当前数据 */
  data: T | null;
  /** 是否正在轮询 */
  isPolling: boolean;
  /** 错误信息 */
  error: Error | null;
  /** 手动开始轮询 */
  start: () => void;
  /** 手动停止轮询 */
  stop: () => void;
}

/**
 * 轮询 Hook
 * 确保上一次轮询完成后再进行下一次
 */
export function usePolling<T>(options: PollingOptions<T>): PollingResult<T> {
  const { pollFn, interval = 2000, enabled = true, shouldStop, onSuccess, onError, onComplete } = options;
  const [data, setData] = useState<T | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const isCancelledRef = useRef(false);
  const timeoutIdRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isPollingRef = useRef(false);

  // 同步 ref 和 state
  useEffect(() => {
    isPollingRef.current = isPolling;
  }, [isPolling]);

  const stop = useCallback(() => {
    isCancelledRef.current = true;
    setIsPolling(false);
    if (timeoutIdRef.current) {
      clearTimeout(timeoutIdRef.current);
      timeoutIdRef.current = null;
    }
  }, []);

  const start = useCallback(() => {
    isCancelledRef.current = false;
    setIsPolling(true);
    setError(null);
  }, []);

  // 当 enabled 改变时，自动开始或停止轮询
  useEffect(() => {
    if (enabled && !isPollingRef.current) {
      start();
    } else if (!enabled && isPollingRef.current) {
      stop();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  useEffect(() => {
    if (!isPolling) {
      return;
    }

    const poll = async () => {
      if (isCancelledRef.current) {
        return;
      }

      try {
        const result = await pollFn();
        setData(result);
        setError(null);

        // 检查是否应该停止轮询
        const shouldStopPolling = shouldStop ? shouldStop(result) : false;

        if (shouldStopPolling) {
          setIsPolling(false);
          onSuccess?.(result);
          onComplete?.(result);
          return;
        }

        // 继续下一次轮询
        if (!isCancelledRef.current) {
          timeoutIdRef.current = setTimeout(poll, interval);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        setIsPolling(false);
        onError?.(error);
        onComplete?.(data ?? null);
      }
    };

    // 立即开始第一次轮询
    poll();

    return () => {
      stop();
    };
  }, [isPolling, pollFn, interval, shouldStop, onSuccess, onError, onComplete, data, stop]);

  return {
    data,
    isPolling,
    error,
    start,
    stop,
  };
}
