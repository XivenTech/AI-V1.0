import axios from 'axios';
import {
  Device,
  Alarm,
  AlarmEvent,
  CallRecord,
  Contact,
  WorkOrder
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

export const getDevices = async (): Promise<Device[]> => {
  const res = await api.get('/devices');
  return res.data;
};

export const getAlarms = async (params?: { status?: string; level?: string }): Promise<Alarm[]> => {
  const res = await api.get('/alarms', { params });
  return res.data;
};

export const getAlarm = async (id: number): Promise<Alarm> => {
  const res = await api.get(`/alarms/${id}`);
  return res.data;
};

export const getAlarmEvents = async (id: number): Promise<AlarmEvent[]> => {
  const res = await api.get(`/alarms/${id}/events`);
  return res.data;
};

export const transitionAlarm = async (
  id: number,
  targetState: string,
  note: string = '',
  operator: string = 'OPERATOR'
): Promise<Alarm> => {
  const res = await api.post(`/alarms/${id}/transition`, {
    target_state: targetState,
    note,
    operator,
  });
  return res.data;
};

export const getCallRecords = async (alarmId?: number): Promise<CallRecord[]> => {
  const res = await api.get('/calls/records', { params: { alarm_id: alarmId } });
  return res.data;
};

export const getCallConfig = async (): Promise<{
  current_provider: string;
  has_aliyun_credentials: boolean;
  tts_code: string;
  timeout_seconds: number;
}> => {
  const res = await api.get('/calls/config');
  return res.data;
};

export const switchCallProvider = async (provider: 'aliyun' | 'mock') => {
  const res = await api.post(`/calls/config/provider?provider=${provider}`);
  return res.data;
};

export const triggerCall = async (data: {
  phone: string;
  alarm_id?: number;
  contact_name?: string;
  provider?: string;
}): Promise<CallRecord> => {
  const res = await api.post('/calls/trigger', data);
  return res.data;
};

export const simulateCallAction = async (data: {
  call_record_id?: number;
  action: 'ANSWER' | 'TIMEOUT' | 'REJECT';
}) => {
  const res = await api.post('/calls/simulate-action', data);
  return res.data;
};

export const getContacts = async (): Promise<Contact[]> => {
  const res = await api.get('/contacts');
  return res.data;
};

export const updateContact = async (
  id: number,
  data: { name: string; phone: string; role: string; is_active?: boolean }
): Promise<Contact> => {
  const res = await api.put(`/contacts/${id}`, data);
  return res.data;
};

export const getWorkOrders = async (status?: string): Promise<WorkOrder[]> => {
  const res = await api.get('/workorders', { params: { status } });
  return res.data;
};

export const transitionWorkOrder = async (
  id: number,
  targetState: string,
  solutionNote: string = '',
  operator: string = 'OPERATOR'
): Promise<WorkOrder> => {
  const res = await api.post(`/workorders/${id}/transition`, {
    target_state: targetState,
    solution_note: solutionNote,
    operator,
  });
  return res.data;
};

export const triggerDemoScenario = async (
  scenario: 'HYDRAULIC_LEAK' | 'MOTOR_OVERHEAT' | 'DEVICE_OFFLINE' | 'RESET',
  deviceCode?: string
) => {
  const res = await api.post('/demo/trigger-scenario', {
    scenario,
    device_code: deviceCode,
  });
  return res.data;
};

export const startGoldenPath = async () => {
  const res = await api.post('/demo/golden-path/start');
  return res.data;
};

export default api;
