import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import nextEnv from "@next/env";

const { loadEnvConfig } = nextEnv;

// Load the single root `.env` into process.env BEFORE Next.js starts so
// Turbopack, proxy.ts, Server Components, and client bundles all receive it.
const webDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(webDir, "..");
loadEnvConfig(rootDir, process.argv[2] === "dev");

const nextBin = path.join(webDir, "node_modules", "next", "dist", "bin", "next");
const child = spawn(process.execPath, [nextBin, ...process.argv.slice(2)], {
  cwd: webDir,
  stdio: "inherit",
  env: process.env,
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => child.kill(sig));
}
child.on("exit", (code, signal) => {
  process.exit(code ?? (signal ? 1 : 0));
});
