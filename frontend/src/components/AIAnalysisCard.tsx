import React from 'react';
import { Card, Tag, Progress, Spin, List, Typography } from 'antd';
import { Bot, CheckCircle2, AlertOctagon, HelpCircle, ShieldAlert } from 'lucide-react';
import { AIAnalysis } from '../types';

const { Text, Paragraph } = Typography;

interface AIAnalysisCardProps {
  analysis?: AIAnalysis | null;
  status: 'PENDING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
}

export const AIAnalysisCard: React.FC<AIAnalysisCardProps> = ({ analysis, status }) => {
  return (
    <Card
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.85) 100%)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(139, 92, 246, 0.3)',
        borderRadius: 12,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
      bodyStyle={{ padding: '16px 20px', flex: 1, display: 'flex', flexDirection: 'column' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 6,
              background: 'rgba(139, 92, 246, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#c084fc',
            }}
          >
            <Bot size={18} />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc' }}>
              AI 智能故障根因推导 (异步旁路)
            </div>
            <div style={{ fontSize: 11, color: '#94a3b8' }}>
              专家机理知识库 + 神经网络时序推理决策
            </div>
          </div>
        </div>

        <div>
          {status === 'ANALYZING' && (
            <Tag color="processing" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Spin size="small" /> 深度推导中...
            </Tag>
          )}
          {status === 'COMPLETED' && <Tag color="purple">已完成诊断</Tag>}
          {status === 'PENDING' && <Tag color="default">等待触发</Tag>}
          {status === 'FAILED' && <Tag color="error">推导异常</Tag>}
        </div>
      </div>

      {status === 'ANALYZING' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '30px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, color: '#c084fc', fontSize: 13 }}>
            正在分析流体压力波动频谱与阀件特征参数...
          </div>
        </div>
      )}

      {status === 'COMPLETED' && analysis ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* 根因判定与置信度 */}
          <div
            style={{
              background: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.25)',
              borderRadius: 8,
              padding: '10px 14px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <span style={{ fontSize: 12, color: '#a78bfa', fontWeight: 600 }}>判定故障根因:</span>
              <span style={{ fontSize: 12, color: '#c084fc' }}>
                诊断置信度: <strong>{(analysis.confidence * 100).toFixed(0)}%</strong>
              </span>
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#f8fafc', marginBottom: 6 }}>
              {analysis.root_cause}
            </div>
            <Progress
              percent={Math.round(analysis.confidence * 100)}
              size="small"
              strokeColor={{ '0%': '#8b5cf6', '100%': '#ec4899' }}
            />
          </div>

          {/* 应急处置建议 */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.5)',
              border: '1px solid rgba(148, 163, 184, 0.1)',
              borderRadius: 8,
              padding: '10px 14px',
            }}
          >
            <div style={{ fontSize: 12, color: '#38bdf8', fontWeight: 600, marginBottom: 4 }}>
              现场处置与安全建议:
            </div>
            <Paragraph style={{ color: '#cbd5e1', fontSize: 12, marginBottom: 0 }}>
              {analysis.suggestion}
            </Paragraph>
          </div>

          {/* 现场排查步骤清单 */}
          {analysis.checklist && analysis.checklist.length > 0 && (
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>
                标准机理排查 Checklist:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {analysis.checklist.map((step, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 6,
                      fontSize: 12,
                      color: '#e2e8f0',
                      background: 'rgba(30, 41, 59, 0.4)',
                      padding: '6px 10px',
                      borderRadius: 6,
                    }}
                  >
                    <CheckCircle2 size={14} color="#10b981" style={{ marginTop: 2, flexShrink: 0 }} />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : status === 'PENDING' ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 13 }}>
          系统处于实时侦听状态，产生异常报警后立即触发异步根因推导。
        </div>
      ) : null}
    </Card>
  );
};
