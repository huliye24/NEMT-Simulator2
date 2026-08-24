/**
 * NEMT 理论中枢仪表板
 * 展示从 Notion 同步的执行框架配置
 */

import React, { useState, useEffect } from 'react';
import {
  DEFAULT_THEORY_CONFIG,
  PHASE_POSITION_MAP,
  getPositionByPhase,
  getATRMultiplier,
  checkLeverageAllowed,
  formatTheorySummary,
  type PhasePosition,
  type RebalanceRule,
} from '../services/notionTheorySync';
import { MarketPhase } from '../types';

interface TheoryDashboardProps {
  currentPhase?: MarketPhase;
  macroScore?: number;
  onchainScore?: number;
}

export const TheoryDashboard: React.FC<TheoryDashboardProps> = ({
  currentPhase = MarketPhase.PHASE_A_NOISE,
  macroScore = 5,
  onchainScore = 5,
}) => {
  const [activeTab, setActiveTab] = useState<'phases' | 'stoploss' | 'rebalance' | 'leverage'>('phases');

  // 当前相位配置
  const currentPhaseConfig = getPositionByPhase(currentPhase);

  // ATR 倍数配置
  const atrMultipliers = {
    vortexBreakout: getATRMultiplier('vortex_breakout'),
    resonanceTrigger: getATRMultiplier('resonance_trigger'),
    trendCallback: getATRMultiplier('trend_callback'),
  };

  // 杠杆检查
  const leverageCheck = checkLeverageAllowed(currentPhase, macroScore, onchainScore, 0);

  return (
    <div className="theory-dashboard p-4 bg-gray-900 rounded-lg">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">
          NEMT 执行框架
          <span className="ml-2 text-xs text-gray-400">(Notion 同步)</span>
        </h2>
        <span className="text-xs text-green-400">✓ 已同步</span>
      </div>

      {/* 标签页 */}
      <div className="flex border-b border-gray-700 mb-4">
        {(['phases', 'stoploss', 'rebalance', 'leverage'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {tab === 'phases' && '📊 相位仓位'}
            {tab === 'stoploss' && '📉 止损规则'}
            {tab === 'rebalance' && '🔄 再平衡'}
            {tab === 'leverage' && '⚠️ 杠杆'}
          </button>
        ))}
      </div>

      {/* 内容区域 */}
      <div className="min-h-[300px]">
        {/* 相位仓位表 */}
        {activeTab === 'phases' && (
          <div className="space-y-3">
            <div className="text-sm text-gray-400 mb-2">当前相位: <span className="text-white font-medium">{currentPhaseConfig.name}</span></div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="text-left py-2">相位</th>
                  <th className="text-right py-2">最大仓位</th>
                  <th className="text-right py-2">单笔风险</th>
                  <th className="text-right py-2">杠杆</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(PHASE_POSITION_MAP).map(([phase, config]) => (
                  <tr
                    key={phase}
                    className={`border-b border-gray-800 ${
                      phase === currentPhase ? 'bg-blue-900/30' : ''
                    }`}
                  >
                    <td className="py-2">
                      <span className={`font-medium ${
                        phase === currentPhase ? 'text-blue-400' : 'text-white'
                      }`}>
                        {config.name}
                      </span>
                    </td>
                    <td className="text-right text-green-400">
                      {(config.maxPosition * 100).toFixed(0)}%
                    </td>
                    <td className="text-right text-yellow-400">
                      {(config.singleRisk * 100).toFixed(1)}%
                    </td>
                    <td className="text-right text-purple-400">
                      {config.leverage}x
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-3 text-xs text-gray-500">
              策略: {currentPhaseConfig.strategy}
            </div>
          </div>
        )}

        {/* 止损规则 */}
        {activeTab === 'stoploss' && (
          <div className="space-y-4">
            <div className="text-sm text-gray-400 mb-2">ATR 适应型止损</div>
            <div className="grid gap-3">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex justify-between items-center">
                  <span className="text-white">涡旋突破</span>
                  <span className="text-2xl font-bold text-blue-400">
                    {atrMultipliers.vortexBreakout}x ATR
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">适用于涡旋边界突破信号</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex justify-between items-center">
                  <span className="text-white">随机共振触发</span>
                  <span className="text-2xl font-bold text-purple-400">
                    {atrMultipliers.resonanceTrigger}x ATR
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">给予更多噪声空间，适合临界点</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="flex justify-between items-center">
                  <span className="text-white">趋势回调加仓</span>
                  <span className="text-2xl font-bold text-green-400">
                    {atrMultipliers.trendCallback}x ATR
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">趋势中回调通常较浅，紧凑止损</p>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              公式: 止损距离 = ATR(14) × 倍数
            </div>
          </div>
        )}

        {/* 再平衡规则 */}
        {activeTab === 'rebalance' && (
          <div className="space-y-4">
            <div>
              <div className="flex items-center mb-2">
                <span className="text-red-400 mr-2">📉</span>
                <span className="text-sm font-medium text-white">减仓触发</span>
              </div>
              <div className="space-y-2">
                {DEFAULT_THEORY_CONFIG.rebalance.reduceTriggers.map((rule, i) => (
                  <div key={i} className="bg-red-900/20 border border-red-800/30 rounded p-2">
                    <div className="text-sm text-red-300">{rule.condition}</div>
                    <div className="text-xs text-gray-400">{rule.action}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="flex items-center mb-2">
                <span className="text-green-400 mr-2">📈</span>
                <span className="text-sm font-medium text-white">加仓触发</span>
              </div>
              <div className="space-y-2">
                {DEFAULT_THEORY_CONFIG.rebalance.addTriggers.map((rule, i) => (
                  <div key={i} className="bg-green-900/20 border border-green-800/30 rounded p-2">
                    <div className="text-sm text-green-300">{rule.condition}</div>
                    <div className="text-xs text-gray-400">{rule.action}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 杠杆规则 */}
        {activeTab === 'leverage' && (
          <div className="space-y-4">
            <div className="bg-yellow-900/20 border border-yellow-800/30 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-yellow-400 font-medium">当前杠杆状态</span>
                <span className={`text-sm ${leverageCheck.allowed ? 'text-green-400' : 'text-red-400'}`}>
                  {leverageCheck.allowed ? '✓ 允许' : '✗ 禁止'}
                </span>
              </div>
              <div className="text-xs text-gray-400">{leverageCheck.reason}</div>
            </div>

            <div className="text-sm text-gray-400 mb-2">杠杆使用规则</div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-gray-800 rounded p-2 text-center">
                <div className="text-2xl font-bold text-purple-400">3x</div>
                <div className="text-xs text-gray-400">最大杠杆</div>
              </div>
              <div className="bg-gray-800 rounded p-2 text-center">
                <div className="text-2xl font-bold text-blue-400">5%</div>
                <div className="text-xs text-gray-400">安全边际</div>
              </div>
            </div>

            <div className="text-sm text-gray-400 mb-2">允许相位: C, D</div>

            <div className="text-sm font-medium text-red-400 mb-2">绝对禁止</div>
            <div className="space-y-1">
              {DEFAULT_THEORY_CONFIG.leverage.forbiddenConditions.map((condition, i) => (
                <div key={i} className="text-xs text-gray-400 flex items-start">
                  <span className="text-red-500 mr-2">✗</span>
                  {condition}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TheoryDashboard;
