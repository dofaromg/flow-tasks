/** @type {import('next').NextConfig} */
// output: 'standalone' matches the Dockerfile (.next/standalone + server.js).
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
};
export default nextConfig;
