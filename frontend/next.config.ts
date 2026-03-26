import type { NextConfig } from "next";
import path from "node:path";

const mintlifyDocsOrigin =
  process.env.MINTLIFY_DOCS_ORIGIN ?? "http://127.0.0.1:3001";

const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
  async redirects() {
    return [
      {
        source: "/sandbox",
        destination: "/docs/collections",
        permanent: false,
      },
    ];
  },
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: "/docs",
          destination: mintlifyDocsOrigin,
        },
        {
          source: "/docs/:path*",
          destination: `${mintlifyDocsOrigin}/:path*`,
        },
        {
          source: "/.well-known/vercel/:path*",
          destination: `${mintlifyDocsOrigin}/.well-known/vercel/:path*`,
        },
        {
          source: "/.well-known/skills/:path*",
          destination: `${mintlifyDocsOrigin}/.well-known/skills/:path*`,
        },
        {
          source: "/skill.md",
          destination: `${mintlifyDocsOrigin}/skill.md`,
        },
      ],
    };
  },
};

export default nextConfig;
