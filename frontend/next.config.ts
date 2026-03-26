import type { NextConfig } from "next";
import path from "node:path";

const mintlifyDocsOrigin =
  process.env.MINTLIFY_DOCS_ORIGIN ??
  process.env.NEXT_PUBLIC_DOCS_URL ??
  "https://docs.routex.xoroai.cloud";
const publicDocsUrl =
  process.env.NEXT_PUBLIC_DOCS_URL ?? mintlifyDocsOrigin;
const isLocalDocsOrigin = /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(
  mintlifyDocsOrigin,
);

const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
  env: {
    NEXT_PUBLIC_DOCS_URL: publicDocsUrl,
  },
  async redirects() {
    const redirects = [
      {
        source: "/sandbox",
        destination: `${publicDocsUrl}/collections`,
        permanent: false,
      },
    ];

    if (!isLocalDocsOrigin) {
      redirects.push(
        {
          source: "/docs",
          destination: publicDocsUrl,
          permanent: false,
        },
        {
          source: "/docs/:path*",
          destination: `${publicDocsUrl}/:path*`,
          permanent: false,
        },
      );
    }

    return redirects;
  },
  async rewrites() {
    if (!isLocalDocsOrigin) {
      return {
        beforeFiles: [],
      };
    }

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
