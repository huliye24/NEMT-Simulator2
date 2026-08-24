/**
 * Copyright 2026 NEMT Lab
 *
 * 自定义窗口控制按钮组件
 * 用于无边框窗口
 */

import React, { useState, useEffect } from 'react';
import { Minus, Square, X, Maximize2 } from 'lucide-react';

// Electron 特有的 CSS 属性
interface ElectronStyle {
  WebkitAppRegion?: 'drag' | 'no-drag' | 'none';
}

type WindowStyle = React.CSSProperties & ElectronStyle;

export function WindowControls() {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    // 获取初始状态
    window.electron?.window.isMaximized().then(setIsMaximized);

    // 监听最大化状态变化
    const unsubscribe = window.electron?.window?.onMaximizeChange?.((maximized: boolean) => {
      setIsMaximized(maximized);
    });

    return () => {
      unsubscribe?.();
    };
  }, []);

  const handleMinimize = () => {
    window.electron?.window.minimize();
  };

  const handleMaximize = () => {
    window.electron?.window.maximize();
  };

  const handleClose = () => {
    window.electron?.window.close();
  };

  const headerStyle: WindowStyle = {
    height: '36px',
    background: '#0f172a',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 16px',
    WebkitAppRegion: 'drag',
    userSelect: 'none',
    borderBottom: '1px solid #1e293b',
  };

  const titleStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    fontSize: '14px',
    fontWeight: '600',
    color: '#e2e8f0',
  };

  const controlsStyle: WindowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    WebkitAppRegion: 'no-drag',
  };

  const buttonStyle: React.CSSProperties = {
    width: '36px',
    height: '28px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'transparent',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    color: '#94a3b8',
    transition: 'all 0.15s',
  };

  return (
    <div style={headerStyle}>
      {/* Logo 和标题 */}
      <div style={titleStyle}>
        <div style={{
          width: '20px',
          height: '20px',
          borderRadius: '4px',
          background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <span style={{ fontSize: '10px', color: '#fff' }}>N</span>
        </div>
        <span>NEMT Simulator</span>
      </div>

      {/* 窗口控制按钮 */}
      <div style={controlsStyle}>
        {/* 最小化 */}
        <button
          onClick={handleMinimize}
          style={buttonStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#1e293b';
            e.currentTarget.style.color = '#e2e8f0';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = '#94a3b8';
          }}
          title="最小化"
        >
          <Minus size={14} />
        </button>

        {/* 最大化/还原 */}
        <button
          onClick={handleMaximize}
          style={buttonStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#1e293b';
            e.currentTarget.style.color = '#e2e8f0';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = '#94a3b8';
          }}
          title={isMaximized ? '还原' : '最大化'}
        >
          {isMaximized ? <Square size={12} /> : <Maximize2 size={14} />}
        </button>

        {/* 关闭 */}
        <button
          onClick={handleClose}
          style={buttonStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#ef4444';
            e.currentTarget.style.color = '#fff';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = '#94a3b8';
          }}
          title="关闭"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}
