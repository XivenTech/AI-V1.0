import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from 'antd';
import { Activity } from 'lucide-react';

interface TelemetryPoint {
  time: string;
  pressure: number;
  current: number;
  temperature: number;
}

interface TelemetryChartProps {
  historyData: TelemetryPoint[];
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({ historyData }) => {
  const option = useMemo(() => {
    const times = historyData.map((d) => d.time);
    const pressures = historyData.map((d) => d.pressure);
    const currents = historyData.map((d) => d.current);
    const temperatures = historyData.map((d) => d.temperature);

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderColor: '#38bdf8',
        textStyle: { color: '#f8fafc', fontSize: 12 },
      },
      legend: {
        data: ['主泵压力 (MPa)', '电机电流 (A)', '轴承温度 (℃)'],
        textStyle: { color: '#94a3b8' },
        top: 0,
        right: 10,
      },
      grid: {
        top: 40,
        left: '3%',
        right: '4%',
        bottom: '8%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: times,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#64748b', fontSize: 11 },
      },
      yAxis: [
        {
          type: 'value',
          name: '压力 (MPa)',
          nameTextStyle: { color: '#38bdf8', fontSize: 11 },
          min: 0,
          max: 35,
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)', type: 'dashed' } },
          axisLabel: { color: '#38bdf8' },
        },
        {
          type: 'value',
          name: '电流/温度',
          nameTextStyle: { color: '#f59e0b', fontSize: 11 },
          min: 0,
          max: 120,
          splitLine: { show: false },
          axisLabel: { color: '#f59e0b' },
        },
      ],
      series: [
        {
          name: '主泵压力 (MPa)',
          type: 'line',
          smooth: true,
          showSymbol: false,
          yAxisIndex: 0,
          data: pressures,
          itemStyle: { color: '#38bdf8' },
          lineStyle: { width: 3, shadowColor: 'rgba(56, 189, 248, 0.5)', shadowBlur: 10 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(56, 189, 248, 0.35)' },
                { offset: 1, color: 'rgba(56, 189, 248, 0.0)' },
              ],
            },
          },
          markLine: {
            symbol: 'none',
            data: [
              {
                yAxis: 18.0,
                name: '压力下限阈值 (18.0 MPa)',
                lineStyle: { color: '#ef4444', width: 2, type: 'dashed' },
                label: { formatter: 'P1阈值 18.0 MPa', color: '#fca5a5', position: 'insideEndTop' },
              },
            ],
          },
        },
        {
          name: '电机电流 (A)',
          type: 'line',
          smooth: true,
          showSymbol: false,
          yAxisIndex: 1,
          data: currents,
          itemStyle: { color: '#f59e0b' },
          lineStyle: { width: 2 },
        },
        {
          name: '轴承温度 (℃)',
          type: 'line',
          smooth: true,
          showSymbol: false,
          yAxisIndex: 1,
          data: temperatures,
          itemStyle: { color: '#ec4899' },
          lineStyle: { width: 2 },
        },
      ],
    };
  }, [historyData]);

  return (
    <Card
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.85) 100%)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        borderRadius: 12,
      }}
      bodyStyle={{ padding: '16px 20px' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <Activity size={18} color="#38bdf8" />
        <span style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc' }}>
          关键机组物理指标实时遥测趋势 (1.5s 连续流采样)
        </span>
      </div>
      <ReactECharts option={option} style={{ height: 260, width: '100%' }} />
    </Card>
  );
};
