import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "NEMT — AI Financial Intelligence",
  description:
    "NEMT (Neural Economic Momentum Theory) — Human Judgment + AI Execution. A multi-agent financial intelligence platform for the modern trader.",
  icons: {
    icon: "/nemt-logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-nemt-bg-base text-slate-100 nemt-grid-bg min-h-screen">
        <Header />
        <main className="pt-16 min-h-screen">
          {children}
        </main>
        <footer className="border-t nemt-divider py-6 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500">
            <div>
              <span className="nemt-amber-text font-semibold">NEMT</span>
              <span className="ml-2 uppercase tracking-wider">Alpha · Foundation Implementation</span>
            </div>
            <div className="nemt-mono">
              No live trading · Mock data only · v0.1.0
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
