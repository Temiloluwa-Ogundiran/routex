const test = require("node:test");
const assert = require("node:assert/strict");

const {
  pickFirstNonEmptyString,
  normalizeDocsBaseUrl,
  buildDocsUrl,
} = require("../lib/docs-origin.cjs");

test("pickFirstNonEmptyString skips blank values", () => {
  assert.equal(
    pickFirstNonEmptyString("", "   ", undefined, "https://docs.routex.xoroai.cloud"),
    "https://docs.routex.xoroai.cloud",
  );
});

test("normalizeDocsBaseUrl falls back when configured values are blank", () => {
  assert.equal(
    normalizeDocsBaseUrl({
      DOCS_ORIGIN: "",
      MINTLIFY_DOCS_ORIGIN: "",
      NEXT_PUBLIC_DOCS_URL: "",
    }),
    "https://docs.routex.xoroai.cloud",
  );
});

test("buildDocsUrl appends paths without double slashes", () => {
  assert.equal(
    buildDocsUrl("https://docs.routex.xoroai.cloud/", "/collections"),
    "https://docs.routex.xoroai.cloud/collections",
  );
});
