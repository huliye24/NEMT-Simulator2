"use client";

import Image from "next/image";
import { cn, fmtPct, fmtPrice } from "@/lib/trade/format";
import { Skeleton } from "../common";
import type { StudioPageProps } from "../types";
import cyclistArtwork from "../assets/emergentix-cyclist-v1.png";
import styles from "./OverviewPage.module.css";

export default function OverviewPage({ data }: StudioPageProps) {
  const change = Number(data.ticker?.price_change_percent ?? 0);

  return (
    <div className={cn("ns-page ns-overview", styles.page)}>
      <section className={styles.hero} aria-label="Portfolio briefing">
        <div className={styles.heroCopy}>
          <div className={styles.quoteBlock}>
            <div className={styles.marketSymbol}>BTC <span>/ USDT</span></div>
            <div className={styles.liveQuote}>
              <strong>{data.ticker ? fmtPrice(data.ticker.last_price) : <Skeleton className="ns-skeleton-kpi" />}</strong>
              {data.ticker ? <span className={change >= 0 ? styles.quoteUp : styles.quoteDown}>{fmtPct(data.ticker.price_change_percent)}</span> : null}
            </div>
          </div>
        </div>
        <div className={styles.artPanel} aria-label="Emergentix urban cyclist illustration">
          <div className={styles.artwork} aria-hidden="true">
            <Image
              src={cyclistArtwork}
              alt=""
              fill
              priority
              sizes="(max-width: 980px) 100vw, 58vw"
            />
          </div>
        </div>
      </section>

    </div>
  );
}


