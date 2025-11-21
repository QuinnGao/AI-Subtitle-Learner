/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  swcMinify: true,
  // 完全禁用静态优化，所有页面都动态渲染
  output: 'standalone',
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
  // 跳过静态生成
  generateBuildId: async () => {
    return 'build-' + Date.now()
  },
}

module.exports = nextConfig

