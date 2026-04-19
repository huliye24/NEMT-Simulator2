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
import { 
  NEMTParams, 
  DEFAULT_PARAMS, 
  ExperimentResult,
  NoiseScanResult,
  NonlinearScanResult,
  MarketPhase,
  PHASE_STRATEGIES,
  PhaseStrategy
} from './types/nemt';
import { Activity, BarChart3, TrendingUp, Zap, Info, LayoutDashboard, BookOpen, ActivitySquare, TrendingDown, Minus, AlertTriangle, CheckCircle, Clock, History, Play, Loader2, Terminal, ChevronDown, ChevronRight, X, RefreshCw, Globe } from 'lucide-react';
import { TheoryTab } from './components/TheoryTab';
import { KanbanBoard } from './components/KanbanBoard';
import { OnChainDashboard } from './components/OnChainDashboard';
import { getPipelineService, signalHistory, TradingSignal, PipelineLogEntry } from './services/nemtPipeline';
import { createExecutionFramework } from './services/executionService';
import { ExecutionCardComponent } from './components/ExecutionCard';
import { QuickAssessmentButton } from './components/QuickAssessmentButton';
import { TheoryDashboard } from './components/TheoryDashboard';
import { MarketPanel } from './components/MarketPanel';
import { NEMTDashboard } from './components/NEMTDashboard';

