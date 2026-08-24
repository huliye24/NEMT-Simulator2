/**
 * Copyright 2026 NEMT Lab
 *
 * 平台头部组件
 */

import React from 'react';
import {
  Container,
  Settings,
  Search
} from 'lucide-react';
import { usePlatformOverview, useUIStore } from '../../stores';

export function PlatformHeader() {
  const {
    runningStrategies,
    totalInstances,
    totalTrades
  } = usePlatformOverview();

  const toggleCommandPalette = useUIStore(state => state.toggleCommandPalette);

  return (
    <header style={{
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      borderBottom: '1px solid #334155',
      padding: '20px 32px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Logo 区域 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Container size={28} color="#fff" />
          </div>
          <div>
            <h1 style={{
              margin: 0,
              fontSize: '24px',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #a78bfa 0%, #818cf8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              NEMT Platform
            </h1>
            <p style={{
              margin: '2px 0 0',
              fontSize: '13px',
              color: '#94a3b8'
            }}>
              策略容器平台 | Strategy Container Platform
            </p>
          </div>
        </div>

        {/* 右侧功能区 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          {/* 平台统计 */}
          <div style={{ display: 'flex', gap: '24px' }}>
            {[
              { label: '在线策略', value: runningStrategies.toString(), color: '#10b981' },
              { label: '容器实例', value: totalInstances.toString(), color: '#3b82f6' },
              { label: '今日交易', value: totalTrades.toLocaleString(), color: '#f59e0b' },
            ].map(stat => (
              <div key={stat.label} style={{ textAlign: 'center' }}>
                <div style={{
                  fontSize: '20px',
                  fontWeight: 'bold',
                  color: stat.color,
                  fontFamily: 'monospace'
                }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: '11px', color: '#64748b' }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* 命令面板按钮 */}
          <button
            onClick={toggleCommandPalette}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              border: '1px solid #475569',
              background: 'transparent',
              color: '#e2e8f0',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px'
            }}
          >
            <Search size={16} />
            <span style={{ opacity: 0.7 }}>⌘K</span>
          </button>

          {/* 设置按钮 */}
          <button style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: '1px solid #475569',
            background: 'transparent',
            color: '#e2e8f0',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px'
          }}>
            <Settings size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
