/**
 * Copyright 2026 NEMT Lab
 *
 * SettingsPanel - 设置面板组件
 */

import React from 'react';
import { useSettingsStore, Settings } from '../../stores/settingsStore';

// ============================================
// 图标组件
// ============================================

const SunIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="5" />
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
  </svg>
);

const MoonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

const GlobeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

const SlidersIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="4" y1="21" x2="4" y2="14" />
    <line x1="4" y1="10" x2="4" y2="3" />
    <line x1="12" y1="21" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12" y2="3" />
    <line x1="20" y1="21" x2="20" y2="16" />
    <line x1="20" y1="12" x2="20" y2="3" />
    <line x1="1" y1="14" x2="7" y2="14" />
    <line x1="9" y1="8" x2="15" y2="8" />
    <line x1="17" y1="16" x2="23" y2="16" />
  </svg>
);

const CodeIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
);

const BellIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);

const KeyboardIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="4" width="20" height="16" rx="2" ry="2" />
    <line x1="6" y1="8" x2="6" y2="8" />
    <line x1="10" y1="8" x2="10" y2="8" />
    <line x1="14" y1="8" x2="14" y2="8" />
    <line x1="18" y1="8" x2="18" y2="8" />
    <line x1="8" y1="12" x2="8" y2="12" />
    <line x1="12" y1="12" x2="12" y2="12" />
    <line x1="16" y1="12" x2="16" y2="12" />
    <line x1="7" y1="16" x2="17" y2="16" />
  </svg>
);

const LinkIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
);

const BugIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="8" y="6" width="8" height="14" rx="4" />
    <path d="M19 8l-3 2" />
    <path d="M5 8l3 2" />
    <path d="M19 16l-3-2" />
    <path d="M5 16l3-2" />
    <line x1="12" y1="6" x2="12" y2="2" />
    <line x1="12" y1="22" x2="12" y2="20" />
  </svg>
);

// ============================================
// 子组件
// ============================================

interface SelectFieldProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

const SelectField: React.FC<SelectFieldProps> = ({ label, value, options, onChange }) => (
  <div style={styles.field}>
    <label style={styles.label}>{label}</label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={styles.select}
    >
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  </div>
);

interface NumberFieldProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}

const NumberField: React.FC<NumberFieldProps> = ({ label, value, min = 0, max, step = 1, onChange }) => (
  <div style={styles.field}>
    <label style={styles.label}>{label}</label>
    <input
      type="number"
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={(e) => onChange(Number(e.target.value))}
      style={styles.numberInput}
    />
  </div>
);

interface TextFieldProps {
  label: string;
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}

const TextField: React.FC<TextFieldProps> = ({ label, value, placeholder, onChange }) => (
  <div style={styles.field}>
    <label style={styles.label}>{label}</label>
    <input
      type="text"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      style={styles.textInput}
    />
  </div>
);

interface SwitchFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

const SwitchField: React.FC<SwitchFieldProps> = ({ label, description, checked, onChange }) => (
  <div style={styles.switchField}>
    <div style={styles.switchInfo}>
      <span style={styles.label}>{label}</span>
      {description && <span style={styles.description}>{description}</span>}
    </div>
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      style={{
        ...styles.switch,
        background: checked ? '#22c55e' : '#475569',
      }}
    >
      <span style={{
        ...styles.switchThumb,
        transform: checked ? 'translateX(16px)' : 'translateX(0)',
      }} />
    </button>
  </div>
);

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ title, icon, children }) => (
  <div style={styles.section}>
    <div style={styles.sectionHeader}>
      {icon}
      <span style={styles.sectionTitle}>{title}</span>
    </div>
    <div style={styles.sectionContent}>
      {children}
    </div>
  </div>
);

// ============================================
// 主组件
// ============================================

export const SettingsPanel: React.FC = () => {
  const {
    pendingSettings,
    updateSettings,
  } = useSettingsStore();

  // 使用临时设置
  const settings = pendingSettings || {
    theme: 'dark',
    language: 'zh-CN',
    defaultContractMultiplier: 1,
    slippageBps: 0,
    gatewayUrl: 'http://localhost:8080',
    debugMode: false,
    shortcutsHint: true,
    notifications: true,
  };

  return (
    <div style={styles.container}>
      {/* 通用设置 */}
      <Section title="通用" icon={<SunIcon />}>
        <SelectField
          label="主题"
          value={settings.theme}
          options={[
            { value: 'dark', label: '深色' },
            { value: 'light', label: '浅色' },
            { value: 'system', label: '跟随系统' },
          ]}
          onChange={(value) => updateSettings({ theme: value as Settings['theme'] })}
        />
        <SelectField
          label="语言"
          value={settings.language}
          options={[
            { value: 'zh-CN', label: '中文' },
            { value: 'en-US', label: 'English' },
          ]}
          onChange={(value) => updateSettings({ language: value as Settings['language'] })}
        />
      </Section>

      {/* 交易设置 */}
      <Section title="交易" icon={<SlidersIcon />}>
        <NumberField
          label="默认合约乘数"
          value={settings.defaultContractMultiplier}
          min={1}
          max={1000}
          onChange={(value) => updateSettings({ defaultContractMultiplier: value })}
        />
        <NumberField
          label="滑点 (bp)"
          value={settings.slippageBps}
          min={0}
          max={1000}
          onChange={(value) => updateSettings({ slippageBps: value })}
        />
      </Section>

      {/* 系统设置 */}
      <Section title="系统" icon={<CodeIcon />}>
        <TextField
          label="Gateway 地址"
          value={settings.gatewayUrl}
          placeholder="http://localhost:8080"
          onChange={(value) => updateSettings({ gatewayUrl: value })}
        />
        <SwitchField
          label="调试模式"
          description="开启后显示详细日志"
          checked={settings.debugMode}
          onChange={(checked) => updateSettings({ debugMode: checked })}
        />
        <SwitchField
          label="快捷键提示"
          description="显示键盘快捷键提示"
          checked={settings.shortcutsHint}
          onChange={(checked) => updateSettings({ shortcutsHint: checked })}
        />
        <SwitchField
          label="通知"
          description="开仓/平仓/风控通知"
          checked={settings.notifications}
          onChange={(checked) => updateSettings({ notifications: checked })}
        />
      </Section>
    </div>
  );
};

// ============================================
// 样式
// ============================================

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    padding: '8px 0',
  },
  section: {
    borderBottom: '1px solid #334155',
    paddingBottom: '20px',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '16px',
    color: '#94a3b8',
  },
  sectionTitle: {
    fontSize: '14px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  sectionContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '14px',
    fontWeight: 500,
    color: '#e2e8f0',
  },
  description: {
    fontSize: '12px',
    color: '#64748b',
    marginTop: '2px',
  },
  select: {
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid #334155',
    background: '#1e293b',
    color: '#e2e8f0',
    fontSize: '14px',
    cursor: 'pointer',
    outline: 'none',
  },
  numberInput: {
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid #334155',
    background: '#1e293b',
    color: '#e2e8f0',
    fontSize: '14px',
    outline: 'none',
    width: '120px',
  },
  textInput: {
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid #334155',
    background: '#1e293b',
    color: '#e2e8f0',
    fontSize: '14px',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
  },
  switchField: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  switch: {
    position: 'relative',
    width: '40px',
    height: '24px',
    borderRadius: '12px',
    border: 'none',
    cursor: 'pointer',
    transition: 'background 0.2s',
    padding: 0,
  },
  switchThumb: {
    position: 'absolute',
    top: '2px',
    left: '2px',
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    background: '#fff',
    transition: 'transform 0.2s',
  },
};
