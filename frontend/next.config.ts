import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  env: {
    CLOUD: process.env.CLOUD ?? "false",
  },
};

export default nextConfig;
