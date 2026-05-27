/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true, // Prevents loading images error in standalone builds
  },
}

module.exports = nextConfig
