"use client";

import type { ReactNode } from "react";
import { PageHeader } from "../common";
import { StudioIcon, type StudioIconName } from "../icons";

export interface ScaffoldModule {
  icon: StudioIconName;
  title: string;
  description: string;
  status?: string;
}

interface ModuleScaffoldProps {
  eyebrow: string;
  title: string;
  description: string;
  icon: StudioIconName;
  modules: ScaffoldModule[];
  note: string;
  actions?: ReactNode;
  children?: ReactNode;
}

export default function ModuleScaffold({
  eyebrow,
  title,
  description,
  icon,
  modules,
  note,
  actions,
  children,
}: ModuleScaffoldProps) {
  return (
    <div className="ns-page">
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        actions={
          <>
            <span className="ns-scaffold-badge">UI FOUNDATION</span>
            {actions}
          </>
        }
      />

      <div className="ns-scaffold-hero">
        <span className="ns-scaffold-hero-icon">
          <StudioIcon name={icon} size={26} />
        </span>
        <div className="ns-scaffold-hero-copy">
          <span className="ns-scaffold-kicker">界面与路由已建立</span>
          <h2>模块结构已预留，服务接口尚未接入</h2>
          <p>{note}</p>
        </div>
        <span className="ns-scaffold-status">
          <span className="ns-status-dot ns-status-muted" />
          未接入
        </span>
      </div>

      <div className="ns-scaffold-grid">
        {modules.map((module) => (
          <article key={module.title} className="ns-card ns-scaffold-module">
            <span className="ns-scaffold-module-icon">
              <StudioIcon name={module.icon} size={19} />
            </span>
            <div>
              <div className="ns-scaffold-module-title">
                <h3>{module.title}</h3>
                <span className="ns-chip">{module.status ?? "未接入"}</span>
              </div>
              <p>{module.description}</p>
            </div>
          </article>
        ))}
      </div>

      {children}

      <div className="ns-scaffold-note">
        <StudioIcon name="info" size={15} />
        <p>
          本页面不展示虚构的策略绩效或运行状态。后端能力接入后，模块会以真实状态、加载态、空状态与错误态启用。
        </p>
      </div>
    </div>
  );
}
