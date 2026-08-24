import type { ReactNode } from "react";
import { classNames } from "@/lib/format";

interface CardProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  rightSlot?: ReactNode;
  className?: string;
  children: ReactNode;
  /** Adds a thin amber accent bar on the left */
  accent?: boolean;
}

/**
 * Reusable panel/card primitive. Bloomberg-style: tight padding, hairline border.
 */
export function Card({ title, subtitle, rightSlot, className, children, accent }: CardProps) {
  return (
    <section
      className={classNames(
        "nemt-panel relative overflow-hidden",
        className
      )}
    >
      {accent && (
        <span
          aria-hidden
          className="absolute left-0 top-0 bottom-0 w-[2px] nemt-amber-gradient"
        />
      )}
      {(title || rightSlot) && (
        <header className="flex items-center justify-between px-4 py-3 border-b nemt-divider">
          <div className="min-w-0">
            {title && (
              <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-300 truncate">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-[11px] text-slate-500 mt-0.5 truncate">{subtitle}</p>
            )}
          </div>
          {rightSlot && <div className="shrink-0 ml-3">{rightSlot}</div>}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}
