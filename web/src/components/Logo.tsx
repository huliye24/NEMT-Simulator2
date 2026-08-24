import Image from "next/image";
import Link from "next/link";

interface LogoProps {
  size?: number;
  withWordmark?: boolean;
  href?: string | null;
}

/**
 * NEMT brand mark. Uses the PNG asset copied to /public; the square
 * frame is the amber gradient block from the brand system.
 */
export function Logo({ size = 32, withWordmark = true, href = "/" }: LogoProps) {
  const wordmark = withWordmark && (
    <div className="flex flex-col leading-tight">
      <span className="text-base font-bold nemt-amber-text tracking-wider">NEMT</span>
      <span className="text-[9px] uppercase tracking-[0.18em] text-slate-500">
        Financial Intelligence
      </span>
    </div>
  );

  const body = (
    <div className="flex items-center gap-2.5">
      <div
        className="relative overflow-hidden rounded-md nemt-amber-glow ring-1 ring-amber-500/30"
        style={{ width: size, height: size }}
      >
        <Image
          src="/nemt-logo.png"
          alt="NEMT logo"
          width={size}
          height={size}
          className="object-cover w-full h-full"
          priority
        />
      </div>
      {wordmark}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="hover:opacity-90 transition-opacity">
        {body}
      </Link>
    );
  }
  return body;
}
