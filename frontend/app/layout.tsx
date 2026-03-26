import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { PostHogIdentityBridge } from "../components/analytics/posthog-identity-bridge";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

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
    <html className={inter.variable} lang="en">
      <body className="routex-root">
        <PostHogIdentityBridge />
        {children}
      </body>
    </html>
  );
}
