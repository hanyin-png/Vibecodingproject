# -*- coding: utf-8 -*-
"""传感器数据查询接口：给数据监测页的趋势曲线供数据"""
import pandas as pd
from fastapi import APIRouter
from sqlalchemy import text

from database import engine

router = APIRouter(prefix="/api/sensor", tags=["数据监测"])

# 监测页展示的 4 个传感器
DISPLAY_SENSORS = ["s3", "s7", "s11", "s12"]


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


@router.get("/{unit}/abnormal-points")
def abnormal_points(unit: int):
    """返回某台设备 4 个展示传感器的异常点（3σ 规则，基线 = 设备自身前 30% 循环）。

    返回格式：{"s3": [120, 121], "s7": [], ...}，值为异常的 cycle 列表。
    """
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT cycle, s3, s7, s11, s12 FROM sensor_data "
                 "WHERE unit = :unit ORDER BY cycle"),
            {"unit": unit},
        ).mappings().all()
    df = pd.DataFrame([dict(r) for r in rows])
    if len(df) < 10:
        return {col: [] for col in DISPLAY_SENSORS}

    baseline = df.iloc[: max(5, int(len(df) * 0.3))]
    result = {}
    for col in DISPLAY_SENSORS:
        mu, sigma = baseline[col].mean(), baseline[col].std()
        if sigma > 0:
            mask = (df[col] - mu).abs() > 3 * sigma
            result[col] = df.loc[mask, "cycle"].tolist()
        else:
            result[col] = []
    return result
