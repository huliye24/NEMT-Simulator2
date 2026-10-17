import type { NextConfig } from "next";

// The app only talks to the NEMT cloud API. In local development the Next
// server proxies /api/v1 to the FastAPI process on loopback, which keeps
// cookies same-origin and avoids storing exchange credentials in the browser.
const apiOrigin = process.env.NEMT_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
    ];
  },
};

export default nextConfig;
