# -*- coding: utf-8 -*-
"""异常检测模块与接口测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "algorithms"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from anomaly import detect
from fastapi.testclient import TestClient
from import_data import load_txt
from sqlalchemy import text

from database import engine
from main import app

client = TestClient(app)


def test_detect_degraded_unit():
    """快失效的设备（unit=20）应判为异常，且能列出异常传感器"""
    test_df = load_txt("test_FD001.txt")
    is_anomaly, sensors, score = detect(test_df[test_df["unit"] == 20])
    assert is_anomaly is True
    assert len(sensors) > 0


def test_detect_healthy_unit():
    """健康早期的数据（unit=1 前 30 循环）应判为正常"""
    test_df = load_txt("test_FD001.txt")
    is_anomaly, sensors, score = detect(test_df[test_df["unit"] == 1].iloc[:30])
    assert is_anomaly is False


def test_anomaly_endpoint():
    """接口：检测设备20 应报异常并自动生成'传感器异常'预警"""
    resp = client.post("/api/anomaly/20")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_anomaly"] is True
    assert len(data["abnormal_sensors"]) > 0

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT alarm_type, level FROM alarm "
                 "WHERE equipment_id=20 ORDER BY id DESC LIMIT 1")
        ).first()
    assert row[0] == "传感器异常"

    # 清理测试数据，恢复设备状态
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM alarm WHERE equipment_id=20"))
        conn.execute(text("UPDATE equipment SET status='健康' WHERE id=20"))
