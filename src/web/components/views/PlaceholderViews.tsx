/**
 * Copyright 2026 NEMT Lab
 *
 * Placeholder 视图组件
 */

import React from 'react';
import { Container, Box, Monitor, Terminal, Database, LucideIcon } from 'lucide-react';

interface PlaceholderViewProps {
  icon: LucideIcon;
  title: string;
  description?: string;
}

export function PlaceholderView({ icon: Icon, title, description }: PlaceholderViewProps) {
  return (
    <div style={{ textAlign: 'center', padding: '80px' }}>
      <Icon size={64} style={{ color: '#334155', marginBottom: '16px' }} />
      <h3 style={{ margin: '0 0 8px', color: '#64748b' }}>{title}</h3>
      <p style={{ color: '#475569' }}>{description || '即将推出...'}</p>
    </div>
  );
}

export function ContainersView() {
  return <PlaceholderView icon={Container} title="容器管理" />;
}

export function CapsulesView() {
  return <PlaceholderView icon={Box} title="胶囊市场" />;
}

export function MonitorView() {
  return <PlaceholderView icon={Monitor} title="监控面板" />;
}

export function TerminalView() {
  return <PlaceholderView icon={Terminal} title="终端" />;
}

export function MarketView() {
  return <PlaceholderView icon={Database} title="数据市场" />;
}
