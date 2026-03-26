from pathlib import Path


DOCS_DIR = Path("mintlify-docs")
OPENAPI_PAGES = ("collections.mdx", "verification.mdx", "payouts.mdx")


def test_api_reference_pages_use_openapi_frontmatter():
    for page in OPENAPI_PAGES:
        content = (DOCS_DIR / page).read_text(encoding="utf-8")

        assert "openapi:" in content
        assert "\napi:" not in content
