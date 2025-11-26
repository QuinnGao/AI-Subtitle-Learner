"use client";

import { useTranslation } from "react-i18next";
import { Progress } from "@/components/ui/progress";
import { Video } from "lucide-react";
import { type AnalyzeResponse } from "@/lib/api";

interface VideoDownloadStatusProps {
  status: AnalyzeResponse;
}

export function VideoDownloadStatus({ status }: VideoDownloadStatusProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
      <div className="flex items-center justify-between">
        <div>
          <p className="flex items-center gap-2 text-sm font-medium text-blue-700 dark:text-blue-300">
            <Video className="h-4 w-4" />
            {t("videoDownload.title")} - {t("taskStatus." + status.status)}
          </p>
          <p className="mt-1 text-xs text-blue-600 dark:text-blue-400">
            {status.message}
          </p>
        </div>
      </div>

      {(status.status === "running" || status.status === "pending") && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-blue-600 dark:text-blue-400">
              {t("progress")}
            </span>
            <span className="text-blue-600 dark:text-blue-400">
              {status.progress}%
            </span>
          </div>
          <Progress value={status.progress} />
        </div>
      )}

      {status.status === "failed" && status.error && (
        <div className="rounded border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-200">
            {t("error")}: {status.error}
          </p>
        </div>
      )}

      {status.status === "completed" && (
        <div className="text-sm text-blue-700 dark:text-blue-300">
          {status.video_path && <p>视频路径: {status.video_path}</p>}
          {status.subtitle_path && <p>字幕路径: {status.subtitle_path}</p>}
          {status.thumbnail_path && <p>缩略图路径: {status.thumbnail_path}</p>}
        </div>
      )}
    </div>
  );
}
