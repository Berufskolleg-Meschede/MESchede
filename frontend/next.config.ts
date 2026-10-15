import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: process.env.MES_NEXT_DIST_DIR ?? '.next',
  turbopack: {
    root: process.cwd(),
  },
  output: "standalone",
};

export default nextConfig;
