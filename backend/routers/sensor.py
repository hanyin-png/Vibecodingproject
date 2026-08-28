# -*- coding: utf-8 -*-
"""传感器数据查询接口：给数据监测页的趋势曲线供数据"""
from fastapi import APIRouter
from sqlalchemy import text

from database import engine

router = APIRouter(prefix="/api/sensor", tags=["数据监测"])


@router.get("/{unit}")
def get_sensor_data(unit: int, start: int = 1, end: int = 99999):
    """查某台设备（unit）在 [start, end] 循环范围内的传感器数据，按 cycle 排序"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM sensor_data "
                 "WHERE unit = :unit AND cycle BETWEEN :start AND :end "
                 "ORDER BY cycle"),
            {"unit": unit, "start": start, "end": end},
        ).mappings().all()
    return [dict(r) for r in rows]
