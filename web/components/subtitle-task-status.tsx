"use client";

import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Loader2 } from "lucide-react";
import { type SubtitleResponse } from "@/lib/api";

interface SubtitleTaskStatusProps {
  status: SubtitleResponse;
  onViewSubtitle?: () => void;
  isLoadingContent?: boolean;
}

export function SubtitleTaskStatus({ status, onViewSubtitle, isLoadingContent = false }: SubtitleTaskStatusProps) {
  const { t } = useTranslation();

  return (
    <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-green-700 dark:text-green-300">
          {t("subtitleTask")} - {t("taskStatus." + status.status)}
        </p>
        {onViewSubtitle && (
          <Button 
            onClick={onViewSubtitle} 
            size="sm" 
            variant="outline" 
            disabled={status.status !== "completed" || isLoadingContent}
          >
            {isLoadingContent ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t("loading")}
              </>
            ) : (
              t("viewSubtitle")
            )}
          </Button>
        )}
      </div>
      {status.message && <p className="text-xs text-green-600 dark:text-green-400">{status.message}</p>}
      {(status.status === "running" || status.status === "pending") && (
        <div className="mt-2">
          <Progress value={status.progress || 0} />
        </div>
      )}
    </div>
  );
}

