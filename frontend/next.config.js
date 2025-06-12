/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  async redirects() {
    return [
      {
        source: '/v1',
        destination: '/',
        permanent: true,
      },
      {
        source: '/v1/:path*',
        destination: '/:path*',
        permanent: true,
      },
    ];
  },
};

// Set assetPrefix only in production/export mode
if (process.env.NODE_ENV === 'production') {
  nextConfig.assetPrefix = '/static';
}

// Add proxy configuration for development
if (process.env.NODE_ENV !== 'production') {
  nextConfig.rewrites = async function () {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/ws/:path*',
        destination: 'http://localhost:8000/ws/:path*',
      },
    ];
  };
}

module.exports = nextConfig;