type ExperimentMode = 'none' | 'single' | 'noise' | 'nonlinear' | 'pipeline';
type MainTab = 'simulator' | 'dashboard' | 'kanban' | 'theory' | 'notion' | 'market' | 'nemt';

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
  
  // Pipeline 状态
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineLogs, setPipelineLogs] = useState<PipelineLogEntry[]>([]);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [pipelineSuccess, setPipelineSuccess] = useState(false);
  const [useRemoteMode, setUseRemoteMode] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  
  // 标签页
  const [activeTab, setActiveTab] = useState<'spectrum' | 'evolution' | 'analysis'>('spectrum');

  // 主标签页状态
  const [mainTab, setMainTab] = useState<MainTab>('simulator');

  // 相位状态
  const [currentPhase, setCurrentPhase] = useState<MarketPhase>(MarketPhase.PHASE_A_NOISE);
  const [phaseConfidence, setPhaseConfidence] = useState(0);
  const [signalHistoryData, setSignalHistoryData] = useState<TradingSignal[]>([]);
  
  // Pipeline服务
  const pipelineService = getPipelineService();

  // 执行框架
  const [executionFramework] = useState(() => createExecutionFramework());
  const [executionCard, setExecutionCard] = useState(executionFramework.getCard());

  // 初始化：检查服务器状态
  useEffect(() => {
    checkServerStatus();
  }, []);

  // 检查远程服务器状态
  const checkServerStatus = useCallback(async () => {
    const status = await pipelineService.checkServerStatus();
    if (status.available) {
      setUseRemoteMode(true);
      pipelineService.setUseRemote(true);
    } else {
      setUseRemoteMode(false);
      pipelineService.setUseRemote(false);
    }
  }, [pipelineService]);

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
        const data = generateDemoData(params.n);
        pipelineService.setParams(params);
        
        pipelineService.runPipeline(data, 'BTCUSDT').then(result => {
          if (result.success) {
            setSingleResult(result.experimentResult);
            setCurrentPhase(result.currentPhase);
            setPhaseConfidence(result.nemtSignals.phaseConfidence);
            setSignalHistoryData(signalHistory.getRecent(10));
          } else {
            console.error('Pipeline error:', result.error);
          }
        });
      } catch (error) {
        console.error('Simulation error:', error);
      }
      setIsRunning(false);
    }, 100);
  }, [params, pipelineService]);

  // 运行完整 Pipeline
  const handleRunFullPipeline = useCallback(async () => {
    setPipelineRunning(true);
    setPipelineError(null);
    setPipelineSuccess(false);
    setExperimentMode('pipeline');
    setShowLogs(true);

    try {
      const data = generateDemoData(params.n);
      pipelineService.setParams(params);

      const result = await pipelineService.runPipeline(data, 'BTCUSDT');

      // 更新日志
      setPipelineLogs(pipelineService.getLogs());

      if (result.success) {
        setPipelineSuccess(true);
        setSingleResult(result.experimentResult);
        setCurrentPhase(result.currentPhase);
        setPhaseConfidence(result.nemtSignals.phaseConfidence);
        setSignalHistoryData(signalHistory.getRecent(10));
        setActiveTab('spectrum');

        // 运行执行框架分析
        const prices = result.experimentResult?.spectrum ? 
          Array.from(result.experimentResult.spectrum).map((v: number, i: number) => i * 0.1 + v) : data;
        const dci = typeof result.nemtSignals.dci === 'number' 
          ? result.nemtSignals.dci 
          : 0.5;
        const vortexMaturity = 8;
        const spectralWidth = result.experimentResult?.spectralWidth || 0.02;
        const noiseLevel = 0.1;

        // 运行执行框架
        const macroScores = {
          macroScore: 7,
          onchainScore: 6,
          halvingPhase: 'main_rise' as const,
          monthsSinceHalving: 10,
          rtiScore: 5,
        };

        const card = executionFramework.runFullFramework(
          dci,
          vortexMaturity,
          result.currentPhase,
          spectralWidth,
          noiseLevel,
          macroScores,
          prices
        );

        setExecutionCard({ ...card });
        console.log('执行框架结果:', card);
      } else {
        setPipelineError(result.error || 'Pipeline 执行失败');
      }
    } catch (error) {
      setPipelineError(error instanceof Error ? error.message : 'Unknown error');
    }

    setPipelineRunning(false);
  }, [params, pipelineService, executionFramework]);

  // 清除 Pipeline 结果
  const handleClearPipeline = useCallback(() => {
    setExperimentMode('none');
    setPipelineLogs([]);
    setPipelineError(null);
    setPipelineSuccess(false);
    setShowLogs(false);
  }, []);

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
    handleClearPipeline();
  }, [handleClearPipeline]);

  // 切换远程模式
  const handleToggleRemoteMode = useCallback(async () => {
    if (useRemoteMode) {
      setUseRemoteMode(false);
      pipelineService.setUseRemote(false);
    } else {
      const status = await pipelineService.checkServerStatus();
      if (status.available) {
        setUseRemoteMode(true);
        pipelineService.setUseRemote(true);
      } else {
        setPipelineError(`API 服务器不可用: ${status.message}`);
        setShowLogs(true);
      }
    }
  }, [useRemoteMode, pipelineService]);

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
              onClick={() => setMainTab('dashboard')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                border: 'none',
                borderRadius: '8px',
                background: mainTab === 'dashboard' ? '#00d4ff' : 'rgba(255,255,255,0.1)',
                color: mainTab === 'dashboard' ? '#1a1a2e' : 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
            >
              <ActivitySquare size={16} />
              指标
            </button>
            <button
              onClick={() => setMainTab('kanban')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                border: 'none',
                borderRadius: '8px',
                background: mainTab === 'kanban' ? '#00d4ff' : 'rgba(255,255,255,0.1)',
                color: mainTab === 'kanban' ? '#1a1a2e' : 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
            >
              <LayoutDashboard size={16} />
              看板
            </button>
            <button
              onClick={() => setMainTab('theory')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                border: 'none',
                borderRadius: '8px',
                background: mainTab === 'theory' ? '#00d4ff' : 'rgba(255,255,255,0.1)',
                color: mainTab === 'theory' ? '#1a1a2e' : 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
            >
              <BookOpen size={16} />
              NEMT理论
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
              <Globe size={16} />
              Notion同步
            </button>
            <button
              onClick={() => setMainTab('market')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                border: 'none',
                borderRadius: '8px',
                background: mainTab === 'market' ? '#00d4ff' : 'rgba(255,255,255,0.1)',
                color: mainTab === 'market' ? '#1a1a2e' : 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
            >
              <BarChart3 size={16} />
              市场数据
            </button>
            <button
              onClick={() => setMainTab('nemt')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 20px',
                border: 'none',
                borderRadius: '8px',
                background: mainTab === 'nemt' ? '#10b981' : 'rgba(255,255,255,0.1)',
                color: mainTab === 'nemt' ? '#1a1a2e' : 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s'
              }}
            >
              <Activity size={16} />
              NEMT Core
            </button>
          </div>
        </div>
      </header>

      <main style={{ padding: '24px 32px', maxWidth: '1600px', margin: '0 auto' }}>
        {/* 指标 Dashboard 标签页 */}
        {mainTab === 'dashboard' && (
          <OnChainDashboard />
        )}

        {/* 看板标签页 */}
        {mainTab === 'kanban' && (
          <KanbanBoard
            title="NEMT 任务看板"
            accentColor="#00d4ff"
          />
        )}

        {/* NEMT理论标签页 */}
        {mainTab === 'theory' && (
          <TheoryTab />
        )}

        {/* Notion 理论中枢同步标签页 */}
        {mainTab === 'notion' && (
          <TheoryDashboard
            currentPhase={currentPhase}
            macroScore={5}
            onchainScore={5}
          />
        )}

        {/* 市场数据标签页 */}
        {mainTab === 'market' && (
          <MarketPanel defaultSymbol="BTCUSDT" />
        )}

        {/* NEMT Core 标签页 */}
        {mainTab === 'nemt' && (
          <NEMTDashboard symbol="BTCUSDT" />
        )}

        {/* 模拟器标签页 */}
        {mainTab === 'simulator' && (
          <>
            {/* Pipeline 状态栏 */}
            {experimentMode === 'pipeline' && (
              <PipelineStatusBar
                running={pipelineRunning}
                success={pipelineSuccess}
                error={pipelineError}
                logs={pipelineLogs}
                showLogs={showLogs}
                onToggleLogs={() => setShowLogs(!showLogs)}
                onClear={handleClearPipeline}
              />
            )}

            {/* 四相位状态 - 始终显示 */}
            <PhaseStatusDisplay currentPhase={currentPhase} confidence={phaseConfidence} />

            {/* 执行框架卡片 - Pipeline 成功后显示 */}
            {experimentMode === 'pipeline' && pipelineSuccess && (
              <ExecutionCardComponent card={executionCard} />
            )}

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
                subtitle={experimentMode === 'single' || experimentMode === 'pipeline' ? '市场相干性度量' : '运行模拟查看'}
              />
              <MetricCard 
                icon={<TrendingUp size={20} />}
                title="共振峰"
                value={singleResult?.resonance.numPeaks.toString() || '—'}
                subtitle={experimentMode === 'single' || experimentMode === 'pipeline' ? '市场周期信号' : '检测市场频率'}
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
            
            {/* Run Full Pipeline 按钮 */}
            <div style={{ marginTop: '20px' }}>
              <button
                onClick={handleRunFullPipeline}
                disabled={pipelineRunning}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 20px',
                  border: 'none',
                  borderRadius: '8px',
                  background: pipelineRunning 
                    ? '#d9d9d9' 
                    : 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)',
                  color: pipelineRunning ? '#999' : 'white',
                  fontSize: '15px',
                  fontWeight: 600,
                  cursor: pipelineRunning ? 'not-allowed' : 'pointer',
                  boxShadow: pipelineRunning ? 'none' : '0 4px 12px rgba(82, 196, 26, 0.3)',
                  transition: 'all 0.2s',
                  marginBottom: '12px'
                }}
              >
                {pipelineRunning ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    运行中...
                  </>
                ) : (
                  <>
                    <Play size={18} />
                    Run Full Pipeline
                  </>
                )}
              </button>

              {/* 模式切换 */}
              <div style={{ 
                display: 'flex', 
                alignItems: 'center',
                gap: '8px',
                padding: '10px 12px',
                background: '#f5f5f5',
                borderRadius: '8px',
                fontSize: '12px'
              }}>
                <Globe size={14} style={{ color: useRemoteMode ? '#52c41a' : '#999' }} />
                <span style={{ flex: 1, color: '#666' }}>
                  模式: {useRemoteMode ? '远程 (Python)' : '本地 (TypeScript)'}
                </span>
                <button
                  onClick={handleToggleRemoteMode}
                  style={{
                    padding: '4px 8px',
                    border: '1px solid #d9d9d9',
                    borderRadius: '4px',
                    background: 'white',
                    cursor: 'pointer',
                    fontSize: '11px',
                    color: '#666'
                  }}
                >
                  切换
                </button>
              </div>
            </div>

            <ActionButtons
              onRun={handleRun}
              onNoiseScan={handleNoiseScan}
              onNonlinearScan={handleNonlinearScan}
              onReset={handleReset}
              isRunning={isRunning}
            />

            {/* 快速市场评估 */}
            <QuickAssessmentButton />

            {/* 运行状态 */}
            {(isRunning || pipelineRunning) && (
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
                <p style={{ margin: 0, color: '#1890ff' }}>
                  {pipelineRunning ? 'Pipeline 运行中...' : '模拟运行中...'}
                </p>
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
            {/* Pipeline 日志面板 */}
            {experimentMode === 'pipeline' && showLogs && (
              <PipelineLogPanel 
                logs={pipelineLogs}
                success={pipelineSuccess}
                error={pipelineError}
                onClose={() => setShowLogs(false)}
              />
            )}

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

            {/* 单次模拟/Pipeline 结果 */}
            {(experimentMode === 'single' || experimentMode === 'pipeline') && singleResult && (
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
                  点击上方 "Run Full Pipeline" 或 "运行模拟" 查看结果
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

        {/* 信号历史面板 */}
        <div style={{ marginTop: '24px' }}>
          <SignalHistoryPanel signals={signalHistoryData} />
        </div>
          </>
        )}
      </main>

      {/* 动画样式 */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
};

// =====================
// Pipeline 状态栏组件
// =====================

interface PipelineStatusBarProps {
  running: boolean;
  success: boolean;
  error: string | null;
  logs: PipelineLogEntry[];
  showLogs: boolean;
  onToggleLogs: () => void;
  onClear: () => void;
}

const PipelineStatusBar: React.FC<PipelineStatusBarProps> = ({
  running,
  success,
  error,
  logs,
  showLogs,
  onToggleLogs,
  onClear
}) => {
  return (
    <div style={{
      marginBottom: '16px',
      borderRadius: '12px',
      overflow: 'hidden',
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
    }}>
      {/* 状态头 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '16px 20px',
        background: running ? '#e6f7ff' : success ? '#f6ffed' : error ? '#fff2f0' : '#fafafa',
        borderBottom: showLogs ? '1px solid #f0f0f0' : 'none'
      }}>
        {running ? (
          <Loader2 size={20} className="animate-spin" style={{ color: '#1890ff' }} />
        ) : success ? (
          <CheckCircle size={20} style={{ color: '#52c41a' }} />
        ) : error ? (
          <AlertTriangle size={20} style={{ color: '#ff4d4f' }} />
        ) : (
          <Play size={20} style={{ color: '#666' }} />
        )}
        
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, color: running ? '#1890ff' : success ? '#52c41a' : error ? '#ff4d4f' : '#666' }}>
            {running ? 'Pipeline 运行中...' : success ? 'Pipeline 执行成功!' : error ? 'Pipeline 执行失败' : 'Pipeline 就绪'}
          </div>
          <div style={{ fontSize: '12px', color: '#999', marginTop: '2px' }}>
            Notion → NEMT分析 → 信号生成 → 结果展示
          </div>
        </div>

        <button
          onClick={onToggleLogs}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
            background: 'white',
            cursor: 'pointer',
            fontSize: '12px',
            color: '#666'
          }}
        >
          <Terminal size={14} />
          {showLogs ? '隐藏日志' : '显示日志'}
          {showLogs ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>

        <button
          onClick={onClear}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
            background: 'white',
            cursor: 'pointer',
            fontSize: '12px',
            color: '#666'
          }}
        >
          <X size={14} />
          清除
        </button>
      </div>

      {/* 日志面板 */}
      {showLogs && (
        <div style={{
          background: '#1a1a2e',
          padding: '16px',
          maxHeight: '300px',
          overflowY: 'auto'
        }}>
          {logs.length === 0 ? (
            <div style={{ color: '#999', fontSize: '13px' }}>暂无日志</div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} style={{
                display: 'flex',
                gap: '12px',
                marginBottom: '8px',
                fontSize: '13px',
                fontFamily: 'monospace'
              }}>
                <span style={{ color: '#666', flexShrink: 0 }}>
                  {new Date(log.timestamp).toLocaleTimeString('zh-CN')}
                </span>
                <span style={{
                  color: log.level === 'SUCCESS' ? '#52c41a' : 
                         log.level === 'WARNING' ? '#faad14' :
                         log.level === 'ERROR' ? '#ff4d4f' : '#1890ff',
                  flexShrink: 0,
                  minWidth: '60px'
                }}>
                  [{log.level}]
                </span>
                <span style={{ color: '#fff' }}>
                  [{log.step}] {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// =====================
// Pipeline 日志面板组件
// =====================

interface PipelineLogPanelProps {
  logs: PipelineLogEntry[];
  success: boolean;
  error: string | null;
  onClose: () => void;
}

const PipelineLogPanel: React.FC<PipelineLogPanelProps> = ({
  logs,
  success,
  error,
  onClose
}) => {
  const logColors: Record<string, string> = {
    'INFO': '#1890ff',
    'SUCCESS': '#52c41a',
    'WARNING': '#faad14',
    'ERROR': '#ff4d4f',
  };

  return (
    <div style={{
      marginBottom: '20px',
      borderRadius: '8px',
      overflow: 'hidden',
      border: success ? '1px solid #52c41a' : error ? '1px solid #ff4d4f' : '1px solid #f0f0f0'
    }}>
      {/* 头部 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        background: success ? '#f6ffed' : error ? '#fff2f0' : '#f5f5f5',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Terminal size={16} />
          <span style={{ fontWeight: 500, fontSize: '14px' }}>
            执行日志
          </span>
          <span style={{
            padding: '2px 8px',
            borderRadius: '10px',
            background: '#f0f0f0',
            fontSize: '11px',
            color: '#666'
          }}>
            {logs.length} 条
          </span>
        </div>
        <button
          onClick={onClose}
          style={{
            padding: '4px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            color: '#999'
          }}
        >
          <X size={16} />
        </button>
      </div>

      {/* 日志内容 */}
      <div style={{
        background: '#1e1e2e',
        padding: '12px 16px',
        maxHeight: '200px',
        overflowY: 'auto',
        fontFamily: 'monospace',
        fontSize: '12px'
      }}>
        {logs.map((log, idx) => (
          <div key={idx} style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '6px',
            lineHeight: 1.5
          }}>
            <span style={{ color: '#666', flexShrink: 0 }}>
              {idx + 1}
            </span>
            <span style={{ color: logColors[log.level] || '#fff', flexShrink: 0 }}>
              {log.level}
            </span>
            <span style={{ color: '#8b949e' }}>
              [{log.step}]
            </span>
            <span style={{ color: '#c9d1d9' }}>
              {log.message}
            </span>
          </div>
        ))}
        
        {logs.length === 0 && (
          <div style={{ color: '#666' }}>暂无日志</div>
        )}
      </div>

      {/* 结果摘要 */}
      {success && !error && (
        <div style={{
          padding: '12px 16px',
          background: '#d9f7be',
          borderTop: '1px solid #95de64',
          fontSize: '13px',
          color: '#389e0d'
        }}>
          <CheckCircle size={14} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          完整流程执行成功！信号已生成，结果已回写。
        </div>
      )}
      
      {error && (
        <div style={{
          padding: '12px 16px',
          background: '#fff1f0',
          borderTop: '1px solid #ffccc7',
          fontSize: '13px',
          color: '#cf1322'
        }}>
          <AlertTriangle size={14} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          {error}
        </div>
      )}
    </div>
  );
};

// =====================
// 指标卡片组件
// =====================

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

// =====================
// 四相位状态组件
// =====================

interface MarketPhaseCardProps {
  phase: MarketPhase;
  strategy: PhaseStrategy;
  isActive: boolean;
  confidence: number;
}

const MarketPhaseCard: React.FC<MarketPhaseCardProps> = ({ phase, strategy, isActive, confidence }) => {
  const phaseColors: Record<MarketPhase, string> = {
    [MarketPhase.PHASE_A_NOISE]: '#8c8c8c',
    [MarketPhase.PHASE_B_VORTEX]: '#1890ff',
    [MarketPhase.PHASE_C_RESONANCE]: '#faad14',
    [MarketPhase.PHASE_D_TREND]: '#52c41a'
  };

  const phaseNames: Record<MarketPhase, string> = {
    [MarketPhase.PHASE_A_NOISE]: 'A',
    [MarketPhase.PHASE_B_VORTEX]: 'B',
    [MarketPhase.PHASE_C_RESONANCE]: 'C',
    [MarketPhase.PHASE_D_TREND]: 'D'
  };

  return (
    <div style={{
      padding: '16px',
      borderRadius: '12px',
      border: isActive ? `2px solid ${phaseColors[phase]}` : '1px solid #f0f0f0',
      background: isActive ? `${phaseColors[phase]}10` : 'white',
      transition: 'all 0.3s'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: phaseColors[phase],
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '20px',
          fontWeight: 700
        }}>
          {phaseNames[phase]}
        </div>
        {isActive && (
          <div style={{
            padding: '4px 12px',
            borderRadius: '12px',
            background: phaseColors[phase],
            color: 'white',
            fontSize: '12px',
            fontWeight: 500
          }}>
            {Math.round(confidence * 100)}%
          </div>
        )}
      </div>
      <h4 style={{ margin: '0 0 8px', color: '#1a1a2e' }}>{strategy.name}</h4>
      <p style={{ margin: '0 0 12px', fontSize: '13px', color: '#666' }}>{strategy.strategyText}</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
        <div>
          <span style={{ color: '#999' }}>仓位: </span>
          <span style={{ fontWeight: 600 }}>{Math.round(strategy.maxPosition * 100)}%</span>
        </div>
        <div>
          <span style={{ color: '#999' }}>杠杆: </span>
          <span style={{ fontWeight: 600 }}>≤{strategy.leverageAllowed}x</span>
        </div>
      </div>
    </div>
  );
};

const PhaseStatusDisplay: React.FC<{ currentPhase: MarketPhase; confidence: number }> = ({ currentPhase, confidence }) => {
  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      marginBottom: '24px'
    }}>
      <h3 style={{ margin: '0 0 20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <TrendingUp size={20} style={{ color: '#1890ff' }} />
        市场相位状态
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        {Object.entries(PHASE_STRATEGIES).map(([phase, strategy]) => (
          <MarketPhaseCard
            key={phase}
            phase={phase as MarketPhase}
            strategy={strategy}
            isActive={phase === currentPhase}
            confidence={phase === currentPhase ? confidence : 0}
          />
        ))}
      </div>
      <div style={{
        marginTop: '20px',
        padding: '16px',
        background: '#f5f5f5',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <AlertTriangle size={20} style={{ color: '#faad14' }} />
        <div>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>
            当前策略: {PHASE_STRATEGIES[currentPhase].strategyText}
          </div>
          <div style={{ fontSize: '13px', color: '#666' }}>
            关注: {PHASE_STRATEGIES[currentPhase].focusText} | 避免: {PHASE_STRATEGIES[currentPhase].avoidText}
          </div>
        </div>
      </div>
    </div>
  );
};

// =====================
// 信号历史组件
// =====================

const SignalHistoryPanel: React.FC<{ signals: TradingSignal[] }> = ({ signals }) => {
  const getSignalIcon = (type: string) => {
    switch (type) {
      case 'vortex_breakout': return <Zap size={16} style={{ color: '#1890ff' }} />;
      case 'resonance_trigger': return <TrendingUp size={16} style={{ color: '#faad14' }} />;
      case 'trend_callback': return <TrendingDown size={16} style={{ color: '#52c41a' }} />;
      default: return <Minus size={16} style={{ color: '#999' }} />;
    }
  };

  const getDirectionIcon = (direction: string) => {
    switch (direction) {
      case 'bullish': return <TrendingUp size={14} style={{ color: '#52c41a' }} />;
      case 'bearish': return <TrendingDown size={14} style={{ color: '#f5222d' }} />;
      default: return <Minus size={14} style={{ color: '#999' }} />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.7) return '#52c41a';
    if (confidence >= 0.4) return '#faad14';
    return '#f5222d';
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
    }}>
      <h3 style={{ margin: '0 0 20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <History size={20} style={{ color: '#1890ff' }} />
        信号历史
        <span style={{ 
          marginLeft: 'auto',
          padding: '4px 12px',
          borderRadius: '12px',
          background: '#f5f5f5',
          fontSize: '13px',
          color: '#666'
        }}>
          {signals.length} 条
        </span>
      </h3>
      
      {signals.length === 0 ? (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center', 
          color: '#999',
          background: '#fafafa',
          borderRadius: '8px'
        }}>
          <Clock size={40} style={{ marginBottom: '12px', opacity: 0.5 }} />
          <p style={{ margin: 0 }}>暂无信号记录</p>
          <p style={{ fontSize: '13px', marginTop: '8px' }}>运行模拟后将自动生成信号</p>
        </div>
      ) : (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {signals.slice(0, 20).map((signal, index) => (
            <div key={signal.id} style={{
              display: 'flex',
              alignItems: 'center',
              padding: '12px',
              borderBottom: index < signals.length - 1 ? '1px solid #f0f0f0' : 'none',
              transition: 'background 0.2s'
            }}>
              <div style={{ marginRight: '12px' }}>
                {getSignalIcon(signal.type)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600, fontSize: '14px' }}>
                    {signal.type.replace('_', ' ').toUpperCase()}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#666', fontSize: '13px' }}>
                    {getDirectionIcon(signal.direction)}
                    {signal.direction}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#999' }}>
                  {signal.reason}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ 
                  fontWeight: 600, 
                  color: getConfidenceColor(signal.confidence),
                  marginBottom: '2px'
                }}>
                  {Math.round(signal.confidence * 100)}%
                </div>
                <div style={{ fontSize: '11px', color: '#999' }}>
                  {formatTime(signal.timestamp)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NEMTApp;
