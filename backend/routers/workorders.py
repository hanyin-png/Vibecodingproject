# -*- coding: utf-8 -*-
"""维修工单接口：从预警一键生成工单（自动带入诊断建议）、状态流转"""
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from database import engine
from routers.diagnose import diagnose_alarm

router = APIRouter(prefix="/api/workorders", tags=["维修工单"])

# 工单状态只允许往前流转：待处理 -> 维修中 -> 已完成
STATUS_FLOW = ["待处理", "维修中", "已完成"]


class StatusIn(BaseModel):
    status: str


@router.get("")
def list_workorders():
    """查工单列表"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM work_order ORDER BY id DESC")
        ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/from-alarm/{alarm_id}", status_code=201)
def create_from_alarm(alarm_id: int):
    """从一条预警生成工单，诊断建议自动带入"""
    with engine.begin() as conn:
        alarm = conn.execute(
            text("SELECT * FROM alarm WHERE id = :id"), {"id": alarm_id}
        ).mappings().first()
        if alarm is None:
            raise HTTPException(status_code=404, detail="预警不存在")
        equip = conn.execute(
            text("SELECT * FROM equipment WHERE id = :id"),
            {"id": alarm["equipment_id"]},
        ).mappings().first()

        # 调规则引擎，把排在第一的诊断结论整理成工单建议
        diag = diagnose_alarm(alarm_id)
        top = diag["matched"][0]
        suggestion = f"疑似故障：{top['fault']}；排查步骤：{' '.join(top['steps'])}；维修措施：{top['action']}"

        title = f"{equip['code']} {alarm['alarm_type']}维修"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = conn.execute(
            text("INSERT INTO work_order (alarm_id, equipment_id, title, suggestion, status, created_at) "
                 "VALUES (:aid, :eid, :title, :sug, '待处理', :now)"),
            {"aid": alarm_id, "eid": alarm["equipment_id"],
             "title": title, "sug": suggestion, "now": now},
        )
    return {"message": "工单已生成", "work_order_id": result.lastrowid, "title": title}


@router.put("/{work_order_id}/status")
def update_status(work_order_id: int, body: StatusIn):
    """工单状态流转：待处理 -> 维修中 -> 已完成（只能往前，不能倒退）"""
    if body.status not in STATUS_FLOW:
        raise HTTPException(status_code=400, detail=f"状态必须是：{'/'.join(STATUS_FLOW)}")
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT status FROM work_order WHERE id = :id"),
            {"id": work_order_id},
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="工单不存在")
        current, target = row[0], body.status
        if STATUS_FLOW.index(target) <= STATUS_FLOW.index(current):
            raise HTTPException(status_code=400, detail=f"不能从「{current}」变更为「{target}」")
        conn.execute(
            text("UPDATE work_order SET status = :s WHERE id = :id"),
            {"s": target, "id": work_order_id},
        )
    return {"message": f"工单状态已更新为「{target}」"}
