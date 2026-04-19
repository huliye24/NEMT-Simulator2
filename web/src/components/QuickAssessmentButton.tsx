/**
 * 快速市场评估按钮组件
 */

import React, { useState } from 'react';
import { Target, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { quickMarketAssessment } from '../services/executionService';
import { MarketPhase } from '../types/nemt';

interface QuickAssessmentButtonProps {
  onAssessmentComplete?: (result: { recommendation: string; reason: string; positionSize: number }) => void;
}

export const QuickAssessmentButton: React.FC<QuickAssessmentButtonProps> = ({ onAssessmentComplete }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    recommendation: 'long' | 'short' | 'watch';
    reason: string;
    positionSize: number;
  } | null>(null);

  const handleAssess = () => {
    setLoading(true);
    
    // 模拟评估
    setTimeout(() => {
      // 随机生成评估结果用于演示
      const dci = 0.5 + Math.random() * 0.3;
      const vortexMaturity = Math.floor(Math.random() * 20);
      const phases = [
        MarketPhase.PHASE_A_NOISE,
        MarketPhase.PHASE_B_VORTEX,
        MarketPhase.PHASE_C_RESONANCE,
        MarketPhase.PHASE_D_TREND
      ];
      const marketPhase = phases[Math.floor(Math.random() * 4)];
      const spectralWidth = 0.01 + Math.random() * 0.03;
      const noiseLevel = 0.05 + Math.random() * 0.15;
      const macroScore = Math.floor(Math.random() * 5) + 5;
      const onchainScore = Math.floor(Math.random() * 5) + 5;
      
      const assessment = quickMarketAssessment(
        dci,
        vortexMaturity,
        marketPhase,
        spectralWidth,
        noiseLevel,
        macroScore,
        onchainScore
      );
      
      setResult(assessment);
      setLoading(false);
      
      if (onAssessmentComplete) {
        onAssessmentComplete(assessment);
      }
    }, 500);
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'long': return '#52c41a';
      case 'short': return '#ff4d4f';
      default: return '#8c8c8c';
    }
  };

  const getRecommendationIcon = (rec: string) => {
    switch (rec) {
      case 'long': return <TrendingUp size={20} />;
      case 'short': return <TrendingDown size={20} />;
      default: return <Minus size={20} />;
    }
  };

  const getRecommendationLabel = (rec: string) => {
    switch (rec) {
      case 'long': return '建议做多';
      case 'short': return '建议做空';
      default: return '观望';
    }
  };

  return (
    <div style={{ marginTop: '16px' }}>
      <button
        onClick={handleAssess}
        disabled={loading}
        style={{
          width: '100%',
          padding: '12px 16px',
          border: 'none',
          borderRadius: '8px',
          background: loading ? '#f5f5f5' : 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)',
          color: loading ? '#999' : 'white',
          cursor: loading ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          fontSize: '14px',
          fontWeight: 500,
          transition: 'all 0.2s',
        }}
      >
        {loading ? (
          <>
            <div style={{
              width: '16px',
              height: '16px',
              border: '2px solid #999',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            评估中...
          </>
        ) : (
          <>
            <Target size={16} />
            快速市场评估
          </>
        )}
      </button>

      {/* 评估结果 */}
      {result && (
        <div style={{
          marginTop: '12px',
          padding: '16px',
          background: '#fafafa',
          borderRadius: '8px',
          border: '1px solid #f0f0f0',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '8px',
          }}>
            <span style={{ color: getRecommendationColor(result.recommendation) }}>
              {getRecommendationIcon(result.recommendation)}
            </span>
            <span style={{
              fontWeight: 600,
              color: getRecommendationColor(result.recommendation),
            }}>
              {getRecommendationLabel(result.recommendation)}
            </span>
            {result.positionSize > 0 && (
              <span style={{
                fontSize: '12px',
                padding: '2px 6px',
                background: getRecommendationColor(result.recommendation),
                color: 'white',
                borderRadius: '4px',
              }}>
                仓位 {result.positionSize}%
              </span>
            )}
          </div>
          <div style={{ fontSize: '12px', color: '#666', lineHeight: 1.5 }}>
            {result.reason}
          </div>
        </div>
      )}
    </div>
  );
};

export default QuickAssessmentButton;
