from pathlib import Path


DOCS_DIR = Path("mintlify-docs")
OPENAPI_PAGES = ("collections.mdx", "verification.mdx", "payouts.mdx")
PUBLIC_DOCS_PAGES = (
    "index",
    "collections",
    "verification",
    "payouts",
    "webhooks",
    "gateway-behavior",
)


def test_api_reference_pages_use_openapi_frontmatter():
    for page in OPENAPI_PAGES:
        content = (DOCS_DIR / page).read_text(encoding="utf-8")

        assert "openapi:" in content
        assert "\napi:" not in content


def test_public_docs_are_curated_and_concise():
    docs_json = (DOCS_DIR / "docs.json").read_text(encoding="utf-8")
    index_content = (DOCS_DIR / "index.mdx").read_text(encoding="utf-8")
    webhooks_content = (DOCS_DIR / "webhooks.mdx").read_text(encoding="utf-8")

    assert '"pages": ["index"]' in docs_json
    for page in PUBLIC_DOCS_PAGES:
        assert page in docs_json

    assert "Quick start" not in index_content
    assert "POST /api/v1/initiate" in index_content
    assert "GET /api/v1/transactions/verify" in index_content
    assert "POST /api/v1/payout" in index_content
    assert "X-AGGREGATOR-SIGNATURE" in webhooks_content


def test_api_reference_group_points_to_live_public_openapi():
    docs_json = (DOCS_DIR / "docs.json").read_text(encoding="utf-8")

    assert '"group": "API Reference"' in docs_json
    assert '"openapi": "https://routexapi.xoroai.cloud/public/openapi.json"' in docs_json
