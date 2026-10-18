"use client";

import MarketPanel from "../market/MarketPanel";
import MusicPlayer from "../music/MusicPlayer";
import type { StudioPageProps } from "../types";
import styles from "./MarketsPage.module.css";

export default function MarketsPage({ data }: StudioPageProps) {
  return (
    <div className={styles.workspace}>
      <div className={styles.market}><MarketPanel data={data} variant="expanded" /></div>
      <aside className={styles.soundtrack} aria-label="市场音乐"><MusicPlayer compact split /></aside>
    </div>
  );
}
