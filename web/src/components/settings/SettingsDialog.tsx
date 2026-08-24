/**
 * Copyright 2026 NEMT Lab
 *
 * SettingsDialog - 设置弹窗组件
 */

import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';
import { SettingsPanel } from './SettingsPanel';

// ============================================
// 组件
// ============================================

export const SettingsDialog: React.FC = () => {
  const { settingsOpen, closeSettings, saveAndClose, discardChanges, hasUnsavedChanges } = useSettingsStore();

  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && settingsOpen) {
        closeSettings();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [settingsOpen, closeSettings]);

  if (!settingsOpen) return null;

  return (
    <div style={styles.overlay} onClick={closeSettings}>
      <div style={styles.dialog} onClick={(e) => e.stopPropagation()}>
        {/* 头部 */}
        <div style={styles.header}>
          <h2 style={styles.title}>设置</h2>
          <button style={styles.closeButton} onClick={closeSettings}>
            <X size={20} />
          </button>
        </div>

        {/* 内容 */}
        <div style={styles.content}>
          <SettingsPanel />
        </div>

        {/* 底部 */}
        <div style={styles.footer}>
          <button
            style={styles.resetButton}
            onClick={() => useSettingsStore.getState().resetSettings()}
          >
            重置默认
          </button>
          <div style={{ flex: 1 }} />
          <button style={styles.cancelButton} onClick={discardChanges}>
            取消
          </button>
          <button
            style={{
              ...styles.confirmButton,
              ...(hasUnsavedChanges ? styles.confirmButtonActive : {}),
            }}
            onClick={saveAndClose}
          >
            确认
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================
// 样式
// ============================================

const styles: { [key: string]: React.CSSProperties } = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.7)',
    backdropFilter: 'blur(4px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10000,
  },
  dialog: {
    width: '520px',
    maxHeight: '80vh',
    background: '#0f172a',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    boxShadow: '0 25px 60px rgba(0, 0, 0, 0.5)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 600,
    color: '#f1f5f9',
  },
  closeButton: {
    background: 'transparent',
    border: 'none',
    color: '#94a3b8',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'color 0.2s, background 0.2s',
  },
  content: {
    padding: '24px',
    overflowY: 'auto',
    flex: 1,
  },
  footer: {
    padding: '16px 24px',
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  resetButton: {
    padding: '8px 16px',
    borderRadius: '8px',
    border: '1px solid #475569',
    background: 'transparent',
    color: '#94a3b8',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'border-color 0.2s, color 0.2s',
  },
  cancelButton: {
    padding: '8px 20px',
    borderRadius: '8px',
    border: '1px solid #475569',
    background: 'transparent',
    color: '#94a3b8',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'border-color 0.2s, color 0.2s',
  },
  confirmButton: {
    padding: '8px 20px',
    borderRadius: '8px',
    border: 'none',
    background: '#475569',
    color: '#94a3b8',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  confirmButtonActive: {
    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
    color: '#fff',
    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.3)',
  },
};
