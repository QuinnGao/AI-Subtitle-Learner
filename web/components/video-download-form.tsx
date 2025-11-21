"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Video } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { downloadVideoByUrl } from "@/lib/api";

interface VideoDownloadFormProps {
  onTaskCreated: (taskId: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

export function VideoDownloadForm({ onTaskCreated, disabled = false, isLoading = false }: VideoDownloadFormProps) {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 验证YouTube URL
  const isValidYouTubeUrl = (url: string): boolean => {
    if (!url.trim()) return false;
    const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/;
    return regex.test(url);
  };

  const handleDownload = async () => {
    if (!youtubeUrl.trim()) {
      toast({
        title: t("error"),
        description: t("invalidUrl"),
        variant: "destructive",
      });
      return;
    }

    if (!isValidYouTubeUrl(youtubeUrl)) {
      toast({
        title: t("error"),
        description: t("invalidUrl"),
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await downloadVideoByUrl(youtubeUrl.trim());

      onTaskCreated(response.task_id);
      setIsSubmitting(false);

      toast({
        title: t("success"),
        description: t("videoDownload.taskCreated"),
      });
    } catch (error: any) {
      console.error("Error creating video download task:", error);
      setIsSubmitting(false);
      toast({
        title: t("error"),
        description: error.response?.data?.detail || error.message || t("videoDownload.createFailed"),
        variant: "destructive",
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
        />
      </div>

      <Button
        type="button"
        onClick={handleDownload}
        className="w-full"
        disabled={disabled || isSubmitting || isLoading || !youtubeUrl.trim()}
      >
        {(isSubmitting || isLoading) ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {isSubmitting ? t("videoDownload.downloading") : t("videoDownload.processing")}
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

