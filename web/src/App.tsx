/**
 * Copyright 2026 NEMT Lab
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * NEMT Simulator - 主应用页面
 */

import React, { useState, useCallback, useEffect } from 'react';
import { 
  SpectrumChart, 
  EvolutionChart, 
  NoiseScanChart, 
  NonlinearScanChart,
  ResultSummary,
  ParameterDisplay
} from './components/Charts';
import { ParamSliderGroup, PresetSelector, ActionButtons } from './components/Controls';
import { NEMTSimulator, generateDemoData } from './utils/nemtCore';
import { NotionBoard } from './components/NotionBoard';
import { NotionConfig, DEFAULT_NOTION_CONFIG } from './types/notion';
import { 
  NEMTParams, 
  DEFAULT_PARAMS, 
  ExperimentResult,
  NoiseScanResult,
  NonlinearScanResult 
} from './types/nemt';
import { Activity, BarChart3, TrendingUp, Zap, Info, LayoutDashboard } from 'lucide-react';

type ExperimentMode = 'none' | 'single' | 'noise' | 'nonlinear';
type MainTab = 'simulator' | 'notion';

// 从 localStorage 加载 Notion 配置
const loadNotionConfig = (): NotionConfig => {
  try {
    const saved = localStorage.getItem('notion_config');
    if (saved) {
      return { ...DEFAULT_NOTION_CONFIG, ...JSON.parse(saved) };
    }
  } catch (e) {
    console.error('Failed to load Notion config:', e);
  }
  return DEFAULT_NOTION_CONFIG;
};

