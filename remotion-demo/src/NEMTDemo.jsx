import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from 'remotion';

const FONT =
  '"Microsoft YaHei", "PingFang SC", "Noto Sans SC", system-ui, sans-serif';

// 三个顶部 KPI 指标
const KPIS = [
  {label: '日完成订单', value: 1284, unit: '单', color: '#4f8cff', decimals: 0},
  {label: '准点率', value: 96.4, unit: '%', color: '#28c76f', decimals: 1},
  {label: '平均等待', value: 18, unit: 'min', color: '#ffb020', decimals: 0},
];

// 按小时分布的运单量
const BARS = [
  {hour: '06', v: 42},
  {hour: '08', v: 118},
  {hour: '10', v: 164},
  {hour: '12', v: 132},
  {hour: '14', v: 148},
  {hour: '16', v: 176},
  {hour: '18', v: 96},
  {hour: '20', v: 54},
];

const MAX_BAR = Math.max(...BARS.map((b) => b.v));

const KpiCard = ({item, index, progress}) => {
  const shown = item.value * progress;
  const text = shown.toFixed(item.decimals);

  return (
    <div
      style={{
        flex: 1,
        padding: '40px 48px',
        marginRight: index === KPIS.length - 1 ? 0 : 32,
        borderRadius: 24,
        backgroundColor: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.10)',
        borderTop: `6px solid ${item.color}`,
        opacity: progress,
        transform: `translateY(${(1 - progress) * 40}px)`,
      }}
    >
      <div style={{fontSize: 30, color: 'rgba(255,255,255,0.62)', letterSpacing: 2}}>
        {item.label}
      </div>
      <div style={{display: 'flex', alignItems: 'baseline', marginTop: 18}}>
        <span
          style={{
            fontSize: 92,
            fontWeight: 700,
            color: item.color,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {text}
        </span>
        <span style={{fontSize: 34, color: 'rgba(255,255,255,0.55)', marginLeft: 12}}>
          {item.unit}
        </span>
      </div>
    </div>
  );
};

export const NEMTDemo = () => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();

  // 标题：先弹入，末尾淡出
  const titleIn = spring({
    frame,
    fps,
    config: {damping: 200, mass: 0.6},
    durationInFrames: 26,
  });
  const titleOut = interpolate(frame, [215, 238], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // KPI 逐个错峰弹入
  const kpiProgress = KPIS.map((_, i) =>
    spring({
      frame: frame - 14 - i * 8,
      fps,
      config: {damping: 200, mass: 0.5},
      durationInFrames: 34,
    })
  );

  // 柱状图：整体从左向右生长
  const chartIn = interpolate(frame, [40, 130], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const subtitleOpacity = interpolate(frame, [16, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#080c18',
        fontFamily: FONT,
        color: '#ffffff',
      }}
    >
      {/* 背景光斑 */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(1200px 700px at 18% -10%, rgba(79,140,255,0.28), transparent 60%),' +
            'radial-gradient(900px 600px at 90% 110%, rgba(40,199,111,0.20), transparent 60%)',
        }}
      />

      <AbsoluteFill
        style={{
          padding: '90px 110px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* 标题区 */}
        <div style={{opacity: titleIn * titleOut}}>
          <div
            style={{
              fontSize: 30,
              letterSpacing: 8,
              color: '#4f8cff',
              transform: `translateY(${(1 - titleIn) * -30}px)`,
            }}
          >
            NEMT · DISPATCH OVERVIEW
          </div>
          <div
            style={{
              fontSize: 76,
              fontWeight: 700,
              marginTop: 14,
              letterSpacing: 3,
              transform: `translateY(${(1 - titleIn) * 40}px)`,
            }}
          >
            非紧急医疗转运 · 调度概览
          </div>
          <div
            style={{
              fontSize: 28,
              color: 'rgba(255,255,255,0.6)',
              marginTop: 18,
              opacity: subtitleOpacity,
            }}
          >
            Remotion 4.0.536 · 1920×1080 · 30fps
          </div>
        </div>

        {/* KPI 区 */}
        <div style={{display: 'flex', marginTop: 64}}>
          {KPIS.map((item, i) => (
            <KpiCard key={item.label} item={item} index={i} progress={kpiProgress[i]} />
          ))}
        </div>

        {/* 柱状图区 */}
        <div
          style={{
            marginTop: 64,
            flex: 1,
            padding: '44px 48px',
            borderRadius: 24,
            backgroundColor: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.10)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{fontSize: 28, color: 'rgba(255,255,255,0.62)'}}>
            分时运单量分布
          </div>

          <div style={{flex: 1, display: 'flex', alignItems: 'flex-end', marginTop: 28}}>
            {BARS.map((b, i) => {
              const barProgress =
                chartIn * interpolate(frame, [40 + i * 10, 70 + i * 10], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                  easing: Easing.out(Easing.cubic),
                });
              const h = (b.v / MAX_BAR) * 220 * barProgress;

              return (
                <div
                  key={b.hour}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                  }}
                >
                  <div
                    style={{
                      fontSize: 26,
                      color: 'rgba(255,255,255,0.75)',
                      marginBottom: 10,
                      fontVariantNumeric: 'tabular-nums',
                      opacity: barProgress,
                    }}
                  >
                    {Math.round(b.v * barProgress)}
                  </div>
                  <div
                    style={{
                      width: 74,
                      height: Math.max(h, 0),
                      borderRadius: '10px 10px 0 0',
                      background:
                        'linear-gradient(180deg, #4f8cff 0%, rgba(79,140,255,0.25) 100%)',
                    }}
                  />
                  <div
                    style={{
                      marginTop: 14,
                      fontSize: 24,
                      color: 'rgba(255,255,255,0.5)',
                    }}
                  >
                    {b.hour}:00
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 底部进度条 */}
        <div
          style={{
            marginTop: 40,
            height: 6,
            borderRadius: 3,
            backgroundColor: 'rgba(255,255,255,0.10)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${interpolate(frame, [0, 239], [0, 100], {
                extrapolateRight: 'clamp',
              })}%`,
              background: 'linear-gradient(90deg, #4f8cff, #28c76f)',
            }}
          />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
