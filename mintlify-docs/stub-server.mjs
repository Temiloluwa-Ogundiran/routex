import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const port = Number(process.env.PORT || "3001");
const docsDir = fileURLToPath(new URL(".", import.meta.url));

const navigation = [
  { label: "Overview", href: "/" },
  { label: "Authentication", href: "/authentication" },
  { label: "Collections", href: "/collections" },
  { label: "Verification", href: "/verification" },
  { label: "Payouts", href: "/payouts" },
  { label: "Webhooks", href: "/webhooks" },
  { label: "Gateway behavior", href: "/gateway-behavior" },
];

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderDocPage(slug) {
  const fileName = slug === "" ? "index.mdx" : `${slug}.mdx`;
  const source = readFileSync(join(docsDir, fileName), "utf8");
  const body = source.replace(/^---[\s\S]*?---\s*/u, "").trim();
  const lines = body.split(/\r?\n/u);
  const firstHeading = lines.find((line) => line.startsWith("# "));
  const title = (firstHeading || (slug === "" ? "# RouteX API Docs" : `# ${slug.replaceAll("-", " ")}`)).replace(
    /^#\s+/u,
    "",
  );
  const content = escapeHtml(lines.filter((line) => line !== firstHeading).join("\n").trim());

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${title}</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #0a0a0a;
        --surface: #171717;
        --border: rgba(255, 255, 255, 0.12);
        --text: #ffffff;
        --muted: rgba(255, 255, 255, 0.72);
        --brand: #fde047;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        background:
          radial-gradient(circle at top right, rgba(253, 224, 71, 0.22), transparent 28%),
          var(--bg);
        color: var(--text);
        font-family: Inter, system-ui, sans-serif;
      }
      .shell {
        width: min(1100px, calc(100% - 40px));
        margin: 32px auto;
        padding: 28px;
        border-radius: 32px;
        border: 1px solid var(--border);
        background: rgba(23, 23, 23, 0.92);
        backdrop-filter: blur(18px);
      }
      .brand {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        text-decoration: none;
        color: var(--text);
      }
      .mark {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        border-radius: 999px;
        background: var(--brand);
        color: var(--bg);
        font-weight: 800;
      }
      nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 28px;
      }
      nav a {
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid var(--border);
        color: var(--muted);
        text-decoration: none;
      }
      nav a:hover {
        color: var(--bg);
        background: var(--brand);
      }
      h1 {
        margin: 0 0 20px;
        font-size: clamp(2.25rem, 5vw, 4rem);
        line-height: 1;
      }
      pre {
        margin: 0;
        white-space: pre-wrap;
        font: 500 15px/1.7 "SFMono-Regular", Consolas, monospace;
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <a class="brand" href="/">
        <span class="mark">R</span>
        <strong>RouteX Docs Preview</strong>
      </a>
      <nav>
        ${navigation
          .map((item) => `<a href="${item.href}">${item.label}</a>`)
          .join("")}
      </nav>
      <h1>${escapeHtml(title)}</h1>
      <pre>${content}</pre>
    </main>
  </body>
</html>`;
}

const server = createServer((request, response) => {
  const url = new URL(request.url || "/", `http://${request.headers.host || "127.0.0.1"}`);
  const slug = url.pathname === "/" ? "" : url.pathname.replace(/^\/+|\/+$/gu, "");
  const supportedSlugs = new Set([
    "",
    "authentication",
    "collections",
    "verification",
    "payouts",
    "webhooks",
    "gateway-behavior",
  ]);

  if (!supportedSlugs.has(slug)) {
    response.statusCode = 404;
    response.setHeader("Content-Type", "text/html; charset=utf-8");
    response.end("<h1>Not found</h1>");
    return;
  }

  response.statusCode = 200;
  response.setHeader("Content-Type", "text/html; charset=utf-8");
  response.end(renderDocPage(slug));
});

server.listen(port, "127.0.0.1");
