/**
 * Copyright 2026 NEMT Lab
 *
 * Tab 导航组件
 * 用于切换介绍、生成系统、演化引擎
 */

import React from 'react';
import { BookOpen, Cpu, Sparkles } from 'lucide-react';

export type TabId = 'intro' | 'generation' | 'evolution';

interface TabNavigationProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: 'intro', label: '介绍', icon: BookOpen },
  { id: 'generation', label: '生成系统', icon: Cpu },
  { id: 'evolution', label: '演化引擎', icon: Sparkles },
];

export function TabNavigation({ activeTab, onTabChange }: TabNavigationProps) {
  React.useEffect(() => {
    // 键盘快捷键支持
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        const num = parseInt(e.key);
        if (num >= 1 && num <= 3) {
          e.preventDefault();
          onTabChange(tabs[num - 1].id);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onTabChange]);

  return (
    <div style={{
      height: '48px',
      background: '#1e293b',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      gap: '8px',
      borderBottom: '1px solid #334155',
    }}>
      {tabs.map((tab, index) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <React.Fragment key={tab.id}>
            {index > 0 && (
              <div style={{
                width: '1px',
                height: '24px',
                background: '#334155',
                margin: '0 8px',
              }} />
            )}
            <button
              onClick={() => onTabChange(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                background: isActive ? '#8b5cf620' : 'transparent',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                color: isActive ? '#a78bfa' : '#94a3b8',
                fontSize: '14px',
                fontWeight: isActive ? '600' : '400',
                transition: 'all 0.2s',
                position: 'relative',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = '#334155';
                  e.currentTarget.style.color = '#e2e8f0';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = '#94a3b8';
                }
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
              {isActive && (
                <div style={{
                  position: 'absolute',
                  bottom: '-9px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '40px',
                  height: '2px',
                  background: '#8b5cf6',
                  borderRadius: '1px',
                }} />
              )}
            </button>
          </React.Fragment>
        );
      })}

      {/* 快捷键提示 */}
      <div style={{
        marginLeft: 'auto',
        display: 'flex',
        gap: '12px',
        fontSize: '11px',
        color: '#475569',
      }}>
        <span>Ctrl+1/2/3 切换</span>
      </div>
    </div>
  );
}
