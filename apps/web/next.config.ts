import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Pin the workspace root to this app. Without this, Next walks up looking
  // for a lockfile and can infer the repo root as the workspace — which puts
  // the whole Meridian tree (meridian.db written by the backend, .venv,
  // session notes) under Turbopack's file watcher and triggers an endless
  // rebuild loop that pegs the CPU.
  turbopack: {
    root: path.join(__dirname),
  },
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
