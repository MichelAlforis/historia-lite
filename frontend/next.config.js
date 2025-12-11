/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: false,
  },
  // Désactiver styled-jsx pour éviter les problèmes SSR
  compiler: {
    styledJsx: false,
  },
}

module.exports = nextConfig
