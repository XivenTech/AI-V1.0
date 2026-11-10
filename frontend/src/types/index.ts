export interface Device {
  id: number;
  code: string;
  name: string;
  type: string;
  location: string;
  status: 'RUNNING' | 'ALARMING' | 'OFFLINE' | 'MAINTENANCE';
  metrics?: {
    pressure?: number;
    temperature?: number;
    current?: number;
    vibration?: number;
    flow?: number;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface AIAnalysis {
  id: number;
  alarm_id: number;
  root_cause: string;
  confidence: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  suggestion: string;
  checklist?: string[];
  created_at: string;
}

export interface AlarmEvent {
  id: number;
  alarm_id: number;
  event_type: string;
  from_status: string;
  to_status: string;
  operator: string;
  note: string;
  created_at: string;
}

export interface Alarm {
  id: number;
  device_id: number;
  title: string;
  level: 'P1' | 'P2' | 'P3';
  status: 'TRIGGERED' | 'ACKNOWLEDGED' | 'PROCESSING' | 'RESOLVED' | 'CLOSED';
  metric_name: string;
  trigger_value: number;
  threshold: number;
  unit: string;
  message: string;
  ai_analysis_status: 'PENDING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  device?: Device;
  ai_analysis?: AIAnalysis;
}

export interface CallRecord {
  id: number;
  alarm_id: number;
  contact_name: string;
  contact_phone: string;
  priority: number;
  provider: 'aliyun' | 'mock';
  call_id: string;
  status: 'CALLING' | 'ANSWERED' | 'UNANSWERED' | 'REJECTED' | 'TIMEOUT' | 'ESCALATED' | 'FAILED';
  duration: number;
  template_code: string;
  template_params?: Record<string, any>;
  error_msg: string;
  created_at: string;
  answered_at?: string;
  ended_at?: string;
}

export interface Contact {
  id: number;
  name: string;
  role: string;
  phone: string;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkOrder {
  id: number;
  order_code: string;
  alarm_id: number;
  title: string;
  priority: 'P1' | 'P2' | 'P3';
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'CLOSED';
  assignee: string;
  description: string;
  ai_suggestion: string;
  steps?: string[];
  solution_note: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface WebSocketEvent<T = any> {
  type:
    | 'telemetry_update'
    | 'alarm_created'
    | 'alarm_transition'
    | 'call_status'
    | 'ai_analysis_ready'
    | 'workorder_created'
    | 'workorder_update'
    | 'scenario_injected'
    | 'demo_reset'
    | 'golden_path_step';
  data: T;
}
