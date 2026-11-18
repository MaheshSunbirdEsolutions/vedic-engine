import type { NextConfig } from "next";

// /engine/* and /books/* are proxied at runtime by Route Handlers so Vercel's
// ENGINE_URL service binding resolves at request time rather than build time.
const nextConfig: NextConfig = {};

export default nextConfig;
