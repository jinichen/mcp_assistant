/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    // Disable features that might conflict with Node.js v22
    serverComponentsExternalPackages: [],
    optimizeCss: false,
  },
  // Increase timeouts for Node.js v22 compatibility
  serverRuntimeConfig: {
    nodeTimeout: 120000, // 2 minutes
  },
  // Specify allowed origins for Node.js v22 security features
  images: {
    domains: ['localhost'],
  },
  // Ensure compatibility with Node.js v22
  webpack: (config, { isServer }) => {
    // Apply fixes for Node.js v22 compatibility
    if (isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        os: false,
      };
    }
    
    return config;
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // 代理到后端API
      },
    ];
  },
}

module.exports = nextConfig 