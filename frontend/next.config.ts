import type { NextConfig } from "next";
import path from "node:path";

const {
  DEFAULT_DOCS_URL,
  buildDocsUrl,
  normalizeDocsBaseUrl,
  pickFirstNonEmptyString,
} = require("./lib/docs-origin.cjs");

const mintlifyDocsOrigin = normalizeDocsBaseUrl(
  pickFirstNonEmptyString(
    process.env.DOCS_ORIGIN,
    process.env.MINTLIFY_DOCS_ORIGIN,
    process.env.NEXT_PUBLIC_DOCS_URL,
    DEFAULT_DOCS_URL,
  ),
);
const publicDocsUrl = normalizeDocsBaseUrl({
  NEXT_PUBLIC_DOCS_URL: process.env.NEXT_PUBLIC_DOCS_URL,
  DOCS_ORIGIN: process.env.DOCS_ORIGIN,
  MINTLIFY_DOCS_ORIGIN: process.env.MINTLIFY_DOCS_ORIGIN,
});
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
        destination: buildDocsUrl(publicDocsUrl, "/collections"),
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
          destination: buildDocsUrl(publicDocsUrl, "/:path*"),
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
          destination: buildDocsUrl(mintlifyDocsOrigin, "/:path*"),
        },
        {
          source: "/.well-known/vercel/:path*",
          destination: buildDocsUrl(
            mintlifyDocsOrigin,
            "/.well-known/vercel/:path*",
          ),
        },
        {
          source: "/.well-known/skills/:path*",
          destination: buildDocsUrl(
            mintlifyDocsOrigin,
            "/.well-known/skills/:path*",
          ),
        },
        {
          source: "/skill.md",
          destination: buildDocsUrl(mintlifyDocsOrigin, "/skill.md"),
        },
      ],
    };
  },
};

export default nextConfig;
