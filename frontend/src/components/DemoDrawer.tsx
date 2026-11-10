import React, { useState, useEffect } from 'react';
import { Drawer, Button, Space, Card, Form, Input, Switch, Divider, message, Alert, Radio, Typography, Steps } from 'antd';
import { Play, RotateCcw, Flame, Zap, WifiOff, Phone, Settings, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { triggerDemoScenario, startGoldenPath, getContacts, updateContact, getCallConfig, switchCallProvider, triggerCall } from '../services/api';
import { Contact } from '../types';

const { Text, Paragraph } = Typography;

interface DemoDrawerProps {
  open: boolean;
  onClose: () => void;
  onRefreshAll?: () => void;
}

export const DemoDrawer: React.FC<DemoDrawerProps> = ({ open, onClose, onRefreshAll }) => {
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [goldenPathRunning, setGoldenPathRunning] = useState<boolean>(false);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [currentProvider, setCurrentProvider] = useState<'aliyun' | 'mock'>('mock');
  const [hasAliyunAK, setHasAliyunAK] = useState<boolean>(false);
  const [testPhone, setTestPhone] = useState<string>('');
  const [form] = Form.useForm();

  const loadData = async () => {
    try {
      const [cts, cfg] = await Promise.all([getContacts(), getCallConfig()]);
      setContacts(cts);
      setCurrentProvider(cfg.current_provider as any);
      setHasAliyunAK(cfg.has_aliyun_credentials);

      const primary = cts.find((c) => c.priority === 1);
      const secondary = cts.find((c) => c.priority === 2);
      form.setFieldsValue({
        primaryName: primary?.name || '张工',
        primaryPhone: primary?.phone || '13800000001',
        secondaryName: secondary?.name || '李主管',
        secondaryPhone: secondary?.phone || '13900000002',
      });
      if (primary) setTestPhone(primary.phone);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open]);

  const handleScenario = async (scenario: 'HYDRAULIC_LEAK' | 'MOTOR_OVERHEAT' | 'DEVICE_OFFLINE' | 'RESET') => {
    try {
      setLoadingScenario(scenario);
      await triggerDemoScenario(scenario);
      message.success(
        scenario === 'RESET'
          ? '系统已成功复位至初始健康工况！'
          : `已成功注入故障场景 [${scenario}]！大屏即将产生告警并在后台发起流程。`
      );
      if (onRefreshAll) onRefreshAll();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '场景触发失败');
    } finally {
      setLoadingScenario(null);
    }
  };

  const handleGoldenPath = async () => {
    try {
      setGoldenPathRunning(true);
      await startGoldenPath();
      message.success('🎬 3 分钟黄金路径闭环演示已启动！大屏将自动推进全流程。');
      onClose();
      if (onRefreshAll) onRefreshAll();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '启动黄金路径失败');
    } finally {
      setGoldenPathRunning(false);
    }
  };

  const handleSaveContacts = async (values: any) => {
    try {
      const primary = contacts.find((c) => c.priority === 1);
      const secondary = contacts.find((c) => c.priority === 2);

      if (primary) {
        await updateContact(primary.id, {
          name: values.primaryName,
          phone: values.primaryPhone,
          role: primary.role,
        });
      }
      if (secondary) {
        await updateContact(secondary.id, {
          name: values.secondaryName,
          phone: values.secondaryPhone,
          role: secondary.role,
        });
      }
      message.success('现场演示手机号已更新！下一次告警将直接呼叫该真实号码。');
      loadData();
    } catch (e: any) {
      message.error('更新手机号失败');
    }
  };

  const handleSwitchProvider = async (p: 'aliyun' | 'mock') => {
    try {
      await switchCallProvider(p);
      setCurrentProvider(p);
      message.success(`外呼通道已切换为: ${p === 'aliyun' ? '阿里云真实外呼' : '本地模拟Mock'}`);
    } catch (e) {
      message.error('切换外呼通道失败');
    }
  };

  const handleTestCall = async () => {
    if (!testPhone) {
      message.warning('请输入测试手机号');
      return;
    }
    try {
      message.loading({ content: `正在向 ${testPhone} 发起外呼测试...`, key: 'callTest' });
      await triggerCall({
        phone: testPhone,
        contact_name: '现场演示嘉宾',
        provider: currentProvider,
      });
      message.success({ content: `已向手机号 ${testPhone} 成功发起语音外呼，请留意手机来电！`, key: 'callTest' });
    } catch (e: any) {
      message.error({ content: e.response?.data?.detail || '拨打失败', key: 'callTest' });
    }
  };

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#f8fafc', fontSize: 16 }}>
          <span>🎬 演示模式控制台 (Demo Console)</span>
        </div>
      }
      placement="right"
      width={480}
      onClose={onClose}
      open={open}
      styles={{
        body: {
          background: '#0f172a',
          color: '#f8fafc',
          padding: '20px',
        },
        header: {
          background: '#1e293b',
          borderBottom: '1px solid rgba(148, 163, 184, 0.15)',
        },
      }}
    >
      {/* 1. 3分钟黄金路径一键启动 */}
      <Card
        style={{
          background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.6) 0%, rgba(30, 41, 59, 0.8) 100%)',
          borderColor: '#3b82f6',
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 700, color: '#93c5fd', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Play size={18} />
          甲方现场 3 分钟黄金路径闭环演练
        </div>
        <Paragraph style={{ color: '#cbd5e1', fontSize: 13, marginBottom: 14 }}>
          点击后系统将全自动运行：<strong>注入液压失压 ➔ 产生 P1 告警 ➔ 发起真实呼叫 ➔ 模拟超时升级至主管 ➔ 主管接听 ➔ 派发智能工单 ➔ 闭环归档</strong>。
        </Paragraph>
        <Button
          type="primary"
          size="large"
          block
          style={{ background: '#2563eb', fontWeight: 600 }}
          loading={goldenPathRunning}
          onClick={handleGoldenPath}
        >
          立即启动 3 分钟闭环演示
        </Button>
      </Card>

      {/* 2. 单点故障场景注入 */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 10 }}>
          单点故障场景动态注入
        </div>
        <Space direction="vertical" style={{ width: '100%' }} size={10}>
          <Button
            block
            size="large"
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              borderColor: '#ef4444',
              color: '#fca5a5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
            loading={loadingScenario === 'HYDRAULIC_LEAK'}
            onClick={() => handleScenario('HYDRAULIC_LEAK')}
          >
            <Flame size={18} />
            [故障1] 模拟主泵液压失压泄漏 (P1 级严重告警)
          </Button>

          <Button
            block
            size="large"
            style={{
              background: 'rgba(245, 158, 11, 0.15)',
              borderColor: '#f59e0b',
              color: '#fcd34d',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
            loading={loadingScenario === 'MOTOR_OVERHEAT'}
            onClick={() => handleScenario('MOTOR_OVERHEAT')}
          >
            <Zap size={18} />
            [故障2] 模拟粗轧电机过载超温 (P2 级严重告警)
          </Button>

          <Button
            block
            size="large"
            style={{
              background: 'rgba(148, 163, 184, 0.15)',
              borderColor: '#64748b',
              color: '#cbd5e1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
            loading={loadingScenario === 'DEVICE_OFFLINE'}
            onClick={() => handleScenario('DEVICE_OFFLINE')}
          >
            <WifiOff size={18} />
            [故障3] 模拟加工中心通讯中断离线 (P3 级告警)
          </Button>

          <Button
            block
            size="middle"
            style={{
              background: 'rgba(16, 185, 129, 0.15)',
              borderColor: '#10b981',
              color: '#6ee7b7',
              marginTop: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
            loading={loadingScenario === 'RESET'}
            onClick={() => handleScenario('RESET')}
          >
            <RotateCcw size={16} />
            一键复位所有设备至初始健康工况
          </Button>
        </Space>
      </div>

      <Divider style={{ borderColor: 'rgba(148, 163, 184, 0.15)' }} />

      {/* 3. 呼叫通道切换与配置 */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 10 }}>
          外呼线路模式选择
        </div>
        <Radio.Group
          value={currentProvider}
          onChange={(e) => handleSwitchProvider(e.target.value)}
          style={{ width: '100%', display: 'flex', gap: 10, marginBottom: 12 }}
        >
          <Radio.Button value="aliyun" style={{ flex: 1, textAlign: 'center' }}>
            ⚡ 阿里云真实外呼
          </Radio.Button>
          <Radio.Button value="mock" style={{ flex: 1, textAlign: 'center' }}>
            🧪 本地模拟外呼 (Mock)
          </Radio.Button>
        </Radio.Group>

        {!hasAliyunAK && currentProvider === 'aliyun' && (
          <Alert
            type="warning"
            showIcon
            message="未检测到阿里云 AK 凭证"
            description="请在项目根目录 .env 中填入 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。若未配置，系统会自动安全回退。"
            style={{ marginBottom: 12, background: 'rgba(245, 158, 11, 0.1)', borderColor: '#f59e0b' }}
          />
        )}
      </div>

      <Divider style={{ borderColor: 'rgba(148, 163, 184, 0.15)' }} />

      {/* 4. 现场联系人手机号配置 (核心演练需求) */}
      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 6 }}>
          现场演示手机号实时配置
        </div>
        <div style={{ fontSize: 12, color: '#64748b', marginBottom: 12 }}>
          可直接填入现场领导或演示人员的真实手机号，发生告警时将真实拨打该手机。
        </div>

        <Form form={form} layout="vertical" onFinish={handleSaveContacts}>
          <Card style={{ background: 'rgba(15, 23, 42, 0.6)', borderColor: 'rgba(148, 163, 184, 0.15)', marginBottom: 12 }}>
            <div style={{ color: '#38bdf8', fontWeight: 600, marginBottom: 8 }}>
              第一联系人 (一线值班人)
            </div>
            <Form.Item name="primaryName" label={<span style={{ color: '#cbd5e1' }}>姓名/称谓</span>} style={{ marginBottom: 10 }}>
              <Input placeholder="如: 张工" />
            </Form.Item>
            <Form.Item
              name="primaryPhone"
              label={<span style={{ color: '#cbd5e1' }}>真实手机号 (接收首呼)</span>}
              style={{ marginBottom: 0 }}
            >
              <Input placeholder="输入真实手机号" />
            </Form.Item>
          </Card>

          <Card style={{ background: 'rgba(15, 23, 42, 0.6)', borderColor: 'rgba(148, 163, 184, 0.15)', marginBottom: 16 }}>
            <div style={{ color: '#f59e0b', fontWeight: 600, marginBottom: 8 }}>
              第二联系人 (车间值班主管 - 升级对象)
            </div>
            <Form.Item name="secondaryName" label={<span style={{ color: '#cbd5e1' }}>姓名/称谓</span>} style={{ marginBottom: 10 }}>
              <Input placeholder="如: 李主管" />
            </Form.Item>
            <Form.Item
              name="secondaryPhone"
              label={<span style={{ color: '#cbd5e1' }}>真实手机号 (超时升级呼叫)</span>}
              style={{ marginBottom: 0 }}
            >
              <Input placeholder="输入真实手机号" />
            </Form.Item>
          </Card>

          <Button type="primary" htmlType="submit" block style={{ marginBottom: 12 }}>
            保存现场手机号配置
          </Button>

          <div style={{ display: 'flex', gap: 8 }}>
            <Input
              value={testPhone}
              onChange={(e) => setTestPhone(e.target.value)}
              placeholder="测试手机号"
            />
            <Button onClick={handleTestCall} style={{ whiteSpace: 'nowrap' }}>
              单次拨打测试
            </Button>
          </div>
        </Form>
      </div>
    </Drawer>
  );
};
