import React, { useState } from 'react';
import { LayoutGrid, Play, Pause, Settings, Terminal, Activity, TrendingUp, TrendingDown, Clock, ChevronRight, X, Plus } from 'lucide-react';

/**
 * NEMT Platform - 策略容器平台
 * 提供策略市场、容器管理、胶囊市场等功能
 */

type NavItemType = 'market' | 'containers' | 'capsule' | 'sdk';
type TabType = 'signals' | 'config' | 'strategy';
type DirectionType = 'bullish' | 'bearish' | 'neutral';

interface Strategy {
  id: string;
  name: string;
  author: string;
  status: 'running' | 'paused' | 'stopped';
  trades: number;
  winRate: number;
  pnl: string;
  sharpe: number;
  description: string;
}

interface Signal {
  id: string;
  type: 'vortex' | 'resonance' | 'trend' | 'macro';
  direction: DirectionType;
  confidence: number;
  phase: string;
  maturity: number;
  dci: number;
  atr: number;
  timestamp: string;
}

const NemtPlatform: React.FC = () => {
  const [activeNav, setActiveNav] = useState<NavItemType>('market');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 模拟策略数据
  const strategies: Strategy[] = [
    {
      id: '1',
      name: 'Vortex Breakout',
      author: 'NEMT Lab',
      status: 'running',
      trades: 1234,
      winRate: 62.0,
      pnl: '$15,680',
      sharpe: 2.34,
      description: '基于涡流理论的突破策略，捕捉市场临界状态的方向选择机会'
    },
    {
      id: '2',
      name: 'Stochastic Resonance',
      author: 'Quantum Trader',
      status: 'paused',
      trades: 856,
      winRate: 58.5,
      pnl: '$8,420',
      sharpe: 1.89,
      description: '随机共振量化策略，在噪声环境中寻找周期性机会'
    },
    {
      id: '3',
      name: 'Phase D Trend Hunter',
      author: 'Macro Algo',
      status: 'running',
      trades: 2341,
      winRate: 71.2,
      pnl: '$42,150',
      sharpe: 3.15,
      description: '专注相位D趋势行情的趋势追踪策略'
    }
  ];

  // 模拟信号数据
  const signals: Signal[] = [
    {
      id: '1',
      type: 'vortex',
      direction: 'bullish',
      confidence: 68,
      phase: 'B',
      maturity: 67,
      dci: 0.73,
      atr: 3200,
      timestamp: '2分钟前'
    },
    {
      id: '2',
      type: 'resonance',
      direction: 'bearish',
      confidence: 45,
      phase: 'C',
      maturity: 82,
      dci: 0.61,
      atr: 2850,
      timestamp: '15分钟前'
    }
  ];

  const navItems: { id: NavItemType; icon: React.ReactNode; label: string }[] = [
    { id: 'market', icon: <LayoutGrid size={18}/>, label: '策略市场' },
    { id: 'containers', icon: <Settings size={18}/>, label: '容器管理' },
    { id: 'capsule', icon: <Activity size={18}/>, label: '胶囊市场' },
    { id: 'sdk', icon: <Terminal size={18}/>, label: 'SDK 文档' },
  ];

  const getStatusColor = (status: Strategy['status']) => {
    switch (status) {
      case 'running': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      case 'paused': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'stopped': return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  const getStatusText = (status: Strategy['status']) => {
    switch (status) {
      case 'running': return '运行中';
      case 'paused': return '已暂停';
      case 'stopped': return '已停止';
    }
  };

  const getSignalTypeLabel = (type: Signal['type']) => {
    switch (type) {
      case 'vortex': return '涡旋突破';
      case 'resonance': return '随机共振';
      case 'trend': return '趋势回调';
      case 'macro': return '宏观共振';
    }
  };

  const getSignalTypeColor = (type: Signal['type']) => {
    switch (type) {
      case 'vortex': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'resonance': return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'trend': return 'bg-green-500/10 text-green-400 border-green-500/20';
      case 'macro': return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
    }
  };

  return (
    <div className="min-h-screen bg-[#0f111a] text-gray-300 font-sans">
      {/* 顶部 Header */}
      <header className="flex justify-between items-center px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <LayoutGrid className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">NEMT Platform</h1>
            <p className="text-xs text-gray-500">策略容器平台 | Strategy Container Platform</p>
          </div>
        </div>
        
        <div className="flex gap-8 text-sm">
          <div className="text-center">
            <p className="text-emerald-400 font-bold">{strategies.filter(s => s.status === 'running').length}</p>
            <p className="text-[10px] text-gray-500">在线策略</p>
          </div>
          <div className="text-center">
            <p className="text-blue-400 font-bold">{strategies.length * 11}</p>
            <p className="text-[10px] text-gray-500">容器实例</p>
          </div>
          <div className="text-center">
            <p className="text-orange-400 font-bold">5,547</p>
            <p className="text-[10px] text-gray-500">今日交易</p>
          </div>
        </div>
      </header>

      <main className="flex">
        {/* 左侧侧边栏 */}
        <nav className="w-56 p-4 space-y-1 border-r border-gray-800 min-h-[calc(100vh-73px)]">
          {navItems.map((item) => (
            <div
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-colors ${
                activeNav === item.id 
                  ? 'bg-indigo-600/10 text-indigo-400' 
                  : 'hover:bg-white/5'
              }`}
            >
              {item.icon}
              <span className="text-sm font-medium">{item.label}</span>
            </div>
          ))}
        </nav>

        {/* 主内容区 */}
        <div className="flex-1 p-6">
          {activeNav === 'market' && (
            <>
              <div className="flex justify-between items-end mb-6">
                <h2 className="text-2xl font-semibold text-white">策略市场</h2>
                <button 
                  onClick={() => setShowCreateModal(true)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-md text-sm flex items-center gap-2 transition-colors"
                >
                  <Plus size={16} />
                  创建策略
                </button>
              </div>

              {/* 策略卡片列表 */}
              <div className="space-y-4">
                {strategies.map((strategy) => (
                  <div 
                    key={strategy.id}
                    className="bg-[#1a1d2e] rounded-xl border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors"
                  >
                    <div className="p-6">
                      <div className="flex justify-between">
                        <div className="flex gap-4">
                          <div className="w-12 h-12 bg-indigo-500/20 rounded-lg flex items-center justify-center text-indigo-400">
                            <Activity size={28} />
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-white">{strategy.name}</h3>
                            <p className="text-xs text-gray-500">by {strategy.author}</p>
                          </div>
                        </div>
                        <span className={`text-xs px-3 py-1 rounded-full border h-fit ${getStatusColor(strategy.status)}`}>
                          {getStatusText(strategy.status)}
                        </span>
                      </div>

                      <p className="mt-4 text-sm text-gray-400">{strategy.description}</p>

                      {/* 数据指标 */}
                      <div className="grid grid-cols-4 mt-6 py-4 border-y border-gray-800 text-center">
                        <Stat label="交易总数" value={strategy.trades.toLocaleString()} />
                        <Stat label="胜率" value={`${strategy.winRate}%`} />
                        <Stat label="盈亏" value={strategy.pnl} color="text-emerald-400" />
                        <Stat label="夏普比率" value={strategy.sharpe.toString()} />
                      </div>

                      {/* 操作按钮 */}
                      <div className="flex gap-3 mt-6">
                        <button className="flex-1 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all">
                          <Activity size={16} />
                          查看详情
                        </button>
                        {strategy.status === 'running' ? (
                          <button className="flex-1 bg-red-500/10 hover:bg-red-500/20 text-red-500 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all">
                            <Pause size={16} />
                            暂停策略
                          </button>
                        ) : (
                          <button className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all">
                            <Play size={16} />
                            启动策略
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {activeNav === 'containers' && (
            <div className="space-y-6">
              <div className="flex justify-between items-end">
                <h2 className="text-2xl font-semibold text-white">容器管理</h2>
                <button className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-md text-sm flex items-center gap-2">
                  + 新建容器
                </button>
              </div>

              {/* 容器列表表格 */}
              <div className="bg-[#1a1d2e] rounded-xl border border-gray-800 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-[#12141f]">
                    <tr className="text-left text-xs text-gray-500 uppercase">
                      <th className="px-6 py-4">容器名称</th>
                      <th className="px-6 py-4">策略</th>
                      <th className="px-6 py-4">状态</th>
                      <th className="px-6 py-4">资源</th>
                      <th className="px-6 py-4">运行时长</th>
                      <th className="px-6 py-4">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i} className="hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                              <Activity size={16} className="text-blue-400" />
                            </div>
                            <span className="text-white font-medium">container-{1000 + i}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm">{strategies[i % 3].name}</td>
                        <td className="px-6 py-4">
                          <span className="bg-emerald-500/10 text-emerald-500 text-xs px-2 py-1 rounded-full">
                            运行中
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-400">0.5 vCPU / 512MB</td>
                        <td className="px-6 py-4 text-sm text-gray-400">
                          {Math.floor(Math.random() * 72)}h {Math.floor(Math.random() * 60)}m
                        </td>
                        <td className="px-6 py-4">
                          <button className="text-gray-400 hover:text-white transition-colors">
                            <Settings size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeNav === 'capsule' && (
            <div className="space-y-6">
              <div className="flex justify-between items-end">
                <h2 className="text-2xl font-semibold text-white">胶囊市场</h2>
              </div>

              {/* 胶囊卡片 */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { name: 'Alpha Capsule', price: '0.5 ETH', Sharpe: 3.2, winRate: '68%' },
                  { name: 'Beta Capsule', price: '0.3 ETH', Sharpe: 2.8, winRate: '62%' },
                  { name: 'Gamma Capsule', price: '0.8 ETH', Sharpe: 4.1, winRate: '71%' },
                  { name: 'Delta Capsule', price: '0.4 ETH', Sharpe: 2.5, winRate: '59%' },
                  { name: 'Epsilon Capsule', price: '1.2 ETH', Sharpe: 3.8, winRate: '70%' },
                  { name: 'Omega Capsule', price: '2.0 ETH', Sharpe: 5.2, winRate: '75%' },
                ].map((capsule, i) => (
                  <div key={i} className="bg-[#1a1d2e] rounded-xl border border-gray-800 p-5 hover:border-gray-700 transition-colors">
                    <div className="flex justify-between items-start mb-4">
                      <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                        <Activity size={20} className="text-purple-400" />
                      </div>
                      <span className="bg-purple-500/10 text-purple-400 text-xs px-2 py-1 rounded-full">
                        #{i + 1}
                      </span>
                    </div>
                    <h3 className="text-white font-bold mb-1">{capsule.name}</h3>
                    <p className="text-xs text-gray-500 mb-4">高阶策略胶囊</p>
                    <div className="grid grid-cols-2 gap-2 mb-4">
                      <div className="bg-[#12141f] rounded-lg p-2 text-center">
                        <p className="text-emerald-400 font-bold">{capsule.Sharpe}</p>
                        <p className="text-[10px] text-gray-500">夏普</p>
                      </div>
                      <div className="bg-[#12141f] rounded-lg p-2 text-center">
                        <p className="text-blue-400 font-bold">{capsule.winRate}</p>
                        <p className="text-[10px] text-gray-500">胜率</p>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-orange-400 font-bold">{capsule.price}</span>
                      <button className="bg-purple-600 hover:bg-purple-500 text-white px-3 py-1.5 rounded-md text-xs transition-colors">
                        购买
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeNav === 'sdk' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold text-white">SDK 文档</h2>
              <div className="bg-[#1a1d2e] rounded-xl border border-gray-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Terminal size={20} className="text-emerald-400" />
                  <h3 className="text-white font-semibold">快速开始</h3>
                </div>
                <div className="bg-[#0d0f16] rounded-lg p-4 font-mono text-sm">
                  <p className="text-gray-500"># 安装 NEMT SDK</p>
                  <p className="text-emerald-400 mt-2">npm install @nemt/sdk</p>
                  <p className="text-gray-500 mt-4"># 初始化策略</p>
                  <p className="text-blue-400 mt-2">import NemtStrategy from '@nemt/sdk';</p>
                  <p className="text-gray-300 mt-2">const strategy = new NemtStrategy(&#123;</p>
                  <p className="text-gray-300 ml-4">phase: 'B',</p>
                  <p className="text-gray-300 ml-4">leverage: 1.0,</p>
                  <p className="text-gray-300 ml-4">maxPosition: 0.5</p>
                  <p className="text-gray-300">&#125;);</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 右侧信号面板 */}
        <div className="w-80 border-l border-gray-800 p-4 space-y-4">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Activity size={18} className="text-indigo-400" />
            实时信号
          </h3>

          {/* 信号卡片 */}
          {signals.map((signal) => (
            <div key={signal.id} className="bg-[#1a1d2e] rounded-xl border border-gray-800 p-4">
              <div className="flex justify-between items-start mb-3">
                <span className={`text-xs px-2 py-1 rounded-full border ${getSignalTypeColor(signal.type)}`}>
                  {getSignalTypeLabel(signal.type)}
                </span>
                <span className="text-xs text-gray-500">{signal.timestamp}</span>
              </div>
              
              <div className="flex items-center gap-2 mb-3">
                {signal.direction === 'bullish' ? (
                  <TrendingUp size={20} className="text-emerald-400" />
                ) : signal.direction === 'bearish' ? (
                  <TrendingDown size={20} className="text-red-400" />
                ) : (
                  <Activity size={20} className="text-gray-400" />
                )}
                <span className="text-white font-semibold capitalize">{signal.direction}</span>
                <span className="text-indigo-400 font-bold ml-auto">{signal.confidence}%</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-[#12141f] rounded-lg p-2">
                  <p className="text-gray-500">相位</p>
                  <p className="text-white font-medium">{signal.phase}</p>
                </div>
                <div className="bg-[#12141f] rounded-lg p-2">
                  <p className="text-gray-500">成熟度</p>
                  <p className="text-white font-medium">{signal.maturity}%</p>
                </div>
                <div className="bg-[#12141f] rounded-lg p-2">
                  <p className="text-gray-500">DCI</p>
                  <p className="text-white font-medium">{signal.dci}</p>
                </div>
                <div className="bg-[#12141f] rounded-lg p-2">
                  <p className="text-gray-500">ATR</p>
                  <p className="text-white font-medium">${signal.atr.toLocaleString()}</p>
                </div>
              </div>
            </div>
          ))}

          {/* 统计信息 */}
          <div className="bg-[#1a1d2e] rounded-xl border border-gray-800 p-4">
            <h4 className="text-xs text-gray-500 uppercase mb-3">市场统计</h4>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">总信号数</span>
                <span className="text-white font-medium">1,234</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">看涨信号</span>
                <span className="text-emerald-400 font-medium">723</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">看跌信号</span>
                <span className="text-red-400 font-medium">456</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">中性信号</span>
                <span className="text-gray-400 font-medium">55</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 创建策略弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1a1d2e] rounded-xl border border-gray-800 w-[500px]">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-800">
              <h3 className="text-white font-semibold">创建新策略</h3>
              <button 
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">策略名称</label>
                <input 
                  type="text"
                  placeholder="输入策略名称"
                  className="w-full bg-[#12141f] border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">策略类型</label>
                <select className="w-full bg-[#12141f] border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                  <option>涡旋突破策略</option>
                  <option>随机共振策略</option>
                  <option>趋势追踪策略</option>
                  <option>宏观配置策略</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">初始资金</label>
                <input 
                  type="text"
                  placeholder="$10,000"
                  className="w-full bg-[#12141f] border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
            <div className="flex gap-3 px-6 py-4 border-t border-gray-800">
              <button 
                onClick={() => setShowCreateModal(false)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2.5 rounded-lg transition-colors"
              >
                取消
              </button>
              <button className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2.5 rounded-lg transition-colors">
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const Stat = ({ label, value, color = "text-white" }: { label: string; value: string; color?: string }) => (
  <div>
    <p className={`${color} text-lg font-bold`}>{value}</p>
    <p className="text-[10px] text-gray-500 uppercase mt-1">{label}</p>
  </div>
);

export default NemtPlatform;
