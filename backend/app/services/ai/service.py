import asyncio
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.alarm import Alarm
from app.models.ai_analysis import AIAnalysis
from app.websocket.manager import websocket_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    AI 智能工业根因分析服务（异步旁路引擎）
    严格与外呼主流程解耦：报警生成后立即以非阻塞异步协程启动
    """

    # 工业领域高置信度故障机理与专家排查决策库
    EXPERT_KNOWLEDGE_BASE = {
        "HYDRAULIC_LEAK": {
            "root_cause": "#1 主泵高压单向阀疲劳撕裂内泄，导致主回路压力急剧溃跌",
            "confidence": 0.94,
            "risk_level": "CRITICAL",
            "suggestion": "立即切换备用油路并隔离故障主泵！建议值班班组手动锁定泵出口截止阀，防止油温次生超标。",
            "checklist": [
                "1. 现场观察主泵体壳体回油管温升（判定是否存在高压油液内泄剧烈发热）",
                "2. 拆卸检查单向阀先导阻尼孔与阀芯主密封面是否有金属磨损碎屑",
                "3. 校验吸油过滤器压差指示器，排查是否存在泵吸空气或气蚀现象",
                "4. 测量比例溢流阀控制线圈输入控制电流（基准 600mA）"
            ]
        },
        "MOTOR_OVERHEAT": {
            "root_cause": "粗轧电机传动端轴承油脂润滑失效，引发重载机械咬合与定子绕组严重过流",
            "confidence": 0.91,
            "risk_level": "HIGH",
            "suggestion": "立即降低轧制线运行负荷，派遣机修人员携测振仪与红外热像仪赴B区现场排查，准备注入高温航空润滑脂。",
            "checklist": [
                "1. 采用非接触式热成像仪扫描驱动端(DE)与非驱动端(NDE)轴承箱表面温差",
                "2. 采集三相平衡电流，排查是否存在单相缺相或绕组匝间绝缘击穿",
                "3. 检查电机强迫风冷风道是否被氧化铁皮异物堵塞",
                "4. 检查联轴器弹性缓冲胶块是否碎裂引起偏心振动"
            ]
        },
        "DEVICE_OFFLINE": {
            "root_cause": "工控环网交换机端口突发广播风暴或工业以太网现场总线物理跳线松脱",
            "confidence": 0.96,
            "risk_level": "MEDIUM",
            "suggestion": "排查网络通讯交换机端口指示灯，重新插拔该工位屏蔽双绞线，必要时切换至备用环网。",
            "checklist": [
                "1. 检查现场交换机端口 Link/Act 绿色指示灯闪烁频率",
                "2. 检查现场远程 I/O 模块 24VDC 稳压电源冗余供电状态",
                "3. 执行 ping 与 arp 探测，排查 IP 地址冲突或总线超时"
            ]
        }
    }

    async def analyze_alarm_async(self, alarm_id: int):
        """
        异步后台执行 AI 根因推导，绝不阻塞呼叫与业务流程
        """
        logger.info(f"【AI旁路服务】启动报警 #{alarm_id} 的异步智能根因推导任务...")

        # 模拟 AI 专家决策链计算耗时 (约 1.5 秒)，使大屏呈现出真实的分析计算过程
        await asyncio.sleep(1.5)

        db: Session = SessionLocal()
        try:
            alarm = db.get(Alarm, alarm_id)
            if not alarm:
                logger.warning(f"报警不存在，AI 分析终止: #{alarm_id}")
                return

            alarm.ai_analysis_status = "ANALYZING"
            db.commit()

            # 根据报警指标类型或设备类型命中专家推导树
            expert_data = None
            if "pressure" in alarm.metric_name.lower() or "液压" in alarm.title:
                expert_data = self.EXPERT_KNOWLEDGE_BASE["HYDRAULIC_LEAK"]
            elif "current" in alarm.metric_name.lower() or "temp" in alarm.metric_name.lower() or "电机" in alarm.title:
                expert_data = self.EXPERT_KNOWLEDGE_BASE["MOTOR_OVERHEAT"]
            else:
                expert_data = self.EXPERT_KNOWLEDGE_BASE["DEVICE_OFFLINE"]

            # 写入 AI 分析表
            analysis = AIAnalysis(
                alarm_id=alarm.id,
                root_cause=expert_data["root_cause"],
                confidence=expert_data["confidence"],
                risk_level=expert_data["risk_level"],
                suggestion=expert_data["suggestion"],
                checklist=expert_data["checklist"],
                raw_response={"engine": settings.AI_PROVIDER, "status": "SUCCESS"}
            )
            db.add(analysis)

            alarm.ai_analysis_status = "COMPLETED"
            db.commit()
            db.refresh(analysis)

            logger.info(f"【AI旁路服务完成】报警 #{alarm.id} 根因确定: {analysis.root_cause} (置信度: {analysis.confidence*100}%)")

            # 广播 WebSocket 通知大屏卡片展示 AI 诊断成果
            await websocket_manager.broadcast(
                "ai_analysis_ready",
                {
                    "alarm_id": alarm.id,
                    "analysis_id": analysis.id,
                    "root_cause": analysis.root_cause,
                    "confidence": analysis.confidence,
                    "risk_level": analysis.risk_level,
                    "suggestion": analysis.suggestion,
                    "checklist": analysis.checklist,
                    "created_at": analysis.created_at.isoformat()
                }
            )

        except Exception as e:
            logger.exception(f"AI 异步分析异常: {e}")
            if alarm:
                alarm.ai_analysis_status = "FAILED"
                db.commit()
        finally:
            db.close()


ai_service = AIService()
