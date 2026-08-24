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
 * NEMT理论 - 比特币双重人格组件
 */

import React, { useState } from 'react';
import { 
  Bitcoin, 
  TrendingUp, 
  Shield, 
  Zap, 
  ArrowRight, 
  ChevronDown, 
  ChevronUp,
  Activity,
  Target,
  Layers
} from 'lucide-react';

type TheorySubTab = 'intro' | 'modes' | 'switching' | 'rti' | 'practice' | 'case';

interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  color?: string;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({ 
  title, 
  icon, 
  children, 
  defaultOpen = true,
  color = '#1890ff'
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div style={{ 
      border: '1px solid #e8e8e8', 
      borderRadius: '12px', 
      marginBottom: '16px',
      overflow: 'hidden'
    }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '16px 20px',
          background: isOpen ? '#f8f9fa' : '#fff',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          transition: 'all 0.2s'
        }}
      >
        <div style={{ color, display: 'flex' }}>{icon}</div>
        <span style={{ fontSize: '16px', fontWeight: 600, flex: 1 }}>{title}</span>
        {isOpen ? <ChevronUp size={20} color="#666" /> : <ChevronDown size={20} color="#666" />}
      </button>
      {isOpen && (
        <div style={{ padding: '20px', background: '#fff', borderTop: '1px solid #e8e8e8' }}>
          {children}
        </div>
      )}
    </div>
  );
};

