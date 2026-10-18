"use client";

import type { TradingData } from "../../useTradingData";
import { StatusDot } from "../common";
import { StudioIcon } from "../icons";

export default function ExecutionSummary({ data }: { data: TradingData }) {
  return (
    <section className="ns-card ns-exec-summary" aria-label="Execution status">
      <div className="ns-exec-summary-item">
        <span className="ns-exec-summary-icon">
          <StudioIcon name="play" size={16} />
        </span>
        <div>
          <span className="ns-exec-summary-label">Execution Service</span>
          <strong className="ns-exec-summary-value is-muted">
            <StatusDot tone="muted" />
            Not Connected
          </strong>
          <p>自动执行 API 尚未接入</p>
        </div>
      </div>
      <div className="ns-exec-summary-item">
        <span className="ns-exec-summary-icon">
          <StudioIcon name="strategies" size={16} />
        </span>
        <div>
          <span className="ns-exec-summary-label">Active Runs</span>
          <strong className="ns-exec-summary-value">0</strong>
          <p>当前没有运行中的实例</p>
        </div>
      </div>
      <div className="ns-exec-summary-item">
        <span className="ns-exec-summary-icon">
          <StudioIcon name="shield" size={16} />
        </span>
        <div>
          <span className="ns-exec-summary-label">Risk Control</span>
          <strong className="ns-exec-summary-value is-warn">
            <StatusDot tone="warn" />
            Unknown
          </strong>
          <p>
            执行风控未接入
            {data.system?.risk.pause_new_orders ? " · 服务端新订单已暂停" : ""}
          </p>
        </div>
      </div>
    </section>
  );
}
