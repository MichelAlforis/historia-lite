/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  typescript: {
    ignoreBuildErrors: false,
  },
  // Désactiver styled-jsx pour éviter les problèmes SSR
  compiler: {
    styledJsx: false,
  },
}

module.exports = nextConfig
