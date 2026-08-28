# -*- coding: utf-8 -*-
"""预警中心接口：预警列表查询、标记已处理"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import engine

router = APIRouter(prefix="/api/alarms", tags=["预警中心"])


@router.get("")
def list_alarms(status: str = ""):
    """查预警列表，可按状态过滤（如 ?status=未处理）"""
    sql = "SELECT * FROM alarm"
    params = {}
    if status:
        sql += " WHERE status = :status"
        params["status"] = status
    sql += " ORDER BY id DESC"
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.put("/{alarm_id}/resolve")
def resolve_alarm(alarm_id: int):
    """把预警标记为已处理"""
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE alarm SET status = '已处理' WHERE id = :id"),
            {"id": alarm_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="预警不存在")
    return {"message": "已标记为已处理"}
