import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Quick tunnels change hostnames; allow Cloudflare trycloudflare origins in dev.
  allowedDevOrigins: ["*.trycloudflare.com"],
};

export default nextConfig;
