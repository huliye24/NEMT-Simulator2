"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/market", label: "Market" },
  { href: "/analysis", label: "Analysis" },
  { href: "/simulation", label: "Simulation" },
  { href: "/journal", label: "Journal" },
  { href: "/settings", label: "Settings" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[var(--nemt-bg-panel)] border-b border-[var(--nemt-border)]">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
              <span className="text-slate-900 font-bold text-sm">N</span>
            </div>
            <span className="text-lg font-bold text-white tracking-tight">NEMT</span>
            <span className="text-xs text-amber-400/80 border border-amber-500/30 px-1.5 py-0.5 rounded">
              ALPHA
            </span>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-1.5 rounded text-sm font-medium transition-all duration-200 ${
                  pathname === item.href
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Status */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-slate-500 font-mono">LIVE</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
