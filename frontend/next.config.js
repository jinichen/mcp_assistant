const createNextIntlPlugin = require('next-intl/plugin');

const withNextIntl = createNextIntlPlugin('./src/i18n.js');

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/sse',
        destination: 'http://localhost:8000/sse',
      }
    ]
  },
  webpack: (config) => {
    config.externals.push({
      'utf-8-validate': 'commonjs utf-8-validate',
      'bufferutil': 'commonjs bufferutil',
    })
    return config
  },
  // Add proxy configuration
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Connection', value: 'keep-alive' },
          { key: 'Keep-Alive', value: 'timeout=60' },
        ],
      },
      {
        source: '/sse',
        headers: [
          { key: 'Connection', value: 'keep-alive' },
          { key: 'Keep-Alive', value: 'timeout=60' },
        ],
      }
    ]
  },
}

module.exports = withNextIntl(nextConfig) 