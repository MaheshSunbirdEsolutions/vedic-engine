import type { NextConfig } from "next";

// All calls to /engine/* are proxied to the Python Vedic Engine (FastAPI).
const ENGINE_URL = process.env.ENGINE_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  experimental: { proxyTimeout: 180_000 },   // AI answers in the Ask tab can take up to a minute
  async rewrites() {
    return [
      { source: "/engine/:path*", destination: `${ENGINE_URL}/:path*` },
      { source: "/books/:path*", destination: `${ENGINE_URL}/books/:path*` },
    ];
  },
};

export default nextConfig;
