"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Video } from "lucide-react";
import { toast } from "sonner";
import { startVideoAnalysis } from "@/lib/api";
import { isValidYouTubeUrl } from "@/lib/utils";

interface VideoDownloadFormProps {
  onTaskCreated: (taskId: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

export function VideoDownloadForm({
  onTaskCreated,
  disabled = false,
  isLoading = false,
}: VideoDownloadFormProps) {
  const { t } = useTranslation();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [shouldShake, setShouldShake] = useState(false);

  // 抖动动画结束后重置
  useEffect(() => {
    if (shouldShake) {
      const timer = setTimeout(() => {
        setShouldShake(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [shouldShake]);

  const handleDownload = async () => {
    if (!youtubeUrl.trim()) {
      setHasError(true);
      setShouldShake(true);
      toast.error(t("error"), {
        description: t("invalidUrl"),
      });
      return;
    }

    if (!isValidYouTubeUrl(youtubeUrl)) {
      setHasError(true);
      setShouldShake(true);
      toast.error(t("error"), {
        description: t("invalidUrl"),
      });
      return;
    }

    setHasError(false);

    setIsSubmitting(true);

    try {
      const response = await startVideoAnalysis(youtubeUrl.trim());

      onTaskCreated(response.task_id);
      setIsSubmitting(false);

      toast.success(t("success"), {
        description: t("videoDownload.taskCreated"),
      });
    } catch (error: any) {
      console.error("Error creating video download task:", error);
      setIsSubmitting(false);
      toast.error(t("error"), {
        description:
          error.response?.data?.detail ||
          error.message ||
          t("videoDownload.createFailed"),
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="youtube-url">{t("youtubeUrl")}</Label>
        <Input
          id="youtube-url"
          type="url"
          placeholder={t("youtubeUrlPlaceholder")}
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          disabled={disabled || isSubmitting || isLoading}
          className={`
            ${hasError ? "!border-red-500 focus-visible:!ring-red-500" : ""}
            ${shouldShake ? "animate-shake" : ""}
          `}
        />
      </div>

      <Button
        type="button"
        onClick={handleDownload}
        className={`
          w-full
          ${hasError ? "bg-red-500 text-white hover:bg-red-600" : ""}
          ${shouldShake ? "animate-shake" : ""}
        `}
        disabled={disabled || isSubmitting || isLoading || !youtubeUrl.trim()}
      >
        {isSubmitting || isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {isSubmitting
              ? t("videoDownload.downloading")
              : t("videoDownload.processing")}
          </>
        ) : (
          <>
            <Video className="mr-2 h-4 w-4" />
            {t("videoDownload.downloadVideo")}
          </>
        )}
      </Button>
    </div>
  );
}
