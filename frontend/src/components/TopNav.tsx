import React, { useState, useEffect } from 'react';
import { Button, Tag, Badge, Tooltip } from 'antd';
import { PlayCircle, Cpu, Wifi, Phone, ShieldCheck, Activity } from 'lucide-react';

interface TopNavProps {
  onOpenDemo: () => void;
  isConnected: boolean;
}

export const TopNav: React.FC<TopNavProps> = ({ onOpenDemo, isConnected }) => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString());
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header
      style={{
        height: 64,
        background: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(56, 189, 248, 0.25)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
      }}
    >
      {/* 品牌与标题 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 8,
            background: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 0 15px rgba(56, 189, 248, 0.5)',
          }}
        >
          <Cpu size={22} />
        </div>
        <div>
          <div
            style={{
              fontSize: 18,
              fontWeight: 800,
              fontFamily: 'Inter, sans-serif',
              letterSpacing: '0.5px',
              background: 'linear-gradient(90deg, #f8fafc 0%, #38bdf8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AI 无人值守工厂智能告警与自动处置平台
          </div>
          <div style={{ fontSize: 11, color: '#64748b', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>UNATTENDED FACTORY ORCHESTRATION</span>
            <span>•</span>
            <span style={{ color: '#38bdf8', fontWeight: 600 }}>V1.0 工业演示版</span>
          </div>
        </div>
      </div>

      {/* 中间状态条 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(30, 41, 59, 0.5)', padding: '6px 14px', borderRadius: 20, border: '1px solid rgba(148, 163, 184, 0.15)' }}>
          <Activity size={14} color="#38bdf8" />
          <span style={{ fontSize: 12, color: '#94a3b8' }}>系统时间:</span>
          <span style={{ fontSize: 13, fontFamily: 'monospace', fontWeight: 700, color: '#f8fafc' }}>
            {timeStr || '03:28:15'}
          </span>
          <Tag color="cyan" style={{ margin: 0, fontSize: 11, lineHeight: '18px', height: 18, padding: '0 6px' }}>
            无人值守模式
          </Tag>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Badge status={isConnected ? 'success' : 'error'} />
          <span style={{ fontSize: 12, color: isConnected ? '#4ade80' : '#f87171' }}>
            {isConnected ? '物联网总线在线' : '总线重连中...'}
          </span>
        </div>
      </div>

      {/* 右侧演示模式控制台唤起按钮 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button
          type="primary"
          size="middle"
          onClick={onOpenDemo}
          style={{
            background: 'linear-gradient(135deg, #2563eb 0%, #0284c7 100%)',
            borderColor: '#38bdf8',
            boxShadow: '0 0 15px rgba(37, 99, 235, 0.4)',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            height: 38,
            padding: '0 18px',
          }}
        >
          <PlayCircle size={18} />
          🎬 演示模式 (Demo Mode)
        </Button>
      </div>
    </header>
  );
};
