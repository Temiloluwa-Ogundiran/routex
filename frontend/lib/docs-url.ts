const rawDocsUrl =
  process.env.NEXT_PUBLIC_DOCS_URL ??
  process.env.DOCS_ORIGIN ??
  process.env.MINTLIFY_DOCS_ORIGIN ??
  "https://docs.routex.xoroai.cloud";

export const DOCS_URL = rawDocsUrl.replace(/\/+$/, "");

export function docsHref(path = "") {
  const normalizedPath = path
    ? path.startsWith("/")
      ? path
      : `/${path}`
    : "";

  return `${DOCS_URL}${normalizedPath}`;
}

export function isExternalHref(href: string) {
  return /^https?:\/\//.test(href);
}
