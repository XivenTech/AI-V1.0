import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Card, Tag, Table, Badge, notification, Alert } from 'antd';
import { AlertCircle, CheckCircle, ShieldAlert, Cpu, Activity, Clock } from 'lucide-react';
import { Device, Alarm, CallRecord, WorkOrder } from '../types';
import { getDevices, getAlarms, getCallRecords, getWorkOrders } from '../services/api';
import { useWebSocket } from '../websocket/useWebSocket';
import { TopNav } from '../components/TopNav';
import { CallStatusPanel } from '../components/CallStatusPanel';
import { DemoDrawer } from '../components/DemoDrawer';
import { AIAnalysisCard } from '../components/AIAnalysisCard';
import { WorkOrderCard } from '../components/WorkOrderCard';
import { TelemetryChart } from '../components/TelemetryChart';

export const DashboardPage: React.FC = () => {
  const [demoOpen, setDemoOpen] = useState<boolean>(false);
  const [devices, setDevices] = useState<Device[]>([]);
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [activeCall, setActiveCall] = useState<CallRecord | null>(null);
  const [activeAlarm, setActiveAlarm] = useState<Alarm | null>(null);
  const [activeWorkOrder, setActiveWorkOrder] = useState<WorkOrder | null>(null);
  const [historyTelemetry, setHistoryTelemetry] = useState<
    Array<{ time: string; pressure: number; current: number; temperature: number }>
  >([]);
  const [goldenPathMessage, setGoldenPathMessage] = useState<{ step: number; title: string; message: string } | null>(
    null
  );

  const { isConnected, subscribe } = useWebSocket();

  // 加载数据
  const refreshAll = useCallback(async () => {
    try {
      const [devList, alarmList, callList, orderList] = await Promise.all([
        getDevices(),
        getAlarms(),
        getCallRecords(),
        getWorkOrders(),
      ]);
      setDevices(devList);
      setAlarms(alarmList);
      setCalls(callList);
      setWorkOrders(orderList);

      if (alarmList.length > 0) {
        setActiveAlarm(alarmList[0]);
      } else {
        setActiveAlarm(null);
      }

      const ongoingCall = callList.find((c) => c.status === 'CALLING') || callList[0] || null;
      setActiveCall(ongoingCall);

      const ongoingOrder = orderList.find((o) => o.status !== 'CLOSED') || orderList[0] || null;
      setActiveWorkOrder(ongoingOrder);
    } catch (e) {
      console.error('加载页面数据失败:', e);
    }
  }, []);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 6000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  // 处理 WebSocket 实时推送
  useEffect(() => {
    const unsubscribe = subscribe((event) => {
      switch (event.type) {
        case 'telemetry_update': {
          const { timestamp, devices: devDatas } = event.data;
          const pump = devDatas.find((d: any) => d.code === 'PUMP-001');
          const motor = devDatas.find((d: any) => d.code === 'MOTOR-002');

          if (pump) {
            setHistoryTelemetry((prev) => {
              const next = [
                ...prev.slice(-24),
                {
                  time: timestamp,
                  pressure: pump.metrics.pressure || 0,
                  current: pump.metrics.current || motor?.metrics?.current || 42,
                  temperature: pump.metrics.temperature || motor?.metrics?.temperature || 58,
                },
              ];
              return next;
            });
          }
          break;
        }

        case 'alarm_created': {
          notification.error({
            message: `【致命告警】${event.data.title}`,
            description: `${event.data.device_name}: 遥测指标越限 (${event.data.trigger_value}${event.data.unit})，主流程正在紧急外呼！`,
            duration: 8,
          });
          refreshAll();
          break;
        }

        case 'alarm_transition':
        case 'ai_analysis_ready':
        case 'workorder_created':
        case 'workorder_update':
        case 'demo_reset': {
          refreshAll();
          break;
        }

        case 'call_status': {
          setActiveCall(event.data);
          refreshAll();
          break;
        }

        case 'golden_path_step': {
          setGoldenPathMessage(event.data);
          refreshAll();
          break;
        }

        default:
          break;
      }
    });

    return () => unsubscribe();
  }, [subscribe, refreshAll]);

  // 计算健康统计
  const alarmingCount = devices.filter((d) => d.status === 'ALARMING').length;
  const offlineCount = devices.filter((d) => d.status === 'OFFLINE').length;
  const healthRate = devices.length ? Math.round(((devices.length - alarmingCount - offlineCount) / devices.length) * 100) : 100;

  return (
    <div style={{ minHeight: '100vh', background: '#0b0f19', color: '#f8fafc', paddingBottom: 40 }}>
      {/* 顶部工业深色导航栏 */}
      <TopNav onOpenDemo={() => setDemoOpen(true)} isConnected={isConnected} />

      <main style={{ maxWidth: 1600, margin: '0 auto', padding: '20px 24px' }}>
        {/* 黄金路径执行提示栏 */}
        {goldenPathMessage && (
          <Alert
            message={
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 700, color: '#38bdf8' }}>
                  🎬 演示演练进行中 [第 {goldenPathMessage.step} 步: {goldenPathMessage.title}]
                </span>
                <span style={{ fontSize: 13, color: '#e2e8f0' }}>{goldenPathMessage.message}</span>
              </div>
            }
            type="info"
            showIcon
            closable
            onClose={() => setGoldenPathMessage(null)}
            style={{
              marginBottom: 16,
              background: 'linear-gradient(90deg, rgba(30, 58, 138, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%)',
              border: '1px solid #38bdf8',
            }}
          />
        )}

        {/* 顶部核心指标 KPI 概览 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={6}>
            <Card
              style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(56, 189, 248, 0.15)', borderRadius: 10 }}
              bodyStyle={{ padding: '14px 18px' }}
            >
              <div style={{ fontSize: 12, color: '#94a3b8' }}>工业机组监控在线</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#f8fafc', marginTop: 4 }}>
                {devices.length} <span style={{ fontSize: 13, color: '#64748b' }}>台核心机组</span>
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Card
              style={{
                background: 'rgba(15, 23, 42, 0.7)',
                border: alarmingCount > 0 ? '1px solid #ef4444' : '1px solid rgba(56, 189, 248, 0.15)',
                borderRadius: 10,
              }}
              bodyStyle={{ padding: '14px 18px' }}
            >
              <div style={{ fontSize: 12, color: '#94a3b8' }}>设备综合正常率</div>
              <div
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: healthRate < 80 ? '#ef4444' : '#10b981',
                  marginTop: 4,
                }}
              >
                {healthRate}%{' '}
                <span style={{ fontSize: 12, color: '#94a3b8' }}>
                  ({alarmingCount > 0 ? `${alarmingCount} 台严重告警` : '全线平稳运行'})
                </span>
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Card
              style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(56, 189, 248, 0.15)', borderRadius: 10 }}
              bodyStyle={{ padding: '14px 18px' }}
            >
              <div style={{ fontSize: 12, color: '#94a3b8' }}>活跃告警 / 待处理</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: alarmingCount > 0 ? '#f59e0b' : '#38bdf8', marginTop: 4 }}>
                {alarms.filter((a) => a.status !== 'CLOSED').length}{' '}
                <span style={{ fontSize: 13, color: '#64748b' }}>起未闭环</span>
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Card
              style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(56, 189, 248, 0.15)', borderRadius: 10 }}
              bodyStyle={{ padding: '14px 18px' }}
            >
              <div style={{ fontSize: 12, color: '#94a3b8' }}>电话外呼闭环率</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#38bdf8', marginTop: 4 }}>
                100% <span style={{ fontSize: 12, color: '#10b981' }}>(双优先级超时升级)</span>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 核心第一区：实时外呼状态监控浮窗面板 */}
        <div style={{ marginBottom: 16 }}>
          <CallStatusPanel currentCall={activeCall} onRefresh={refreshAll} />
        </div>

        {/* 核心第二区：左侧遥测与设备列表 + 右侧 AI 与工单 */}
        <Row gutter={[16, 16]}>
          {/* 左侧：物理曲线与设备工况列表 */}
          <Col xs={24} lg={14}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* ECharts 遥测折线图 */}
              <TelemetryChart historyData={historyTelemetry} />

              {/* 接入设备工况卡片列表 */}
              <Card
                style={{
                  background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.85) 100%)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: 12,
                }}
                bodyStyle={{ padding: '16px 20px' }}
              >
                <div style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Cpu size={18} color="#38bdf8" />
                  接入工业机组实时状态 (Adapter 接入层)
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {devices.map((dev) => (
                    <div
                      key={dev.id}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1.2fr 1fr 1.5fr 1fr',
                        alignItems: 'center',
                        background: dev.status === 'ALARMING' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                        border: dev.status === 'ALARMING' ? '1px solid #ef4444' : '1px solid rgba(148, 163, 184, 0.1)',
                        padding: '12px 16px',
                        borderRadius: 8,
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9' }}>{dev.name}</div>
                        <div style={{ fontSize: 11, color: '#64748b' }}>{dev.code} • {dev.location}</div>
                      </div>

                      <div>
                        {dev.status === 'RUNNING' && <Badge status="success" text={<span style={{ color: '#4ade80' }}>运行正常</span>} />}
                        {dev.status === 'ALARMING' && <Badge status="error" text={<span style={{ color: '#f87171', fontWeight: 600 }}>越限告警中</span>} />}
                        {dev.status === 'OFFLINE' && <Badge status="default" text={<span style={{ color: '#94a3b8' }}>通讯离线</span>} />}
                      </div>

                      <div style={{ fontSize: 12, color: '#cbd5e1' }}>
                        {dev.metrics?.pressure !== undefined && (
                          <span style={{ marginRight: 12 }}>
                            压力: <strong style={{ color: (dev.metrics.pressure < 18) ? '#f87171' : '#38bdf8' }}>{dev.metrics.pressure} MPa</strong>
                          </span>
                        )}
                        {dev.metrics?.current !== undefined && dev.metrics.current > 0 && (
                          <span style={{ marginRight: 12 }}>
                            电流: <strong style={{ color: (dev.metrics.current > 75) ? '#f87171' : '#f59e0b' }}>{dev.metrics.current} A</strong>
                          </span>
                        )}
                        {dev.metrics?.temperature !== undefined && (
                          <span>
                            温度: <strong style={{ color: (dev.metrics.temperature > 90) ? '#f87171' : '#ec4899' }}>{dev.metrics.temperature} ℃</strong>
                          </span>
                        )}
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <Tag color={dev.status === 'ALARMING' ? 'red' : 'blue'}>
                          {dev.type}
                        </Tag>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </Col>

          {/* 右侧：当前活跃告警 + AI 根因推导 + 智能派单 */}
          <Col xs={24} lg={10}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* 当前告警高亮展示 */}
              {activeAlarm ? (
                <Card
                  style={{
                    background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
                    border: '1px solid #ef4444',
                    boxShadow: '0 0 20px rgba(239, 68, 68, 0.25)',
                    borderRadius: 12,
                  }}
                  bodyStyle={{ padding: '16px 20px' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <ShieldAlert size={18} color="#ef4444" />
                      <span style={{ fontSize: 15, fontWeight: 700, color: '#fca5a5' }}>
                        [{activeAlarm.level}] {activeAlarm.title}
                      </span>
                    </div>
                    <Tag color="red">{activeAlarm.status}</Tag>
                  </div>
                  <div style={{ fontSize: 13, color: '#e2e8f0', marginBottom: 8 }}>
                    {activeAlarm.message}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', display: 'flex', gap: 12 }}>
                    <span>设备: {activeAlarm.device?.name || '主泵'}</span>
                    <span>触发值: {activeAlarm.trigger_value} {activeAlarm.unit}</span>
                    <span>安全阈值: {activeAlarm.threshold} {activeAlarm.unit}</span>
                  </div>
                </Card>
              ) : (
                <Card
                  style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(148, 163, 184, 0.15)', borderRadius: 12 }}
                  bodyStyle={{ padding: '16px 20px', textAlign: 'center', color: '#10b981' }}
                >
                  <CheckCircle size={20} style={{ display: 'inline', marginRight: 6 }} />
                  全厂当前无严重活动告警，系统运行平稳。
                </Card>
              )}

              {/* AI 根因推导卡片 */}
              <AIAnalysisCard
                analysis={activeAlarm?.ai_analysis}
                status={activeAlarm?.ai_analysis_status || 'PENDING'}
              />

              {/* 智能维修工单卡片 */}
              <WorkOrderCard workOrder={activeWorkOrder} onRefresh={refreshAll} />
            </div>
          </Col>
        </Row>
      </main>

      {/* 🎬 演示模式 (Demo Mode) 控制台抽屉 */}
      <DemoDrawer open={demoOpen} onClose={() => setDemoOpen(false)} onRefreshAll={refreshAll} />
    </div>
  );
};
