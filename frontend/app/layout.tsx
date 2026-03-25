import type { Metadata } from "next";
import type { CSSProperties } from "react";
import { PostHogIdentityBridge } from "../components/analytics/posthog-identity-bridge";
import "./globals.css";

export const metadata: Metadata = {
  title: "RouteX",
  description: "Smart payment routing for collections and payouts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      style={
        {
          "--font-body": '"Aptos", "Segoe UI", sans-serif',
          "--font-heading": '"Bahnschrift SemiCondensed", "Arial Narrow Bold", sans-serif',
        } as CSSProperties
      }
    >
      <body>
        <PostHogIdentityBridge />
        {children}
      </body>
    </html>
  );
}
