# -*- coding: utf-8 -*-
"""健康评估接口：RUL 预测。

流程：设备 id -> 找到 unit -> 从库里取传感器数据 -> 提取最后 20 循环特征
-> 随机森林推理 -> 算健康度 -> 写 prediction 表 -> RUL 过低自动生成预警。
"""
import os
import sys
from datetime import datetime

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import BASE_DIR, engine

router = APIRouter(prefix="/api/predict", tags=["健康评估"])

# 复用 algorithms/ 里的特征提取函数
ALG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "algorithms"))
sys.path.insert(0, ALG_DIR)
from rul_rf import extract_last_window  # noqa: E402

MODEL_PATH = os.path.join(BASE_DIR, "models", "rf_rul.pkl")
_model = None  # 模型只在第一次用时加载，之后常驻内存（演示不卡）


def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def health_score(rul):
    """健康度评分：RUL 上限 125，换算成 0~100 分"""
    return max(0.0, min(100.0, rul / 125 * 100))


def alarm_level(rul):
    """按 RUL 阈值分级（规则引擎和预警统一用这套阈值）"""
    if rul <= 30:
        return "严重"
    if rul <= 60:
        return "警告"
    return "提示"


@router.post("/{equipment_id}")
def predict_rul(equipment_id: int):
    """对一台设备做 RUL 预测，结果写入 prediction 表"""
    with engine.begin() as conn:
        # 1. 找设备，code 形如 ENG-001，数字部分就是数据集里的 unit
        equip = conn.execute(
            text("SELECT * FROM equipment WHERE id = :id"), {"id": equipment_id}
        ).mappings().first()
        if equip is None:
            raise HTTPException(status_code=404, detail="设备不存在")
        unit = int(equip["code"].split("-")[1])

        # 2. 取该设备的传感器数据
        rows = conn.execute(
            text("SELECT * FROM sensor_data WHERE unit = :unit ORDER BY cycle"),
            {"unit": unit},
        ).mappings().all()
        if not rows:
            raise HTTPException(status_code=400, detail="该设备没有传感器数据")
        df = pd.DataFrame([dict(r) for r in rows])

        # 3. 提取最后窗口特征 -> 推理
        X, _ = extract_last_window(df)
        if len(X) == 0:
            raise HTTPException(status_code=400, detail="数据不足一个窗口（20 循环）")
        rul = float(get_model().predict(X)[0])
        score = health_score(rul)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 4. 写预测记录
        conn.execute(
            text("INSERT INTO prediction (equipment_id, rul, health_score, method, created_at) "
                 "VALUES (:eid, :rul, :score, 'random_forest', :now)"),
            {"eid": equipment_id, "rul": round(rul, 1), "score": round(score, 1), "now": now},
        )

        # 5. RUL 不超过 90 自动生成预警，同时更新设备状态
        if rul <= 90:
            level = alarm_level(rul)
            conn.execute(
                text("INSERT INTO alarm (equipment_id, alarm_type, level, message, status, created_at) "
                     "VALUES (:eid, '剩余寿命不足', :level, :msg, '未处理', :now)"),
                {"eid": equipment_id, "level": level,
                 "msg": f"预测剩余寿命仅 {rul:.0f} 个循环，健康度 {score:.0f} 分", "now": now},
            )
            conn.execute(
                text("UPDATE equipment SET status = :s WHERE id = :id"),
                {"s": "故障" if rul <= 30 else "预警", "id": equipment_id},
            )

    return {
        "equipment_id": equipment_id,
        "unit": unit,
        "rul": round(rul, 1),
        "health_score": round(score, 1),
        "method": "random_forest",
    }


@router.get("/history/{equipment_id}")
def prediction_history(equipment_id: int):
    """查某台设备的历史评估记录（健康评估页用）"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM prediction WHERE equipment_id = :id ORDER BY created_at DESC"),
            {"id": equipment_id},
        ).mappings().all()
    return [dict(r) for r in rows]
