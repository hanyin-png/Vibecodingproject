# -*- coding: utf-8 -*-
"""异常检测接口：对设备最近的传感器数据做孤立森林检测，异常自动生成预警"""
import os
import sys
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import BASE_DIR, engine

router = APIRouter(prefix="/api/anomaly", tags=["异常检测"])

ALG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "algorithms"))
sys.path.insert(0, ALG_DIR)
from anomaly import detect  # noqa: E402


@router.post("/{equipment_id}")
def detect_anomaly(equipment_id: int):
    """对一台设备做异常检测；发现异常则自动写一条"传感器异常"预警"""
    with engine.begin() as conn:
        equip = conn.execute(
            text("SELECT * FROM equipment WHERE id = :id"), {"id": equipment_id}
        ).mappings().first()
        if equip is None:
            raise HTTPException(status_code=404, detail="设备不存在")
        unit = int(equip["code"].split("-")[1])

        rows = conn.execute(
            text("SELECT * FROM sensor_data WHERE unit = :unit ORDER BY cycle"),
            {"unit": unit},
        ).mappings().all()
        if not rows:
            raise HTTPException(status_code=400, detail="该设备没有传感器数据")
        df = pd.DataFrame([dict(r) for r in rows])

        is_anomaly, abnormal_sensors, score = detect(df)

        # 异常 -> 自动生成预警，并把设备状态改为"预警"
        if is_anomaly:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sensors_text = "、".join(abnormal_sensors) if abnormal_sensors else "多个"
            conn.execute(
                text("INSERT INTO alarm (equipment_id, alarm_type, level, message, status, created_at) "
                     "VALUES (:eid, '传感器异常', '警告', :msg, '未处理', :now)"),
                {"eid": equipment_id,
                 "msg": f"孤立森林检测到运行数据异常，异常传感器：{sensors_text}",
                 "now": now},
            )
            conn.execute(
                text("UPDATE equipment SET status = '预警' WHERE id = :id AND status = '健康'"),
                {"id": equipment_id},
            )

    return {
        "equipment_id": equipment_id,
        "unit": unit,
        "is_anomaly": is_anomaly,
        "abnormal_sensors": abnormal_sensors,
        "anomaly_score": round(score, 4),
    }
