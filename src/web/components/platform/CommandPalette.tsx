/**
 * Copyright 2026 NEMT Lab
 *
 * 命令面板组件
 */

import React, { useEffect, useState } from 'react';
import {
  Search,
  Cpu,
  Container,
  Box,
  Monitor,
  Terminal,
  Database,
  Plus
} from 'lucide-react';
import { useUIStore, useStrategyStore } from '../../stores';

interface Command {
  id: string;
  label: string;
  icon: React.ElementType;
  action: () => void;
}

export function CommandPalette() {
  const { commandPaletteOpen, toggleCommandPalette, setActiveView } = useUIStore();
  const addStrategy = useStrategyStore(state => state.addStrategy);
  const [query, setQuery] = useState('');

  const commands: Command[] = [
    { id: 'strategies', label: '策略市场', icon: Cpu, action: () => setActiveView('strategies') },
    { id: 'containers', label: '容器管理', icon: Container, action: () => setActiveView('containers') },
    { id: 'capsules', label: '胶囊市场', icon: Box, action: () => setActiveView('capsules') },
    { id: 'monitor', label: '监控面板', icon: Monitor, action: () => setActiveView('monitor') },
    { id: 'terminal', label: '终端', icon: Terminal, action: () => setActiveView('terminal') },
    { id: 'market', label: '数据市场', icon: Database, action: () => setActiveView('market') },
    {
      id: 'new-strategy',
      label: '新建策略',
      icon: Plus,
      action: () => {
        addStrategy({
          name: '新策略',
          author: 'User',
          description: '这是一个新创建的策略',
          version: '1.0.0',
          status: 'draft',
          metrics: { totalTrades: 0, winRate: 0, totalPnL: 0, sharpeRatio: 0 },
          tags: ['新策略']
        });
      }
    },
  ];

  const filteredCommands = commands.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery('');
    }
  }, [commandPaletteOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && commandPaletteOpen) {
        toggleCommandPalette();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, toggleCommandPalette]);

  if (!commandPaletteOpen) return null;

  const Icon = (props: { size: number; style?: React.CSSProperties }) => null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.7)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '15vh',
        zIndex: 1000
      }}
      onClick={toggleCommandPalette}
    >
      <div
        style={{
          width: '560px',
          background: '#1e293b',
          borderRadius: '16px',
          border: '1px solid #334155',
          overflow: 'hidden',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 搜索框 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '16px 20px',
          borderBottom: '1px solid #334155'
        }}>
          <Search size={20} style={{ color: '#64748b' }} />
          <input
            type="text"
            placeholder="输入命令或搜索..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#e2e8f0',
              fontSize: '16px'
            }}
          />
          <button
            onClick={toggleCommandPalette}
            style={{
              background: '#334155',
              border: 'none',
              borderRadius: '6px',
              padding: '4px 8px',
              color: '#94a3b8',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            ESC
          </button>
        </div>

        {/* 命令列表 */}
        <div style={{ maxHeight: '400px', overflowY: 'auto', padding: '8px' }}>
          {filteredCommands.map(cmd => {
            const IconComponent = cmd.icon;
            return (
              <div
                key={cmd.id}
                onClick={() => {
                  cmd.action();
                  toggleCommandPalette();
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'background 0.15s'
                }}
                onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.background = '#334155'}
                onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.background = 'transparent'}
              >
                <IconComponent size={18} style={{ color: '#8b5cf6' }} />
                <span style={{ color: '#e2e8f0', fontSize: '14px' }}>{cmd.label}</span>
              </div>
            );
          })}

          {filteredCommands.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: '32px',
              color: '#64748b'
            }}>
              未找到匹配的命令
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
