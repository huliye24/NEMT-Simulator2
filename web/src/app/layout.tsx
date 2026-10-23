import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./trade.css";
import "./studio.css";
import "./studio-v2.css";
import "./studio-v3.css";
import SiteChrome from "@/components/SiteChrome";

export const metadata: Metadata = {
  title: {
    default: "NEMT — AI Financial Intelligence",
    template: "%s · NEMT",
  },
  description:
    "NEMT (Neural Economic Momentum Theory) — a mobile-first Binance Spot DEMO/Testnet terminal and financial intelligence platform.",
  applicationName: "NEMT",
  icons: {
    icon: [
      { url: "/icons/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: "/icons/apple-touch-icon.png",
  },
  appleWebApp: {
    capable: true,
    title: "NEMT",
    statusBarStyle: "black-translucent",
  },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#04070c",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased bg-nemt-bg-base text-slate-100 nemt-grid-bg min-h-screen">
        <SiteChrome>{children}</SiteChrome>
      </body>
    </html>
  );
}
