# -*- coding: utf-8 -*-
"""首页总览统计接口：给仪表盘页面供数据"""
from fastapi import APIRouter
from sqlalchemy import text

from database import engine

router = APIRouter(prefix="/api/stats", tags=["首页总览"])


@router.get("")
def overview():
    """总览统计：设备数、未处理预警数、待处理工单数、健康状态分布、健康度最低 TOP5"""
    with engine.connect() as conn:
        equip_total = conn.execute(text("SELECT COUNT(*) FROM equipment")).scalar()
        alarm_open = conn.execute(
            text("SELECT COUNT(*) FROM alarm WHERE status='未处理'")).scalar()
        wo_open = conn.execute(
            text("SELECT COUNT(*) FROM work_order WHERE status='待处理'")).scalar()
        status_rows = conn.execute(
            text("SELECT status, COUNT(*) FROM equipment GROUP BY status")).all()
        # 每台设备取最新一次预测，按健康度升序取最差的 5 台
        top5 = conn.execute(text("""
            SELECT e.code AS code, p.health_score AS health_score, p.rul AS rul
            FROM prediction p JOIN equipment e ON e.id = p.equipment_id
            WHERE p.id IN (SELECT MAX(id) FROM prediction GROUP BY equipment_id)
            ORDER BY p.health_score ASC LIMIT 5
        """)).mappings().all()
    return {
        "equipment_total": equip_total,
        "alarm_open": alarm_open,
        "workorder_open": wo_open,
        "status_dist": [{"status": s, "count": c} for s, c in status_rows],
        "low_health_top5": [dict(r) for r in top5],
    }
