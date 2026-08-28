# -*- coding: utf-8 -*-
"""智能诊断接口：对一条预警，用规则引擎给出诊断建议。

异常传感器的判定方法：和设备自己的"健康时期"对比——
取该设备前 1/3 循环作为健康基线，最近 20 循环的均值偏离基线超过 3σ
的传感器判为异常。
"""
import os
import sys

import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import BASE_DIR, engine
from routers.predict import get_model

router = APIRouter(prefix="/api/diagnose", tags=["智能诊断"])

# 复用 algorithms/ 里的规则引擎和特征提取
ALG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "algorithms"))
sys.path.insert(0, ALG_DIR)
from import_data import USED_SENSORS  # noqa: E402
from rules_engine import diagnose  # noqa: E402
from rul_rf import extract_last_window  # noqa: E402

WINDOW = 20  # 与 rul_rf 的窗口一致


def find_abnormal_sensors(df):
    """和设备自己的健康基线（前 1/3 循环）对比，找出偏离超过 3σ 的传感器"""
    base_len = max(5, len(df) // 3)
    baseline = df.iloc[:base_len]
    recent = df.iloc[-WINDOW:]
    abnormal = []
    for col in USED_SENSORS:
        mu = baseline[col].mean()
        sigma = baseline[col].std()
        if sigma > 0 and abs(recent[col].mean() - mu) > 3 * sigma:
            abnormal.append(col)
    return abnormal


@router.post("/{alarm_id}")
def diagnose_alarm(alarm_id: int):
    """对指定预警做规则引擎诊断"""
    with engine.connect() as conn:
        # 1. 查预警和设备
        alarm = conn.execute(
            text("SELECT * FROM alarm WHERE id = :id"), {"id": alarm_id}
        ).mappings().first()
        if alarm is None:
            raise HTTPException(status_code=404, detail="预警不存在")
        equip = conn.execute(
            text("SELECT * FROM equipment WHERE id = :id"),
            {"id": alarm["equipment_id"]},
        ).mappings().first()
        unit = int(equip["code"].split("-")[1])

        # 2. 取传感器数据，找异常传感器
        rows = conn.execute(
            text("SELECT * FROM sensor_data WHERE unit = :unit ORDER BY cycle"),
            {"unit": unit},
        ).mappings().all()
    df = pd.DataFrame([dict(r) for r in rows])
    abnormal = find_abnormal_sensors(df)

    # 3. 现场算一次 RUL（诊断要拿到当前寿命水平）
    X, _ = extract_last_window(df)
    rul = float(get_model().predict(X)[0])

    # 4. 规则引擎推理
    result = diagnose(abnormal, rul, alarm["alarm_type"])
    result["alarm_id"] = alarm_id
    result["equipment_id"] = alarm["equipment_id"]
    result["unit"] = unit
    return result
