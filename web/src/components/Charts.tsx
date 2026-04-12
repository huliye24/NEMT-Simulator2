/**
 * NEMT可视化组件
 */

import React, { useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { ExperimentResult, NoiseScanResult, NonlinearScanResult } from '../types/nemt';

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface SpectrumChartProps {
  freqs: Float64Array;
  spectrum: Float64Array;
  peakFrequencies?: number[];
  title?: string;
}

export const SpectrumChart: React.FC<SpectrumChartProps> = ({
  freqs,
  spectrum,
  peakFrequencies = [],
  title = '频谱分析'
}) => {
  const labels = Array.from(freqs).map(f => f.toFixed(3));
  const data = {
    labels,
    datasets: [
      {
        label: '振幅谱',
        data: Array.from(spectrum),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: true,
        text: title,
        font: { size: 16 }
      },
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => `振幅: ${context.parsed.y.toFixed(4)}`
        }
      }
    },
    scales: {
      x: {
        title: { display: true, text: '频率' },
        ticks: { maxTicksLimit: 10 }
      },
      y: {
        title: { display: true, text: '振幅' },
        beginAtZero: true
      }
    }
  };

  return (
    <div style={{ height: '300px' }}>
      <Line options={options} data={data} />
    </div>
  );
};

interface EvolutionChartProps {
  evolution: number[][];
  title?: string;
}

export const EvolutionChart: React.FC<EvolutionChartProps> = ({
  evolution,
  title = '振幅演化'
}) => {
  const datasets = evolution.map((amp, idx) => ({
    label: `t=${idx}`,
    data: amp,
    borderColor: `rgba(${55 + idx * 2}, ${100 + idx}, ${200 - idx}, 0.5)`,
    borderWidth: 0.5,
    pointRadius: 0,
    fill: false
  }));

  const data = {
    labels: Array.from({ length: evolution[0]?.length || 0 }, (_, i) => i),
    datasets
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: true,
        text: title,
        font: { size: 16 }
      },
      legend: { display: false }
    },
    scales: {
      x: {
        title: { display: true, text: '空间位置' }
      },
      y: {
        title: { display: true, text: '|ψ|' },
        beginAtZero: true
      }
    }
  };

  return (
    <div style={{ height: '300px' }}>
      <Line options={options} data={data} />
    </div>
  );
};

interface SpectralWidthChartProps {
  data: { x: number; y: number }[];
  label: string;
  color: string;
  title?: string;
}

export const SpectralWidthChart: React.FC<SpectralWidthChartProps> = ({
  data,
  label,
  color,
  title = '谱宽变化'
}) => {
  const chartData = {
    labels: data.map(d => d.x.toFixed(2)),
    datasets: [
      {
        label,
        data: data.map(d => d.y),
        borderColor: color,
        backgroundColor: `${color}33`,
        fill: true,
        tension: 0.4
      }
    ]
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: true,
        text: title,
        font: { size: 16 }
      },
      legend: { display: false }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  return (
    <div style={{ height: '250px' }}>
      <Line options={options} data={chartData} />
    </div>
  );
};

interface NoiseScanChartProps {
  results: NoiseScanResult;
}

export const NoiseScanChart: React.FC<NoiseScanChartProps> = ({ results }) => {
  // 谱宽随噪声变化
  const widthData = {
    labels: results.noiseLevels.map(n => n.toFixed(1)),
    datasets: [
      {
        label: '谱宽',
        data: results.spectralWidths,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  // 共振峰数量
  const resonanceData = {
    labels: results.noiseLevels.map(n => n.toFixed(1)),
    datasets: [
      {
        label: '共振峰数量',
        data: results.resonanceCounts,
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
      <div style={{ height: '250px' }}>
        <Line options={options} data={widthData} />
        <p style={{ textAlign: 'center', fontSize: '14px', marginTop: '8px' }}>谱宽 vs 噪声水平</p>
      </div>
      <div style={{ height: '250px' }}>
        <Line options={options} data={resonanceData} />
        <p style={{ textAlign: 'center', fontSize: '14px', marginTop: '8px' }}>共振峰数量 vs 噪声水平</p>
      </div>
    </div>
  );
};

interface NonlinearScanChartProps {
  results: NonlinearScanResult;
}

export const NonlinearScanChart: React.FC<NonlinearScanChartProps> = ({ results }) => {
  const widthData = {
    labels: results.betaValues.map(b => b.toFixed(1)),
    datasets: [
      {
        label: '谱宽',
        data: results.spectralWidths,
        borderColor: 'rgb(153, 102, 255)',
        backgroundColor: 'rgba(153, 102, 255, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const resonanceData = {
    labels: results.betaValues.map(b => b.toFixed(1)),
    datasets: [
      {
        label: '共振峰数量',
        data: results.resonanceCounts,
        borderColor: 'rgb(255, 159, 64)',
        backgroundColor: 'rgba(255, 159, 64, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
      <div style={{ height: '250px' }}>
        <Line options={options} data={widthData} />
        <p style={{ textAlign: 'center', fontSize: '14px', marginTop: '8px' }}>谱宽 vs 非线性强度 β</p>
      </div>
      <div style={{ height: '250px' }}>
        <Line options={options} data={resonanceData} />
        <p style={{ textAlign: 'center', fontSize: '14px', marginTop: '8px' }}>共振峰数量 vs β</p>
      </div>
    </div>
  );
};

interface ResultSummaryProps {
  result: ExperimentResult;
}

export const ResultSummary: React.FC<ResultSummaryProps> = ({ result }) => {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
      gap: '16px',
      padding: '16px',
      background: '#f5f5f5',
      borderRadius: '8px'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
          {result.spectralWidth.toFixed(6)}
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>谱宽</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
          {result.resonance.numPeaks}
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>共振峰</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
          {result.meanFrequency.toFixed(4)}
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>平均频率</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#eb2f96' }}>
          {result.evolution?.length || 0}
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>演化步数</div>
      </div>
    </div>
  );
};

interface ParameterDisplayProps {
  params: ExperimentResult['params'];
}

export const ParameterDisplay: React.FC<ParameterDisplayProps> = ({ params }) => {
  return (
    <div style={{
      display: 'flex',
      gap: '24px',
      padding: '12px 16px',
      background: '#fff',
      borderRadius: '6px',
      border: '1px solid #d9d9d9'
    }}>
      <div>
        <span style={{ color: '#666', fontSize: '12px' }}>α (扩散系数)</span>
        <div style={{ fontSize: '16px', fontWeight: 500 }}>{params.alpha}</div>
      </div>
      <div>
        <span style={{ color: '#666', fontSize: '12px' }}>β (非线性)</span>
        <div style={{ fontSize: '16px', fontWeight: 500 }}>{params.beta}</div>
      </div>
      <div>
        <span style={{ color: '#666', fontSize: '12px' }}>η (噪声)</span>
        <div style={{ fontSize: '16px', fontWeight: 500 }}>{params.noiseLevel}</div>
      </div>
      <div>
        <span style={{ color: '#666', fontSize: '12px' }}>步数</span>
        <div style={{ fontSize: '16px', fontWeight: 500 }}>{params.steps}</div>
      </div>
    </div>
  );
};
