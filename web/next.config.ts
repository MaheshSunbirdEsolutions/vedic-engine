import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// Share the single root `.env` across both `vedic_engine` (Python) and `web` (Next.js).
const configDir = typeof __dirname !== "undefined" ? __dirname : path.dirname(fileURLToPath(import.meta.url));
loadEnvConfig(path.resolve(configDir, ".."), process.env.NODE_ENV !== "production");

// /engine/* and /books/* are proxied at runtime by Route Handlers so Vercel's
// ENGINE_URL service binding resolves at request time rather than build time.
const nextConfig: NextConfig = {};

export default nextConfig;
