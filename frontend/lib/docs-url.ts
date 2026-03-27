const DEFAULT_DOCS_URL = "https://docs.routex.xoroai.cloud";

function pickFirstNonEmptyString(...values: Array<string | undefined>) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return DEFAULT_DOCS_URL;
}

const rawDocsUrl = pickFirstNonEmptyString(
  process.env.NEXT_PUBLIC_DOCS_URL,
  process.env.DOCS_ORIGIN,
  process.env.MINTLIFY_DOCS_ORIGIN,
  DEFAULT_DOCS_URL,
);

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
