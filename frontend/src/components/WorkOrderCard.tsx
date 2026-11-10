import React, { useState } from 'react';
import { Card, Tag, Button, Typography, Steps, message, Modal, Input } from 'antd';
import { Wrench, CheckCircle, Clock, UserCheck, CheckCheck } from 'lucide-react';
import { WorkOrder } from '../types';
import { transitionWorkOrder } from '../services/api';

const { Text, Paragraph } = Typography;

interface WorkOrderCardProps {
  workOrder?: WorkOrder | null;
  onRefresh?: () => void;
}

export const WorkOrderCard: React.FC<WorkOrderCardProps> = ({ workOrder, onRefresh }) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [completeModalOpen, setCompleteModalOpen] = useState<boolean>(false);
  const [solutionNote, setSolutionNote] = useState<string>(
    '现场更换单向阀密封环并紧固高压管路接头，系统打压测试 25.0 MPa 保持正常无泄漏。'
  );

  const handleTransition = async (targetState: string, note: string = '') => {
    if (!workOrder) return;
    try {
      setLoadingAction(targetState);
      await transitionWorkOrder(workOrder.id, targetState, note, workOrder.assignee || '现场工程师');
      message.success(`工单状态已成功更新为: ${targetState}`);
      if (targetState === 'COMPLETED') {
        setCompleteModalOpen(false);
      }
      if (onRefresh) onRefresh();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '工单状态流转失败');
    } finally {
      setLoadingAction(null);
    }
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Tag color="warning">待接单处置</Tag>;
      case 'IN_PROGRESS':
        return <Tag color="processing">排查抢修中</Tag>;
      case 'COMPLETED':
        return <Tag color="success">现场维修完成</Tag>;
      case 'CLOSED':
        return <Tag color="default">已验收归档闭环</Tag>;
      default:
        return <Tag>{status}</Tag>;
    }
  };

  return (
    <Card
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.85) 100%)',
        backdropFilter: 'blur(16px)',
        border: workOrder?.status === 'IN_PROGRESS' ? '1px solid #10b981' : '1px solid rgba(16, 185, 129, 0.25)',
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
              background: 'rgba(16, 185, 129, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#34d399',
            }}
          >
            <Wrench size={18} />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc' }}>
              智能维修工单 (自动派单)
            </div>
            <div style={{ fontSize: 11, color: '#94a3b8' }}>
              电话确认后触发自动派工并联动工单状态机
            </div>
          </div>
        </div>

        <div>{workOrder ? getStatusTag(workOrder.status) : <Tag color="default">暂无待办</Tag>}</div>
      </div>

      {workOrder ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* 单号与负责人 */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1.5fr 1fr',
              background: 'rgba(15, 23, 42, 0.6)',
              padding: '10px 14px',
              borderRadius: 8,
              border: '1px solid rgba(148, 163, 184, 0.1)',
            }}
          >
            <div>
              <div style={{ fontSize: 11, color: '#64748b' }}>工单编号</div>
              <div style={{ fontSize: 14, fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                {workOrder.order_code}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: '#64748b' }}>责任处理人</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>
                {workOrder.assignee || '未指派'}
              </div>
            </div>
          </div>

          {/* 标题与描述 */}
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 4 }}>
              {workOrder.title}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              {workOrder.description}
            </div>
          </div>

          {/* AI 维修指导摘要 */}
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px dashed rgba(16, 185, 129, 0.3)',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 12,
              color: '#a7f3d0',
            }}
          >
            <strong>AI 现场检修指导:</strong> {workOrder.ai_suggestion}
          </div>

          {/* 处理完成说明 (若已完成) */}
          {workOrder.solution_note && (
            <div
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(148, 163, 184, 0.15)',
                borderRadius: 8,
                padding: '8px 12px',
                fontSize: 12,
                color: '#cbd5e1',
              }}
            >
              <span style={{ color: '#10b981', fontWeight: 600 }}>处置记录:</span> {workOrder.solution_note}
            </div>
          )}

          {/* 闭环流转操作按钮组 */}
          <div style={{ marginTop: 'auto', paddingTop: 8, display: 'flex', gap: 8 }}>
            {workOrder.status === 'PENDING' && (
              <Button
                type="primary"
                block
                style={{ background: '#3b82f6', borderColor: '#3b82f6' }}
                loading={loadingAction === 'IN_PROGRESS'}
                onClick={() => handleTransition('IN_PROGRESS', '工程师已接单，正在前往现场进行物理隔离与排查')}
              >
                接单并开始处置
              </Button>
            )}

            {workOrder.status === 'IN_PROGRESS' && (
              <Button
                type="primary"
                block
                style={{ background: '#10b981', borderColor: '#10b981' }}
                onClick={() => setCompleteModalOpen(true)}
              >
                排查维修完成 (闭环消除告警)
              </Button>
            )}

            {workOrder.status === 'COMPLETED' && (
              <Button
                block
                style={{ background: 'rgba(100, 116, 139, 0.2)', borderColor: '#64748b', color: '#cbd5e1' }}
                loading={loadingAction === 'CLOSED'}
                onClick={() => handleTransition('CLOSED', '工单最终验收归档，设备恢复满负荷连续稳定运行')}
              >
                验收并归档关闭 (Closed)
              </Button>
            )}

            {workOrder.status === 'CLOSED' && (
              <div style={{ textAlign: 'center', width: '100%', color: '#10b981', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                <CheckCheck size={16} /> 该工单与告警均已全流程闭环归档
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 13 }}>
          当前无活动工单。当外呼电话被值班人员接听后，系统将自动生成检修工单。
        </div>
      )}

      {/* 维修完成确认弹窗 */}
      <Modal
        title="提交现场检修处置结果"
        open={completeModalOpen}
        onCancel={() => setCompleteModalOpen(false)}
        onOk={() => handleTransition('COMPLETED', solutionNote)}
        confirmLoading={loadingAction === 'COMPLETED'}
        okText="确认并闭环消除告警"
        cancelText="取消"
      >
        <div style={{ marginBottom: 12, color: '#64748b', fontSize: 13 }}>
          请简要记录现场排查结果，提交后系统将把工单流转为 COMPLETED，并自动将关联告警联动解除：
        </div>
        <Input.TextArea
          rows={3}
          value={solutionNote}
          onChange={(e) => setSolutionNote(e.target.value)}
        />
      </Modal>
    </Card>
  );
};
