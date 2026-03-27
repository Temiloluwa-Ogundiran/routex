import type { Metadata } from "next";
import { PostHogIdentityBridge } from "../components/analytics/posthog-identity-bridge";
import { RoutexSurfaceController } from "../components/layout/routex-surface-controller";
import "./fonts.css";
import "./globals.css";
import "./dualmode.css";

export const metadata: Metadata = {
  title: "RouteX",
  description: "Smart payment routing for collections and payouts.",
};

const SURFACE_BOOTSTRAP_SCRIPT = `
(() => {
  const surface =
    window.location.pathname.startsWith('/dashboard') ||
    window.location.pathname.startsWith('/admin')
      ? 'ops'
      : 'public';

  document.documentElement.dataset.rxSurface = surface;
  if (document.body) {
    document.body.dataset.rxSurface = surface;
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html data-rx-surface="public" lang="en">
      <head />
      <body className="routex-root" data-rx-surface="public">
        <script dangerouslySetInnerHTML={{ __html: SURFACE_BOOTSTRAP_SCRIPT }} />
        <PostHogIdentityBridge />
        <RoutexSurfaceController />
        {children}
      </body>
    </html>
  );
}
