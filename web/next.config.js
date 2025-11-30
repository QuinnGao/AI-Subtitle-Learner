/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // swcMinify 在 Next.js 16 中已移除，默认启用
  // 完全禁用静态优化，所有页面都动态渲染
  output: 'standalone',
  // 跳过静态生成
  generateBuildId: async () => {
    return 'build-' + Date.now()
  },
  // 环境变量配置
  env: {
    // 确保环境变量在构建时可用
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1',
    NEXT_PUBLIC_ENV: process.env.NEXT_PUBLIC_ENV || process.env.NODE_ENV || 'development',
  },
}

module.exports = nextConfig

