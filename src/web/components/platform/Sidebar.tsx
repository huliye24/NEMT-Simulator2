/**
 * Copyright 2026 NEMT Lab
 *
 * 侧边导航组件
 */

import React from 'react';
import {
  Cpu,
  Container,
  Box,
  Monitor,
  Terminal,
  Database,
  Code,
  Play,
  TestTube,
  BarChart3,
  Wallet,
} from 'lucide-react';
import { useActiveView, useUIStore } from '../../stores';

const menuItems = [
  { id: 'strategies', icon: Cpu, label: '策略市场' },
  { id: 'execution', icon: Play, label: '策略执行' },
  { id: 'backtest', icon: BarChart3, label: '回测引擎' },
  { id: 'dualbuffer', icon: TestTube, label: '双缓冲检验' },
  { id: 'containers', icon: Container, label: '容器管理' },
  { id: 'capsules', icon: Box, label: '胶囊市场' },
  { id: 'position', icon: Wallet, label: '仓位管理' },
  { id: 'monitor', icon: Monitor, label: '监控面板' },
  { id: 'terminal', icon: Terminal, label: '终端' },
  { id: 'market', icon: Database, label: '数据市场' },
] as const;

export function Sidebar() {
  const activeView = useActiveView();
  const { setActiveView, sidebarCollapsed } = useUIStore();

  return (
    <nav style={{
      width: sidebarCollapsed ? '64px' : '220px',
      background: '#0f172a',
      borderRight: '1px solid #1e293b',
      padding: sidebarCollapsed ? '24px 0' : '24px 0',
      transition: 'width 0.2s'
    }}>
      {menuItems.map(item => {
        const Icon = item.icon;
        const isActive = activeView === item.id;

        return (
          <div
            key={item.id}
            onClick={() => setActiveView(item.id)}
            title={sidebarCollapsed ? item.label : undefined}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: sidebarCollapsed ? '12px 22px' : '12px 24px',
              cursor: 'pointer',
              background: isActive ? '#8b5cf620' : 'transparent',
              borderLeft: isActive ? '3px solid #8b5cf6' : '3px solid transparent',
              color: isActive ? '#a78bfa' : '#64748b',
              transition: 'all 0.2s',
              fontSize: '14px',
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start'
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = '#1e293b';
                e.currentTarget.style.color = '#94a3b8';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = '#64748b';
              }
            }}
          >
            <Icon size={18} />
            {!sidebarCollapsed && item.label}
          </div>
        );
      })}

      {/* 底部开发者区域 */}
      <div style={{
        marginTop: '24px',
        padding: sidebarCollapsed ? '16px 12px' : '16px',
        borderTop: '1px solid #1e293b'
      }}>
        <div style={{
          fontSize: '11px',
          color: '#475569',
          marginBottom: '8px',
          textTransform: 'uppercase',
          letterSpacing: '1px',
          display: sidebarCollapsed ? 'none' : 'block'
        }}>
          开发者
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 12px',
          background: '#1e293b',
          borderRadius: '8px',
          cursor: 'pointer',
          justifyContent: sidebarCollapsed ? 'center' : 'flex-start'
        }}>
          <Code size={16} style={{ color: '#8b5cf6' }} />
          {!sidebarCollapsed && <span style={{ fontSize: '13px', color: '#94a3b8' }}>SDK 文档</span>}
        </div>
      </div>
    </nav>
  );
}
