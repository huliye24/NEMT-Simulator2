"use client";

import { usePathname } from "next/navigation";
import Header from "./Header";

/**
 * Keeps the research dashboard chrome intact while giving /trade its own
 * full-screen, app-like shell (no desktop header/footer).
 */
export default function SiteChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isTradeApp = pathname?.startsWith("/trade") ?? false;

  if (isTradeApp) {
    return <>{children}</>;
  }

  return (
    <>
      <Header />
      <main className="pt-16 min-h-screen">{children}</main>
      <footer className="border-t nemt-divider py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500">
          <div>
            <span className="nemt-amber-text font-semibold">NEMT</span>
            <span className="ml-2 uppercase tracking-wider">
              Alpha · Foundation Implementation
            </span>
          </div>
          <div className="nemt-mono">
            No live trading · Mock data only · v0.1.0
          </div>
        </div>
      </footer>
    </>
  );
}
