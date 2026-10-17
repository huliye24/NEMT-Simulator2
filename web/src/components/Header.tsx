"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "./Logo";
import { classNames } from "@/lib/format";
import { MemoryIndicator } from "./MemoryIndicator";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/market", label: "Market" },
  { href: "/analysis", label: "Analysis" },
  { href: "/simulation", label: "Simulation" },
  { href: "/journal", label: "Journal" },
  { href: "/settings", label: "Settings" },
];

interface HeaderProps {
  /** Optional right-side slot (e.g. clock, status) */
  rightSlot?: React.ReactNode;
}

export default function Header({ rightSlot }: HeaderProps) {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-nemt-bg-deep/85 backdrop-blur-md border-b nemt-divider">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Logo size={32} withWordmark href="/" />

          <nav className="hidden md:flex items-center gap-0.5">
            {navItems.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={classNames(
                    "px-3 py-1.5 rounded-md text-[13px] font-medium transition-all duration-150",
                    active
                      ? "text-amber-300 bg-amber-500/10 ring-1 ring-amber-500/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-2 sm:gap-3">
            {rightSlot}
            <Link
              href="/trade"
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-semibold uppercase tracking-wider text-cyan-300 bg-cyan-500/10 ring-1 ring-cyan-400/25 hover:bg-cyan-500/15 transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-300" />
              Trade
            </Link>
            <MemoryIndicator />
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-md bg-emerald-500/10 ring-1 ring-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] font-semibold tracking-wider text-emerald-300 uppercase">
                Alpha
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