export const TheoryTab: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<TheorySubTab>('intro');

  const subTabs = [
    { id: 'intro', label: '概述', icon: <Activity size={16} /> },
    { id: 'modes', label: '双重模式', icon: <Layers size={16} /> },
    { id: 'switching', label: '角色切换', icon: <ArrowRight size={16} /> },
    { id: 'rti', label: 'RTI指标', icon: <Target size={16} /> },
    { id: 'practice', label: '实战指南', icon: <TrendingUp size={16} /> },
    { id: 'case', label: '案例复盘', icon: <Bitcoin size={16} /> },
  ];

  const goldModeFeatures = [
    { label: '与纳斯达克相关性', value: '低（<0.3）或负', color: '#52c41a' },
    { label: '与黄金相关性', value: '正（>0.5）', color: '#faad14' },
    { label: '与美元指数相关性', value: '负（美元弱→比特币强）', color: '#1890ff' },
    { label: '主导叙事', value: '稀缺性、抗审查、主权对冲', color: '#722ed1' },
    { label: '链上行为', value: 'LTH持仓增长，交易所余额下降', color: '#13c2c2' },
    { label: '波动特征', value: '趋势性强，回调幅度相对克制', color: '#eb2f96' },
  ];

  const techModeFeatures = [
    { label: '与纳斯达克相关性', value: '高（>0.6）', color: '#f5222d' },
    { label: '与黄金相关性', value: '低或负', color: '#8c8c8c' },
    { label: '与美元指数相关性', value: '不显著或正', color: '#d9d9d9' },
    { label: '主导叙事', value: '创新、ETF、机构采用', color: '#1890ff' },
    { label: '链上行为', value: 'STH活跃，交易所流入增加', color: '#52c41a' },
    { label: '波动特征', value: '暴涨暴跌，高贝塔', color: '#fa8c16' },
  ];

  const rtiCriteria = [
    { 
      item: 'BTC-纳斯达克30日相关性', 
      gold: '<0.2', 
      neutral: '0.3-0.5', 
      tech: '>0.7',
      goldColor: '#52c41a',
      techColor: '#f5222d'
    },
    { 
      item: 'BTC-黄金30日相关性', 
      gold: '>0.6', 
      neutral: '0.2-0.4', 
      tech: '<0.1或负',
      goldColor: '#faad14',
      techColor: '#8c8c8c'
    },
    { 
      item: '交易所BTC余额趋势', 
      gold: '持续下降', 
      neutral: '横盘', 
      tech: '持续上升',
      goldColor: '#13c2c2',
      techColor: '#eb2f96'
    },
    { 
      item: 'LTH供应量占比变化', 
      gold: '月增长>1%', 
      neutral: '变化<0.5%', 
      tech: '月下降>1%',
      goldColor: '#722ed1',
      techColor: '#fa8c16'
    },
    { 
      item: '资金费率情绪', 
      gold: '持续负费率', 
      neutral: '正常区间', 
      tech: '持续高正费率',
      goldColor: '#1890ff',
      techColor: '#f5222d'
    },
  ];

  const renderContent = () => {
    switch (activeSubTab) {
      case 'intro':
        return (
          <div style={{ lineHeight: 1.8 }}>
            <p style={{ fontSize: '16px', marginBottom: '20px', color: '#333' }}>
              比特币具有<strong style={{ color: '#faad14' }}>数字黄金</strong>和<strong style={{ color: '#1890ff' }}>高波动科技股</strong>双重属性。
              在某一时期，只有一种属性主导定价。
            </p>
            
            <div style={{ 
              background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
              borderRadius: '12px',
              padding: '24px',
              color: '#fff',
              marginBottom: '20px'
            }}>
              <h4 style={{ margin: '0 0 16px', fontSize: '18px' }}>核心观点</h4>
              <p style={{ margin: '0 0 12px', opacity: 0.9 }}>
                比特币到底是什么？<strong>NEMT的答案是：它两者都是，但在不同的市场相位中，主导角色会切换。</strong>
              </p>
              <p style={{ margin: 0, opacity: 0.9 }}>
                交易者的任务不是争论比特币的本质，而是<strong>识别当前市场正在以哪种角色定价，并根据角色特征制定策略。</strong>
              </p>
            </div>

            <h4 style={{ marginBottom: '12px' }}>历史案例</h4>
            <div style={{ display: 'grid', gap: '12px' }}>
              <div style={{ 
                padding: '16px', 
                background: '#fff2e8', 
                borderRadius: '8px',
                borderLeft: '4px solid #fa8c16'
              }}>
                <strong style={{ color: '#d4380d' }}>2020年3月12日</strong>：比特币暴跌50%，与纳斯达克同步。表现为<strong>高波动科技股</strong>。
              </div>
              <div style={{ 
                padding: '16px', 
                background: '#fffdd6', 
                borderRadius: '8px',
                borderLeft: '4px solid #faad14'
              }}>
                <strong style={{ color: '#d48806' }}>2020年7月</strong>：比特币突破10000美元，涨幅超6倍。表现为<strong>数字黄金</strong>。
              </div>
              <div style={{ 
                padding: '16px', 
                background: '#e6f7ff', 
                borderRadius: '8px',
                borderLeft: '4px solid #1890ff'
              }}>
                <strong style={{ color: '#096dd9' }}>2023年3月</strong>：硅谷银行倒闭后，比特币与黄金同步上涨。切换至<strong>数字黄金模式</strong>。
              </div>
            </div>
          </div>
        );

      case 'modes':
        return (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              {/* 数字黄金模式 */}
              <div style={{ 
                border: '2px solid #faad14',
                borderRadius: '12px',
                padding: '20px',
                background: '#fffbe6'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <Shield size={28} color="#faad14" />
                  <h4 style={{ margin: 0, fontSize: '20px', color: '#d48806' }}>数字黄金模式</h4>
                </div>
                <p style={{ fontSize: '14px', color: '#666', marginBottom: '16px', lineHeight: 1.6 }}>
                  定价逻辑围绕稀缺性叙事、价值储存需求、与黄金的替代关系展开。
                </p>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {goldModeFeatures.map((f, i) => (
                    <div key={i} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: '#fff',
                      borderRadius: '6px'
                    }}>
                      <span style={{ fontSize: '13px', color: '#666' }}>{f.label}</span>
                      <span style={{ fontSize: '13px', fontWeight: 500, color: f.color }}>{f.value}</span>
                    </div>
                  ))}
                </div>
                <div style={{ 
                  marginTop: '16px', 
                  padding: '12px',
                  background: '#52c41a',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '14px',
                  textAlign: 'center'
                }}>
                  偏向：+2分
                </div>
              </div>

              {/* 科技股模式 */}
              <div style={{ 
                border: '2px solid #1890ff',
                borderRadius: '12px',
                padding: '20px',
                background: '#e6f7ff'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <Zap size={28} color="#1890ff" />
                  <h4 style={{ margin: 0, fontSize: '20px', color: '#096dd9' }}>高波动科技股模式</h4>
                </div>
                <p style={{ fontSize: '14px', color: '#666', marginBottom: '16px', lineHeight: 1.6 }}>
                  被归类为风险资产，定价逻辑切换为流动性驱动、风险偏好指标。
                </p>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {techModeFeatures.map((f, i) => (
                    <div key={i} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: '#fff',
                      borderRadius: '6px'
                    }}>
                      <span style={{ fontSize: '13px', color: '#666' }}>{f.label}</span>
                      <span style={{ fontSize: '13px', fontWeight: 500, color: f.color }}>{f.value}</span>
                    </div>
                  ))}
                </div>
                <div style={{ 
                  marginTop: '16px', 
                  padding: '12px',
                  background: '#f5222d',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '14px',
                  textAlign: 'center'
                }}>
                  偏向：-2分
                </div>
              </div>
            </div>
          </div>
        );

      case 'switching':
        return (
          <div>
            <CollapsibleSection 
              title="3.2.1 宏观流动性拐点（最核心）" 
              icon={<Activity size={20} />}
              color="#f5222d"
            >
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div style={{ padding: '16px', background: '#f6ffed', borderRadius: '8px', borderLeft: '4px solid #52c41a' }}>
                  <h5 style={{ margin: '0 0 8px', color: '#389e0d' }}>流动性扩张期</h5>
                  <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
                    降息、QE、财政刺激 → 资金成本低，风险偏好高 → <strong>倾向于高波动科技股模式</strong>
                  </p>
                </div>
                <div style={{ padding: '16px', background: '#fffbe6', borderRadius: '8px', borderLeft: '4px solid #faad14' }}>
                  <h5 style={{ margin: '0 0 8px', color: '#d48806' }}>流动性收缩期</h5>
                  <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
                    加息、QT、信贷紧缩 → 若比特币能<strong>与纳斯达克脱钩</strong> → 开始切换至<strong>数字黄金模式</strong>
                  </p>
                </div>
              </div>
              <div style={{ 
                marginTop: '16px', 
                padding: '16px',
                background: '#f0f5ff',
                borderRadius: '8px'
              }}>
                <strong>切换信号：</strong>BTC-纳斯达克30天相关性从0.6以上快速下降到0.3以下，同时与黄金的相关性开始转正。
              </div>
            </CollapsibleSection>

            <CollapsibleSection 
              title="3.2.2 减半周期的阶段" 
              icon={<Bitcoin size={20} />}
              color="#722ed1"
            >
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div style={{ padding: '16px', background: '#fffbe6', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>减半前6-12个月</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#faad14' }}>数字黄金模式</div>
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>叙事：供给稀缺</div>
                </div>
                <div style={{ padding: '16px', background: '#e6f7ff', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>减半后6-18个月</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#1890ff' }}>科技股模式</div>
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>叙事：机构采用、ETF</div>
                </div>
                <div style={{ padding: '16px', background: '#fff0f0', borderRadius: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>牛市末端至熊市初期</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#f5222d' }}>风险资产属性</div>
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>叙事：杠杆泡沫破裂</div>
                </div>
              </div>
            </CollapsibleSection>

            <CollapsibleSection 
              title="3.2.3 链上结构转换" 
              icon={<Layers size={20} />}
              color="#13c2c2"
            >
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <h5 style={{ margin: '0 0 12px', color: '#389e0d' }}>切换至黄金模式的链上信号</h5>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '14px', color: '#666' }}>
                    <li>交易所余额从上升转为下降</li>
                    <li>1年以上未移动的供应量占比上升</li>
                    <li>矿工流出量下降</li>
                    <li>鲸鱼地址数（&gt;1000 BTC）增长</li>
                  </ul>
                </div>
                <div>
                  <h5 style={{ margin: '0 0 12px', color: '#f5222d' }}>切换至科技股模式的链上信号</h5>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '14px', color: '#666' }}>
                    <li>交易所余额开始上升</li>
                    <li>短期持有者供应量占比上升</li>
                    <li>稳定币交易所余额增长</li>
                    <li>永续合约持仓量（OI）快速攀升</li>
                  </ul>
                </div>
              </div>
            </CollapsibleSection>
          </div>
        );

      case 'rti':
        return (
          <div>
            <div style={{ 
              background: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)',
              borderRadius: '12px',
              padding: '24px',
              color: '#fff',
              marginBottom: '20px'
            }}>
              <h4 style={{ margin: '0 0 12px', fontSize: '20px' }}>角色倾向指数 (Role Tendency Index, RTI)</h4>
              <p style={{ margin: 0, opacity: 0.9, fontSize: '14px' }}>
                RTI由五个子项构成，每项得分-2到+2，总分-10到+10。<br/>
                正分越高，越偏向数字黄金模式；负分越低，越偏向科技股模式。
              </p>
            </div>

            <div style={{ 
              border: '1px solid #e8e8e8', 
              borderRadius: '8px', 
              overflow: 'hidden',
              marginBottom: '20px'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: '#fafafa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e8e8e8' }}>子项</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e8e8e8', color: '#d48806', width: '25%' }}>数字黄金端（+2）</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e8e8e8', color: '#666', width: '25%' }}>中性（0）</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e8e8e8', color: '#f5222d', width: '25%' }}>科技股端（-2）</th>
                  </tr>
                </thead>
                <tbody>
                  {rtiCriteria.map((c, i) => (
                    <tr key={i}>
                      <td style={{ padding: '12px', borderBottom: '1px solid #f0f0f0', fontWeight: 500 }}>
                        {c.item}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', color: c.goldColor }}>
                        {c.gold}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', color: '#666' }}>
                        {c.neutral}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', color: c.techColor }}>
                        {c.tech}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div style={{ 
                padding: '20px', 
                background: '#fffbe6', 
                borderRadius: '8px',
                border: '2px solid #faad14',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '32px', fontWeight: 700, color: '#faad14' }}>RTI ≥ +5</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#d48806', margin: '8px 0' }}>确认数字黄金模式</div>
                <div style={{ fontSize: '12px', color: '#666' }}>策略：回调加仓，止损放宽</div>
              </div>
              <div style={{ 
                padding: '20px', 
                background: '#f5f5f5', 
                borderRadius: '8px',
                border: '2px solid #d9d9d9',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '32px', fontWeight: 700, color: '#666' }}>-5 ~ +5</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#666', margin: '8px 0' }}>模式模糊期</div>
                <div style={{ fontSize: '12px', color: '#666' }}>策略：降低仓位，等待明确</div>
              </div>
              <div style={{ 
                padding: '20px', 
                background: '#e6f7ff', 
                borderRadius: '8px',
                border: '2px solid #1890ff',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '32px', fontWeight: 700, color: '#1890ff' }}>RTI ≤ -5</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#096dd9', margin: '8px 0' }}>确认科技股模式</div>
                <div style={{ fontSize: '12px', color: '#666' }}>策略：紧盯美联储，仓位灵活</div>
              </div>
            </div>
          </div>
        );

      case 'practice':
        return (
          <div>
            <CollapsibleSection 
              title="3.4.1 择时：在正确的模式下做正确的事" 
              icon={<Target size={20} />}
              color="#52c41a"
            >
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div style={{ padding: '16px', background: '#fffbe6', borderRadius: '8px' }}>
                  <h5 style={{ margin: '0 0 12px', color: '#d48806' }}>RTI确认数字黄金模式时</h5>
                  <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '14px', color: '#666' }}>
                    <li>应该<strong>更多关注月线和周线</strong></li>
                    <li>回调是"上车机会"而非"趋势反转"</li>
                    <li>应该<strong>少看15分钟线</strong></li>
                    <li>止损设在链上成本带以下</li>
                  </ul>
                </div>
                <div style={{ padding: '16px', background: '#e6f7ff', borderRadius: '8px' }}>
                  <h5 style={{ margin: '0 0 12px', color: '#096dd9' }}>RTI确认科技股模式时</h5>
                  <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '14px', color: '#666' }}>
                    <li>应该<strong>关注美股盘前和开盘时段</strong></li>
                    <li>紧盯<strong>美联储日程</strong></li>
                    <li>密切关注纳斯达克和VIX</li>
                    <li>使用更严格的追踪止损</li>
                  </ul>
                </div>
              </div>
            </CollapsibleSection>

            <CollapsibleSection 
              title="3.4.2 仓位：根据角色调整风险暴露" 
              icon={<TrendingUp size={20} />}
              color="#722ed1"
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: '#fafafa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e8e8e8' }}>模式</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e8e8e8' }}>基础仓位</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e8e8e8' }}>加仓节奏</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e8e8e8' }}>止损宽容度</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '12px', borderBottom: '1px solid #f0f0f0', fontWeight: 500, color: '#d48806' }}>
                      数字黄金模式
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                      偏高（60-80%）
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                      回测加仓
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                      宽（15-20%）
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '12px', borderBottom: '1px solid #f0f0f0', fontWeight: 500, color: '#666' }}>
                      模式模糊期
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                      中性（30-50%）
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                      不主动加仓
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
                      标准（10-15%）
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '12px', fontWeight: 500, color: '#096dd9' }}>
                      科技股模式
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      灵活（20-60%）
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      突破加仓
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      紧（5-10%）
                    </td>
                  </tr>
                </tbody>
              </table>
            </CollapsibleSection>

            <CollapsibleSection 
              title="3.4.3 对冲：利用二重性构建内部对冲" 
              icon={<Shield size={20} />}
              color="#13c2c2"
            >
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '16px', lineHeight: 1.8 }}>
                利用比特币在不同角色下的<strong>波动特征差异</strong>来管理曲线风险。
              </p>
              <div style={{ 
                padding: '16px', 
                background: '#f0f5ff', 
                borderRadius: '8px',
                fontSize: '14px',
                lineHeight: 2
              }}>
                <div>1. 在RTI高（黄金模式）时建立现货长仓，以月为持有周期</div>
                <div>2. 在RTI开始下降时，不开新仓，用部分利润买入看跌期权或建立永续合约空头对冲</div>
                <div>3. 当RTI降至负值（科技股模式）且市场出现泡沫特征时，对冲仓位可以加码</div>
              </div>
              <div style={{ 
                marginTop: '16px',
                padding: '12px',
                background: '#fff7e6',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#d48806'
              }}>
                <strong>关键洞察：</strong>黄金模式下跌慢、反弹快；科技股模式下跌快、反弹慢。
              </div>
            </CollapsibleSection>
          </div>
        );

      case 'case':
        return (
          <div>
            <div style={{ 
              background: 'linear-gradient(135deg, #fa8c16 0%, #d46b08 100%)',
              borderRadius: '12px',
              padding: '20px',
              color: '#fff',
              marginBottom: '20px'
            }}>
              <h4 style={{ margin: '0 0 8px', fontSize: '18px' }}>案例：2023年3月硅谷银行事件</h4>
              <p style={{ margin: 0, opacity: 0.9, fontSize: '14px' }}>一次教科书级别的角色切换</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div style={{ 
                padding: '16px', 
                background: '#fff0f0', 
                borderRadius: '8px',
                borderLeft: '4px solid #f5222d'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>切换前（2023年1-2月）</div>
                <div style={{ fontSize: '14px', fontWeight: 500, color: '#f5222d' }}>BTC-纳指相关性：0.65</div>
                <div style={{ fontSize: '14px', fontWeight: 500, color: '#f5222d' }}>RTI：约 -3</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>科技股模式偏强</div>
              </div>
              <div style={{ 
                padding: '16px', 
                background: '#fffdd6', 
                borderRadius: '8px',
                borderLeft: '4px solid #faad14'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>切换触发（3月10-12日）</div>
                <div style={{ fontSize: '14px', fontWeight: 500, color: '#fa8c16' }}>BTC-纳指相关性：0.6 → 0.1</div>
                <div style={{ fontSize: '14px', fontWeight: 500, color: '#fa8c16' }}>BTC-黄金相关性：0.2 → 0.6</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>银行倒闭触发</div>
              </div>
              <div style={{ 
                padding: '16px', 
                background: '#f6ffed', 
                borderRadius: '8px',
                borderLeft: '4px solid #52c41a'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>切换后（3月中旬-4月）</div>
                <div style={{ fontSize: '14px', fontWeight: 500, color: '#52c41a' }}>RTI升至 +6</div>
                <div style={{ fontSize: '14px', fontWeight: 500, color: '#52c41a' }}>BTC: $20000 → $31000</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>确认黄金模式</div>
              </div>
            </div>

            <div style={{ 
              padding: '20px', 
              background: '#fafafa', 
              borderRadius: '8px',
              marginBottom: '16px'
            }}>
              <h5 style={{ margin: '0 0 12px', fontSize: '16px' }}>价格表现对比</h5>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 700, color: '#52c41a' }}>+55%</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>比特币</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 700, color: '#1890ff' }}>+8%</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>纳斯达克</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 700, color: '#faad14' }}>+10%</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>黄金</div>
                </div>
              </div>
            </div>

            <div style={{ 
              padding: '20px',
              background: '#e6f7ff',
              borderRadius: '8px'
            }}>
              <h5 style={{ margin: '0 0 12px', fontSize: '16px', color: '#096dd9' }}>交易层面的推演</h5>
              <div style={{ display: 'grid', gap: '12px', fontSize: '14px' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                  <span style={{ 
                    background: '#1890ff', 
                    color: '#fff', 
                    padding: '2px 8px', 
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}>3月10-12日</span>
                  <span>RTI快速上升，是切换的确认窗口。应将思维从"反弹减仓"切换为"回调加仓"</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                  <span style={{ 
                    background: '#52c41a', 
                    color: '#fff', 
                    padding: '2px 8px', 
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}>3月中旬</span>
                  <span>回调（如$26000→$24000）都是黄金模式下的加仓机会，而非离场信号</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                  <span style={{ 
                    background: '#faad14', 
                    color: '#fff', 
                    padding: '2px 8px', 
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}>4月中旬</span>
                  <span>RTI开始回落时，再重新评估风险</span>
                </div>
              </div>
            </div>

            <div style={{ 
              marginTop: '20px',
              padding: '16px',
              background: '#fffbe6',
              borderRadius: '8px',
              border: '2px solid #faad14',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '16px', fontWeight: 600, color: '#d48806' }}>
                角色的切换本身就是一个巨大的阿尔法信号
              </div>
              <div style={{ fontSize: '14px', color: '#666', marginTop: '8px' }}>
                识别切换的早晚，决定了你是在车上还是在车下
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '20px', minHeight: '600px' }}>
      {/* 左侧导航 */}
      <div style={{ 
        background: '#fff',
        borderRadius: '12px',
        padding: '16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        height: 'fit-content'
      }}>
        <h4 style={{ margin: '0 0 16px', fontSize: '14px', color: '#666' }}>目录</h4>
        <div style={{ display: 'grid', gap: '4px' }}>
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as TheorySubTab)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 12px',
                border: 'none',
                borderRadius: '6px',
                background: activeSubTab === tab.id ? '#e6f7ff' : 'transparent',
                color: activeSubTab === tab.id ? '#1890ff' : '#666',
                cursor: 'pointer',
                fontSize: '14px',
                textAlign: 'left',
                transition: 'all 0.2s'
              }}
            >
              <span style={{ color: activeSubTab === tab.id ? '#1890ff' : '#999' }}>
                {tab.icon}
              </span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 右侧内容 */}
      <div style={{ 
        background: '#fff',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
      }}>
        <h3 style={{ margin: '0 0 20px', fontSize: '20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Bitcoin size={24} color="#faad14" />
          第三章：黄金-股票二重性
          <span style={{ 
            fontSize: '12px', 
            fontWeight: 400, 
            color: '#999',
            marginLeft: 'auto'
          }}>
            比特币的双重人格与角色切换
          </span>
        </h3>
        {renderContent()}
      </div>
    </div>
  );
};
