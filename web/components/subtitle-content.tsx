"use client";

import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";

interface SubtitleContentProps {
  content: string;
  onClose: () => void;
}

export function SubtitleContent({ content, onClose }: SubtitleContentProps) {
  const { t } = useTranslation();

  return (
    <div 
      data-subtitle-content
      className="mt-4 p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">{t("subtitleContent")}</h3>
        <Button onClick={onClose} size="sm" variant="ghost" className="h-6 px-2">
          {t("close")}
        </Button>
      </div>
      <div className="max-h-96 overflow-y-auto">
        <pre className="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-mono">{content}</pre>
      </div>
    </div>
  );
}

