/**
 * NEMT参数控制组件
 */

import React from 'react';
import { NEMTParams, PRESET_PARAMS } from '../types/nemt';

interface ParamSliderProps {
  label: string;
  name: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (name: string, value: number) => void;
  unit?: string;
  description?: string;
}

export const ParamSlider: React.FC<ParamSliderProps> = ({
  label,
  name,
  value,
  min,
  max,
  step,
  onChange,
  unit = '',
  description
}) => {
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <label style={{ fontWeight: 500 }}>{label}</label>
        <span style={{ 
          background: '#e6f7ff', 
          padding: '2px 8px', 
          borderRadius: '4px',
          fontFamily: 'monospace'
        }}>
          {value.toFixed(step < 0.1 ? 3 : 2)} {unit}
        </span>
      </div>
      <input
        type="range"
        name={name}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(name, parseFloat(e.target.value))}
        style={{ width: '100%', cursor: 'pointer' }}
      />
      {description && (
        <div style={{ fontSize: '11px', color: '#888', marginTop: '2px' }}>
          {description}
        </div>
      )}
    </div>
  );
};

interface ParamSliderGroupProps {
  params: NEMTParams;
  onChange: (params: Partial<NEMTParams>) => void;
}

export const ParamSliderGroup: React.FC<ParamSliderGroupProps> = ({ params, onChange }) => {
  const handleChange = (name: string, value: number) => {
    onChange({ [name]: value });
  };

  return (
    <div style={{ display: 'grid', gap: '8px' }}>
      <ParamSlider
        label="α (扩散系数)"
        name="alpha"
        value={params.alpha}
        min={0.01}
        max={1}
        step={0.01}
        onChange={handleChange}
        description="市场流动性指标，越大表示扩散越快"
      />
      <ParamSlider
        label="β (非线性强度)"
        name="beta"
        value={params.beta}
        min={0.1}
        max={20}
        step={0.1}
        onChange={handleChange}
        description="情绪/杠杆效应强度，越大表示非线性越强"
      />
      <ParamSlider
        label="η (噪声水平)"
        name="noiseLevel"
        value={params.noiseLevel}
        min={0}
        max={2}
        step={0.01}
        onChange={handleChange}
        description="外部扰动强度，模拟随机交易"
      />
      <ParamSlider
        label="演化步数"
        name="steps"
        value={params.steps}
        min={50}
        max={500}
        step={10}
        onChange={handleChange}
        description="模拟时间越长，结果越稳定"
      />
      <ParamSlider
        label="数据点数"
        name="n"
        value={params.n}
        min={64}
        max={512}
        step={64}
        onChange={handleChange}
        description="价格序列长度，必须是2的幂次"
      />
    </div>
  );
};

interface PresetSelectorProps {
  onSelect: (params: NEMTParams) => void;
}

export const PresetSelector: React.FC<PresetSelectorProps> = ({ onSelect }) => {
  return (
    <div style={{ marginBottom: '16px' }}>
      <label style={{ display: 'block', fontWeight: 500, marginBottom: '8px' }}>
        预设场景
      </label>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {PRESET_PARAMS.map((preset) => (
          <button
            key={preset.name}
            onClick={() => onSelect(preset.params)}
            style={{
              padding: '8px 16px',
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              background: '#fff',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#1890ff';
              e.currentTarget.style.background = '#e6f7ff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#d9d9d9';
              e.currentTarget.style.background = '#fff';
            }}
            title={preset.description}
          >
            {preset.name}
          </button>
        ))}
      </div>
    </div>
  );
};

interface ActionButtonsProps {
  onRun: () => void;
  onNoiseScan: () => void;
  onNonlinearScan: () => void;
  onReset: () => void;
  isRunning: boolean;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onRun,
  onNoiseScan,
  onNonlinearScan,
  onReset,
  isRunning
}) => {
  const buttonStyle: React.CSSProperties = {
    padding: '10px 20px',
    borderRadius: '6px',
    border: 'none',
    cursor: isRunning ? 'not-allowed' : 'pointer',
    fontWeight: 500,
    fontSize: '14px',
    transition: 'all 0.2s',
    opacity: isRunning ? 0.6 : 1
  };

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '20px' }}>
      <button
        onClick={onRun}
        disabled={isRunning}
        style={{
          ...buttonStyle,
          background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
          color: 'white'
        }}
      >
        {isRunning ? '运行中...' : '▶ 运行模拟'}
      </button>
      <button
        onClick={onNoiseScan}
        disabled={isRunning}
        style={{
          ...buttonStyle,
          background: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)',
          color: 'white'
        }}
      >
        噪声扫描
      </button>
      <button
        onClick={onNonlinearScan}
        disabled={isRunning}
        style={{
          ...buttonStyle,
          background: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)',
          color: 'white'
        }}
      >
        非线性扫描
      </button>
      <button
        onClick={onReset}
        disabled={isRunning}
        style={{
          ...buttonStyle,
          background: '#fff',
          color: '#666',
          border: '1px solid #d9d9d9'
        }}
      >
        重置参数
      </button>
    </div>
  );
};