export const NEMTApp: React.FC = () => {
  // 参数状态
  const [params, setParams] = useState<NEMTParams>(DEFAULT_PARAMS);
  
  // 实验结果
  const [singleResult, setSingleResult] = useState<ExperimentResult | null>(null);
  const [noiseScanResult, setNoiseScanResult] = useState<NoiseScanResult | null>(null);
  const [nonlinearScanResult, setNonlinearScanResult] = useState<NonlinearScanResult | null>(null);
  
  // 运行状态
  const [isRunning, setIsRunning] = useState(false);
  const [experimentMode, setExperimentMode] = useState<ExperimentMode>('none');
  
  // 标签页
  const [activeTab, setActiveTab] = useState<'spectrum' | 'evolution' | 'analysis'>('spectrum');
  
  // 主标签页 (模拟器 / Notion 看板)
  const [mainTab, setMainTab] = useState<MainTab>('simulator');
  
  // Notion 配置
  const [notionConfig, setNotionConfig] = useState<NotionConfig>(loadNotionConfig);
  
  // 保存 Notion 配置到 localStorage
  useEffect(() => {
    localStorage.setItem('notion_config', JSON.stringify(notionConfig));
  }, [notionConfig]);

  // 参数更新
  const handleParamChange = useCallback((newParams: Partial<NEMTParams>) => {
    setParams(prev => ({ ...prev, ...newParams }));
  }, []);

  // 运行单次模拟
  const handleRun = useCallback(() => {
    setIsRunning(true);
    setExperimentMode('single');
    
    setTimeout(() => {
      try {
        const simulator = new NEMTSimulator(params);
        const data = generateDemoData(params.n);
        const result = simulator.runExperiment(data);
        setSingleResult(result);
      } catch (error) {
        console.error('Simulation error:', error);
      }
      setIsRunning(false);
    }, 100);
  }, [params]);

  // 运行噪声扫描
  const handleNoiseScan = useCallback(() => {
    setIsRunning(true);
    setExperimentMode('noise');
    
    setTimeout(() => {
      try {
        const simulator = new NEMTSimulator(params);
        const data = generateDemoData(params.n);
        const result = simulator.runNoiseScan(data);
        setNoiseScanResult(result);
      } catch (error) {
        console.error('Noise scan error:', error);
      }
      setIsRunning(false);
    }, 100);
  }, [params]);

  // 运行非线性扫描
  const handleNonlinearScan = useCallback(() => {
    setIsRunning(true);
    setExperimentMode('nonlinear');
    
    setTimeout(() => {
      try {
        const simulator = new NEMTSimulator(params);
        const data = generateDemoData(params.n);
        const result = simulator.runNonlinearScan(data);
        setNonlinearScanResult(result);
      } catch (error) {
        console.error('Nonlinear scan error:', error);
      }
      setIsRunning(false);
    }, 100);
  }, [params]);

  // 重置
  const handleReset = useCallback(() => {
    setParams(DEFAULT_PARAMS);
    setSingleResult(null);
    setNoiseScanResult(null);
    setNonlinearScanResult(null);
    setExperimentMode('none');
  }, []);

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      {/* 头部 */}
      <header style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        color: 'white',
        padding: '24px 32px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Activity size={36} color="#00d4ff" />
            <div>
              <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 600 }}>
                NEMT Simulator
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.8, fontSize: '14px' }}>
                非平衡市场理论模拟器 | Non-Equilibrium Market Theory
              </p>
            </div>
          </div>
          
          {/* 主导航标签 */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setMainTab('simulator')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                border: 'none',
                borderRadius: '8px',
                background: mainTab === 'simulator' ? '#00d4ff' : 'rgba(255,255,255,0.1)',
                color: mainTab === 'simulator' ? '#1a1a2e' : 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
            >
              <Activity size={16} />
              模拟器
            </button>
            <button
              onClick={() => setMainTab('notion')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                border: 'none',
                borderRadius: '8px',
                background: mainTab === 'notion' ? '#00d4ff' : 'rgba(255,255,255,0.1)',
                color: mainTab === 'notion' ? '#1a1a2e' : 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
            >
              <LayoutDashboard size={16} />
              Notion 看板
            </button>
          </div>
        </div>
      </header>

      <main style={{ padding: '24px 32px', maxWidth: '1600px', margin: '0 auto' }}>
        {/* Notion 看板标签页 */}
        {mainTab === 'notion' && (
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}>
            <NotionBoard 
              initialConfig={notionConfig}
              onTaskCreated={(task) => console.log('Task created:', task)}
              onTaskUpdated={(task) => console.log('Task updated:', task)}
              onTaskDeleted={(taskId) => console.log('Task deleted:', taskId)}
              onConfigChange={(config) => setNotionConfig(config)}
            />
          </div>
        )}

        {/* 模拟器标签页 */}
        {mainTab === 'simulator' && (
          <>
        {/* 核心指标卡片 */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <MetricCard 
            icon={<Activity size={20} />}
            title="核心模型"
            value="NLS方程"
            subtitle="i∂ψ/∂t + α∇²ψ + β|ψ|²ψ = η"
          />
          <MetricCard 
            icon={<BarChart3 size={20} />}
            title="谱宽指标"
            value={singleResult?.spectralWidth.toFixed(4) || '—'}
            subtitle={experimentMode === 'single' ? '市场相干性度量' : '运行单次模拟查看'}
          />
          <MetricCard 
            icon={<TrendingUp size={20} />}
            title="共振峰"
            value={singleResult?.resonance.numPeaks.toString() || '—'}
            subtitle={experimentMode === 'single' ? '市场周期信号' : '检测市场频率'}
          />
          <MetricCard 
            icon={<Zap size={20} />}
            title="数据点"
            value={params.n.toString()}
            subtitle={`演化 ${params.steps} 步`}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
          {/* 左侧控制面板 */}
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            height: 'fit-content'
          }}>
            <h3 style={{ margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Info size={18} />
              参数设置
            </h3>
            
            <PresetSelector onSelect={setParams} />
            
            <div style={{ marginTop: '20px' }}>
              <ParamSliderGroup params={params} onChange={handleParamChange} />
            </div>
            
            <ActionButtons
              onRun={handleRun}
              onNoiseScan={handleNoiseScan}
              onNonlinearScan={handleNonlinearScan}
              onReset={handleReset}
              isRunning={isRunning}
            />

            {/* 运行状态 */}
            {isRunning && (
              <div style={{
                marginTop: '20px',
                padding: '16px',
                background: '#e6f7ff',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  border: '3px solid #1890ff',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  margin: '0 auto 12px',
                  animation: 'spin 1s linear infinite'
                }} />
                <p style={{ margin: 0, color: '#1890ff' }}>模拟运行中...</p>
              </div>
            )}
          </div>

          {/* 右侧结果面板 */}
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
          }}>
            {/* 标签页 */}
            <div style={{ 
              display: 'flex', 
              gap: '8px', 
              marginBottom: '20px',
              borderBottom: '1px solid #f0f0f0'
            }}>
              {['spectrum', 'evolution', 'analysis'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  style={{
                    padding: '10px 20px',
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                    fontWeight: activeTab === tab ? 600 : 400,
                    color: activeTab === tab ? '#1890ff' : '#666',
                    borderBottom: activeTab === tab ? '2px solid #1890ff' : '2px solid transparent',
                    transition: 'all 0.2s'
                  }}
                >
                  {tab === 'spectrum' && '频谱分析'}
                  {tab === 'evolution' && '振幅演化'}
                  {tab === 'analysis' && '实验分析'}
                </button>
              ))}
            </div>

            {/* 单次模拟结果 */}
            {experimentMode === 'single' && singleResult && (
              <>
                {activeTab === 'spectrum' && (
                  <div>
                    <ResultSummary result={singleResult} />
                    <div style={{ marginTop: '24px' }}>
                      <SpectrumChart
                        freqs={singleResult.freqs}
                        spectrum={singleResult.spectrum}
                        peakFrequencies={singleResult.resonance.peakFrequencies}
                        title="频谱分析"
                      />
                    </div>
                    <div style={{ marginTop: '24px' }}>
                      <ParameterDisplay params={singleResult.params} />
                    </div>
                  </div>
                )}
                
                {activeTab === 'evolution' && singleResult.evolution && (
                  <EvolutionChart 
                    evolution={singleResult.evolution} 
                    title="振幅演化 (时间 → 空间)"
                  />
                )}
                
                {activeTab === 'analysis' && (
                  <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                    <p>在此处进行更深入的分析</p>
                    <p style={{ fontSize: '14px' }}>运行噪声扫描或非线性扫描查看更多结果</p>
                  </div>
                )}
              </>
            )}

            {/* 噪声扫描结果 */}
            {experimentMode === 'noise' && noiseScanResult && (
              <div>
                <h3 style={{ margin: '0 0 20px' }}>噪声扫描实验</h3>
                <p style={{ color: '#666', marginBottom: '20px' }}>
                  观察不同噪声水平下的谱结构响应。低噪声产生清晰谱结构，高噪声可能导致相变。
                </p>
                <NoiseScanChart results={noiseScanResult} />
                
                {/* 每个噪声水平的频谱 */}
                <h4 style={{ marginTop: '32px' }}>各噪声水平频谱对比</h4>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                  gap: '16px'
                }}>
                  {noiseScanResult.results.map((result, idx) => (
                    <div key={idx} style={{ 
                      border: '1px solid #f0f0f0',
                      borderRadius: '8px',
                      padding: '12px'
                    }}>
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        marginBottom: '8px'
                      }}>
                        <span style={{ fontWeight: 500 }}>η = {result.params.noiseLevel}</span>
                        <span style={{ color: '#666' }}>谱宽: {result.spectralWidth.toFixed(4)}</span>
                      </div>
                      <SpectrumChart
                        freqs={result.freqs}
                        spectrum={result.spectrum}
                        title=""
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 非线性扫描结果 */}
            {experimentMode === 'nonlinear' && nonlinearScanResult && (
              <div>
                <h3 style={{ margin: '0 0 20px' }}>非线性扫描实验</h3>
                <p style={{ color: '#666', marginBottom: '20px' }}>
                  研究非线性效应（情绪/杠杆/羊群效应对市场的影响）。β增大可能出现孤子结构。
                </p>
                <NonlinearScanChart results={nonlinearScanResult} />
                
                {/* 每个β值的频谱 */}
                <h4 style={{ marginTop: '32px' }}>各非线性强度频谱对比</h4>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                  gap: '16px'
                }}>
                  {nonlinearScanResult.results.map((result, idx) => (
                    <div key={idx} style={{ 
                      border: '1px solid #f0f0f0',
                      borderRadius: '8px',
                      padding: '12px'
                    }}>
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        marginBottom: '8px'
                      }}>
                        <span style={{ fontWeight: 500 }}>β = {result.params.beta}</span>
                        <span style={{ color: '#666' }}>谱宽: {result.spectralWidth.toFixed(4)}</span>
                      </div>
                      <SpectrumChart
                        freqs={result.freqs}
                        spectrum={result.spectrum}
                        title=""
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 无结果状态 */}
            {experimentMode === 'none' && (
              <div style={{ 
                padding: '80px 40px', 
                textAlign: 'center',
                background: '#fafafa',
                borderRadius: '8px'
              }}>
                <Activity size={64} color="#ccc" style={{ marginBottom: '16px' }} />
                <h3 style={{ margin: '0 0 8px', color: '#666' }}>开始模拟</h3>
                <p style={{ margin: 0, color: '#999' }}>
                  调整参数后点击"运行模拟"查看结果
                </p>
              </div>
            )}
          </div>
        </div>

        {/* 数学模型说明 */}
        <div style={{
          marginTop: '24px',
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <h3 style={{ margin: '0 0 16px' }}>数学模型</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
            <div>
              <h4 style={{ color: '#1890ff', margin: '0 0 8px' }}>NLS方程</h4>
              <code style={{ 
                display: 'block', 
                padding: '12px', 
                background: '#f5f5f5', 
                borderRadius: '6px',
                fontFamily: 'monospace'
              }}>
                i∂ψ/∂t + α∂²ψ/∂x² + β|ψ|²ψ = η
              </code>
            </div>
            <div>
              <h4 style={{ color: '#52c41a', margin: '0 0 8px' }}>参数说明</h4>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#666' }}>
                <li><strong>ψ (psi)</strong>: 市场状态复振幅</li>
                <li><strong>α (alpha)</strong>: 扩散系数，流动性指标</li>
                <li><strong>β (beta)</strong>: 非线性强度，情绪效应</li>
                <li><strong>η (eta)</strong>: 噪声项，外部扰动</li>
              </ul>
            </div>
            <div>
              <h4 style={{ color: '#722ed1', margin: '0 0 8px' }}>核心指标</h4>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#666' }}>
                <li><strong>谱宽</strong>: 市场相干性度量，越小越稳定</li>
                <li><strong>共振峰</strong>: 周期性市场信号</li>
                <li><strong>平均频率</strong>: 市场主导振荡频率</li>
              </ul>
            </div>
          </div>
        </div>
          </>
        )}
      </main>

      {/* 动画样式 */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

// 指标卡片组件
interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  subtitle: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ icon, title, value, subtitle }) => (
  <div style={{
    background: 'white',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
      <div style={{ color: '#1890ff' }}>{icon}</div>
      <span style={{ color: '#666', fontSize: '14px' }}>{title}</span>
    </div>
    <div style={{ fontSize: '28px', fontWeight: 700, color: '#1a1a2e' }}>{value}</div>
    <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>{subtitle}</div>
  </div>
);

export default NEMTApp;
