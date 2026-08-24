/**
 * Copyright 2026 NEMT Lab
 *
 * 介绍页面组件
 * 展示 NEMT Simulator 平台简介和核心概念
 */

import React from 'react';
import { Container, Zap, Shield, Code, BarChart3, Layers } from 'lucide-react';

const features = [
  {
    icon: Container,
    title: '策略容器平台',
    description: 'NEMT 不生产策略，而是策略运行的容器。类似抖音平台提供基础设施，KOL/开发者提供内容。',
    color: '#8b5cf6',
  },
  {
    icon: Zap,
    title: '高速回测引擎',
    description: '基于 Go 语言构建的高性能回测引擎，支持多种时间周期和复杂策略回测。',
    color: '#f59e0b',
  },
  {
    icon: Shield,
    title: '风险管理体系',
    description: '内置多层风险控制机制，实时监控仓位、保证金和流动性风险。',
    color: '#10b981',
  },
  {
    icon: Code,
    title: 'SDK 开发工具',
    description: '完整的策略开发 SDK，支持 Python/Go/JavaScript 多语言策略编写。',
    color: '#3b82f6',
  },
  {
    icon: BarChart3,
    title: '数据分析',
    description: '强大的数据分析和可视化功能，帮助理解策略表现和市场规律。',
    color: '#ec4899',
  },
  {
    icon: Layers,
    title: '模块化架构',
    description: '采用微服务架构，各组件独立部署，支持水平扩展。',
    color: '#6366f1',
  },
];

const quickStart = [
  { step: '1', title: '创建策略', desc: '使用 SDK 或图形界面创建交易策略' },
  { step: '2', title: '回测验证', desc: '在历史数据上运行回测验证策略有效性' },
  { step: '3', title: '参数优化', desc: '使用优化器找到最佳参数组合' },
  { step: '4', title: '实盘部署', desc: '将策略部署到实盘环境运行' },
];

export function Introduction() {
  return (
    <div style={{
      padding: '32px 48px',
      maxWidth: '1200px',
      margin: '0 auto',
      overflow: 'auto',
      height: '100%',
    }}>
      {/* 头部介绍 */}
      <div style={{ marginBottom: '48px' }}>
        <h1 style={{
          fontSize: '36px',
          fontWeight: 'bold',
          background: 'linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #60a5fa 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '16px',
        }}>
          NEMT Simulator
        </h1>
        <p style={{
          fontSize: '18px',
          color: '#94a3b8',
          lineHeight: 1.6,
          maxWidth: '800px',
        }}>
          NEMT 是一个开放的策略容器平台，为量化交易者提供完整的策略开发、回测和部署环境。
          平台采用现代化的微服务架构，支持高并发、低延迟的交易执行。
        </p>
      </div>

      {/* 核心特性 */}
      <div style={{ marginBottom: '48px' }}>
        <h2 style={{
          fontSize: '20px',
          fontWeight: '600',
          color: '#e2e8f0',
          marginBottom: '24px',
        }}>
          核心特性
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px',
        }}>
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                style={{
                  padding: '24px',
                  background: '#1e293b',
                  borderRadius: '12px',
                  border: '1px solid #334155',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '10px',
                  background: `${feature.color}20`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                }}>
                  <Icon size={22} style={{ color: feature.color }} />
                </div>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  color: '#e2e8f0',
                  marginBottom: '8px',
                }}>
                  {feature.title}
                </h3>
                <p style={{
                  fontSize: '14px',
                  color: '#94a3b8',
                  lineHeight: 1.5,
                }}>
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 快速开始 */}
      <div style={{ marginBottom: '48px' }}>
        <h2 style={{
          fontSize: '20px',
          fontWeight: '600',
          color: '#e2e8f0',
          marginBottom: '24px',
        }}>
          快速开始
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '16px',
        }}>
          {quickStart.map((item) => (
            <div
              key={item.step}
              style={{
                padding: '20px',
                background: '#1e293b',
                borderRadius: '12px',
                border: '1px solid #334155',
                textAlign: 'center',
              }}
            >
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: '#8b5cf6',
                color: '#fff',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 12px',
              }}>
                {item.step}
              </div>
              <h4 style={{
                fontSize: '14px',
                fontWeight: '600',
                color: '#e2e8f0',
                marginBottom: '6px',
              }}>
                {item.title}
              </h4>
              <p style={{
                fontSize: '12px',
                color: '#64748b',
              }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 技术栈 */}
      <div>
        <h2 style={{
          fontSize: '20px',
          fontWeight: '600',
          color: '#e2e8f0',
          marginBottom: '24px',
        }}>
          技术栈
        </h2>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          {['Go', 'Python', 'TypeScript', 'React', 'Electron', 'gRPC', 'WebSocket', 'Docker', 'Kubernetes'].map((tech) => (
            <div
              key={tech}
              style={{
                padding: '8px 16px',
                background: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#94a3b8',
              }}
            >
              {tech}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
