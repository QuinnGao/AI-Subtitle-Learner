import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import zhCN from '@/locales/zh-CN.json'
import enUS from '@/locales/en-US.json'

// 检查是否在浏览器环境
const isBrowser = typeof window !== 'undefined'

if (!i18n.isInitialized) {
  const initConfig: any = {
    resources: {
      'zh-CN': {
        translation: zhCN,
      },
      'en-US': {
        translation: enUS,
      },
    },
    fallbackLng: 'zh-CN',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false, // 禁用Suspense以避免SSR问题
    },
  }

  // 只在浏览器环境使用LanguageDetector
  if (isBrowser) {
    i18n.use(LanguageDetector)
  }

  i18n.use(initReactI18next).init(initConfig)
}

export default i18n

