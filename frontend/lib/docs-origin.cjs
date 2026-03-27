const DEFAULT_DOCS_URL = "https://docs.routex.xoroai.cloud";

function pickFirstNonEmptyString(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return "";
}

function stripTrailingSlashes(value) {
  return value.replace(/\/+$/, "");
}

function normalizeDocsBaseUrl(valueOrEnv) {
  if (typeof valueOrEnv === "string") {
    return stripTrailingSlashes(
      pickFirstNonEmptyString(valueOrEnv, DEFAULT_DOCS_URL),
    );
  }

  const env = valueOrEnv ?? {};
  return stripTrailingSlashes(
    pickFirstNonEmptyString(
      env.NEXT_PUBLIC_DOCS_URL,
      env.DOCS_ORIGIN,
      env.MINTLIFY_DOCS_ORIGIN,
      DEFAULT_DOCS_URL,
    ),
  );
}

function buildDocsUrl(baseUrl, path = "") {
  const normalizedBaseUrl = normalizeDocsBaseUrl(baseUrl);
  const normalizedPath = path
    ? path.startsWith("/")
      ? path
      : `/${path}`
    : "";

  return `${normalizedBaseUrl}${normalizedPath}`;
}

module.exports = {
  DEFAULT_DOCS_URL,
  buildDocsUrl,
  normalizeDocsBaseUrl,
  pickFirstNonEmptyString,
  stripTrailingSlashes,
};
