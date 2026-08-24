/**
 * Copyright 2026 NEMT Lab
 *
 * 胶囊状态栏组件
 */

import React from 'react';
import { Layers } from 'lucide-react';
import { useCapsules } from '../../stores';

export function CapsuleBar() {
  const capsules = useCapsules();

  return (
    <div style={{
      background: '#1e293b',
      borderBottom: '1px solid #334155',
      padding: '12px 32px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <Layers size={16} style={{ color: '#8b5cf6' }} />
        <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '500' }}>
          胶囊容器
        </span>
      </div>
      <div style={{ display: 'flex', gap: '12px' }}>
        {capsules.map(capsule => (
          <div key={capsule.id} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            background: capsule.status === 'active' ? '#10b98115' : '#0f172a',
            border: `1px solid ${capsule.status === 'active' ? '#10b98144' : '#334155'}`,
            borderRadius: '8px',
            cursor: 'pointer'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: capsule.status === 'active' ? '#10b981' :
                          capsule.status === 'error' ? '#ef4444' : '#64748b'
            }} />
            <div>
              <div style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: '500' }}>
                {capsule.name}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                {capsule.instanceCount} 实例
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
