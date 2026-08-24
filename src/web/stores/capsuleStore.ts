/**
 * Copyright 2026 NEMT Lab
 *
 * 胶囊 Store - 独立管理胶囊容器状态
 * 遵循原则：单一职责，只管胶囊
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================
// 类型定义
// ============================================

export type CapsuleType = 'market' | 'signal' | 'risk' | 'execution' | 'brain' | 'monitor';
export type CapsuleStatus = 'active' | 'inactive' | 'error';

export interface Capsule {
  id: string;
  name: string;
  type: CapsuleType;
  status: CapsuleStatus;
  instanceCount: number;
  description?: string;
  version?: string;
}

export interface CapsuleConfig {
  maxInstances: number;
  autoRestart: boolean;
  healthCheckInterval: number;
}

// ============================================
// 状态接口
// ============================================

interface CapsuleState {
  capsules: Capsule[];
  selectedCapsuleId: string | null;
  isLoading: boolean;
}

// ============================================
// Actions 接口
// ============================================

interface CapsuleActions {
  // 胶囊状态控制
  updateCapsuleStatus: (id: string, status: CapsuleStatus) => void;
  updateCapsuleInstanceCount: (id: string, count: number) => void;
  selectCapsule: (id: string | null) => void;

  // 胶囊 CRUD
  addCapsule: (capsule: Omit<Capsule, 'id'>) => void;
  removeCapsule: (id: string) => void;

  // 数据操作
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

// ============================================
// 默认数据
// ============================================

const defaultCapsules: Capsule[] = [
  {
    id: 'market',
    name: 'MarketCapsule',
    type: 'market',
    status: 'active',
    instanceCount: 12,
    description: '市场数据采集与处理',
    version: '2.0.0'
  },
  {
    id: 'signal',
    name: 'SignalCapsule',
    type: 'signal',
    status: 'active',
    instanceCount: 8,
    description: '交易信号生成',
    version: '1.8.0'
  },
  {
    id: 'risk',
    name: 'RiskCapsule',
    type: 'risk',
    status: 'active',
    instanceCount: 6,
    description: '风险管理控制',
    version: '1.5.0'
  },
  {
    id: 'execution',
    name: 'ExecutionCapsule',
    type: 'execution',
    status: 'active',
    instanceCount: 4,
    description: '订单执行引擎',
    version: '2.1.0'
  },
  {
    id: 'brain',
    name: 'BrainCapsule',
    type: 'brain',
    status: 'active',
    instanceCount: 2,
    description: '决策大脑',
    version: '1.0.0'
  },
  {
    id: 'monitor',
    name: 'MonitorCapsule',
    type: 'monitor',
    status: 'error',
    instanceCount: 1,
    description: '系统监控',
    version: '1.2.0'
  },
];

// ============================================
// Store 创建
// ============================================

export const useCapsuleStore = create<CapsuleState & CapsuleActions>()(
  persist(
    (set) => ({
      // 初始状态
      capsules: defaultCapsules,
      selectedCapsuleId: null,
      isLoading: false,

      // 胶囊状态控制
      updateCapsuleStatus: (id, status) => {
        set(state => ({
          capsules: state.capsules.map(c =>
            c.id === id ? { ...c, status } : c
          )
        }));
      },

      updateCapsuleInstanceCount: (id, count) => {
        set(state => ({
          capsules: state.capsules.map(c =>
            c.id === id ? { ...c, instanceCount: count } : c
          )
        }));
      },

      selectCapsule: (id) => {
        set({ selectedCapsuleId: id });
      },

      // 胶囊 CRUD
      addCapsule: (capsuleData) => {
        const newCapsule: Capsule = {
          ...capsuleData,
          id: `capsule_${Date.now()}`,
        };
        set(state => ({
          capsules: [...state.capsules, newCapsule]
        }));
      },

      removeCapsule: (id) => {
        set(state => ({
          capsules: state.capsules.filter(c => c.id !== id),
          selectedCapsuleId: state.selectedCapsuleId === id ? null : state.selectedCapsuleId
        }));
      },

      // 数据操作
      setLoading: (loading) => {
        set({ isLoading: loading });
      },

      reset: () => {
        set({
          capsules: defaultCapsules,
          selectedCapsuleId: null,
          isLoading: false
        });
      },
    }),
    {
      name: 'nemt-capsule-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        capsules: state.capsules,
      })
    }
  )
);

// ============================================
// 选择器 (Selectors)
// ============================================

export const useCapsules = () => useCapsuleStore(state => state.capsules);

export const useSelectedCapsule = () => useCapsuleStore(state =>
  state.capsules.find(c => c.id === state.selectedCapsuleId)
);

export const useActiveCapsules = () => useCapsuleStore(state =>
  state.capsules.filter(c => c.status === 'active')
);

export const useCapsulesByType = (type: CapsuleType) => useCapsuleStore(state =>
  state.capsules.filter(c => c.type === type)
);

export const useCapsuleMetrics = () => useCapsuleStore(state => {
  const capsules = state.capsules;
  return {
    totalInstances: capsules.reduce((sum, c) => sum + c.instanceCount, 0),
    activeCount: capsules.filter(c => c.status === 'active').length,
    errorCount: capsules.filter(c => c.status === 'error').length,
    inactiveCount: capsules.filter(c => c.status === 'inactive').length,
  };
});

export const useCapsuleHealth = () => useCapsuleStore(state => {
  const capsules = state.capsules;
  const total = capsules.length;
  const healthy = capsules.filter(c => c.status === 'active').length;
  return {
    healthy,
    total,
    healthPercent: total > 0 ? Math.round((healthy / total) * 100) : 0,
    isHealthy: healthy === total,
  };
});
