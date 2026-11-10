import React, { useState, useEffect } from 'react';
import { Card, Tag, Button, Space, message, Badge } from 'antd';
import { Phone, PhoneCall, AlertTriangle, CheckCircle, Clock, FastForward, ShieldAlert } from 'lucide-react';
import { CallRecord } from '../types';
import { simulateCallAction, getCallRecords } from '../services/api';

interface CallStatusPanelProps {
  currentCall: CallRecord | null;
  onRefresh?: () => void;
}

export const CallStatusPanel: React.FC<CallStatusPanelProps> = ({ currentCall, onRefresh }) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const handleSimulate = async (action: 'ANSWER' | 'TIMEOUT' | 'REJECT') => {
    try {
      setLoadingAction(action);
      await simulateCallAction({
        call_record_id: currentCall?.id,
        action,
      });
      message.success(
        action === 'ANSWER'
          ? '模拟已接听：系统已确认告警并自动派发智能工单！'
          : '模拟未接听：状态机已判定超时并触发升级拨打！'
      );
      if (onRefresh) onRefresh();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '模拟操作执行失败');
    } finally {
      setLoadingAction(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CALLING':
        return <Badge status="processing" text={<span style={{ color: '#38bdf8', fontWeight: 600 }}>外呼拨号振铃中...</span>} />;
      case 'ANSWERED':
        return <Badge status="success" text={<span style={{ color: '#4ade80', fontWeight: 600 }}>已接听并确认</span>} />;
      case 'UNANSWERED':
      case 'TIMEOUT':
        return <Badge status="warning" text={<span style={{ color: '#fbbf24', fontWeight: 600 }}>超时未接听 (已升级)</span>} />;
      case 'ESCALATED':
        return <Badge status="error" text={<span style={{ color: '#f87171', fontWeight: 600 }}>呼叫已自动升级</span>} />;
      case 'REJECTED':
        return <Badge status="error" text={<span style={{ color: '#f87171', fontWeight: 600 }}>被叫拒接/正忙</span>} />;
      default:
        return <Badge status="default" text={<span style={{ color: '#94a3b8' }}>待机中</span>} />;
    }
  };

  return (
    <Card
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.85) 100%)',
        backdropFilter: 'blur(16px)',
        border: currentCall?.status === 'CALLING' ? '1px solid #38bdf8' : '1px solid rgba(56, 189, 248, 0.25)',
        boxShadow: currentCall?.status === 'CALLING' ? '0 0 25px rgba(56, 189, 248, 0.25)' : 'none',
        borderRadius: 12,
        transition: 'all 0.3s ease',
      }}
      bodyStyle={{ padding: '16px 20px' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 8,
              background: currentCall?.status === 'CALLING' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(100, 116, 139, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: currentCall?.status === 'CALLING' ? '#38bdf8' : '#94a3b8',
              animation: currentCall?.status === 'CALLING' ? 'pulse 1.5s infinite' : 'none',
            }}
          >
            <PhoneCall size={20} />
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 8 }}>
              外呼中心联动监控
              <Tag color={currentCall?.provider === 'aliyun' ? 'cyan' : 'purple'} style={{ margin: 0 }}>
                {currentCall?.provider === 'aliyun' ? '⚡ 阿里云语音真实外呼' : '🧪 模拟仿真外呼 (Mock)'}
              </Tag>
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              高危紧急报警直拨手机号，超时未接听自动升级至二级主管
            </div>
          </div>
        </div>

        <div>
          {getStatusBadge(currentCall?.status || 'IDLE')}
        </div>
      </div>

      {currentCall ? (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            borderRadius: 8,
            padding: '12px 16px',
            border: '1px solid rgba(148, 163, 184, 0.15)',
            display: 'grid',
            gridTemplateColumns: '1.2fr 1.5fr 1fr auto',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div>
            <div style={{ fontSize: 12, color: '#64748b' }}>当前呼叫对象</div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0' }}>
              {currentCall.contact_name}
              <Tag color={currentCall.priority === 1 ? 'blue' : 'gold'} style={{ marginLeft: 6 }}>
                第 {currentCall.priority} 优先级
              </Tag>
            </div>
          </div>

          <div>
            <div style={{ fontSize: 12, color: '#64748b' }}>真实手机号码 / 任务ID</div>
            <div style={{ fontSize: 15, fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
              {currentCall.contact_phone}
            </div>
            <div style={{ fontSize: 11, color: '#64748b' }}>
              ID: {currentCall.call_id || '等待下发'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 12, color: '#64748b' }}>通话时长 / 发起时间</div>
            <div style={{ fontSize: 14, color: '#cbd5e1' }}>
              {currentCall.duration > 0 ? `${currentCall.duration} 秒` : '振铃中...'}
            </div>
            <div style={{ fontSize: 11, color: '#64748b' }}>
              {new Date(currentCall.created_at).toLocaleTimeString()}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              type="primary"
              size="middle"
              style={{ background: '#10b981', borderColor: '#10b981' }}
              loading={loadingAction === 'ANSWER'}
              onClick={() => handleSimulate('ANSWER')}
            >
              模拟已接听
            </Button>
            <Button
              danger
              size="middle"
              loading={loadingAction === 'TIMEOUT'}
              onClick={() => handleSimulate('TIMEOUT')}
            >
              模拟超时未接听(升级)
            </Button>
          </div>
        </div>
      ) : (
        <div
          style={{
            padding: '16px',
            textAlign: 'center',
            color: '#64748b',
            background: 'rgba(15, 23, 42, 0.4)',
            borderRadius: 8,
          }}
        >
          当前无活跃外呼任务。当工厂设备产生严重报警时，系统将自动触发真实手机语音外呼。
        </div>
      )}
    </Card>
  );
};
