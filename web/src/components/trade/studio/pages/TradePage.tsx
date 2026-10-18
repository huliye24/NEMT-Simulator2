"use client";

import TradingWorkbench from "./TradingWorkbench";
import type { StudioPageProps } from "../types";

export default function TradePage(props: StudioPageProps) {
  return (
    <TradingWorkbench
      {...props}
      eyebrow="WORKSPACE / SPOT TRADING"
      title="现货交易"
      description="BTC/USDT 现货执行监控。人工下单入口已关闭，策略执行产生的订单与成交在此同步。"
    />
  );
}
