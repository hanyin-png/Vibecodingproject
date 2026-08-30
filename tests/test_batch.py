# -*- coding: utf-8 -*-
"""批量评估接口测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import engine
from main import app

client = TestClient(app)


def test_batch_predict():
    """一键批量评估：100 台全部评估；第二次跑预警不重复生成"""
    resp = client.post("/api/predict/batch")
    assert resp.status_code == 200
    data = resp.json()
    assert data["evaluated"] == 100

    # 第二次跑：已有未处理预警的设备不应重复生成
    resp2 = client.post("/api/predict/batch")
    assert resp2.json()["new_alarms"] == 0

    # 统计接口应能反映全机群评估结果
    stats = client.get("/api/stats").json()
    assert len(stats["low_health_top5"]) == 5
    assert stats["low_health_top5"][0]["health_score"] <= 30  # 榜首一定是不太健康的

    # 清理：恢复出厂状态（设备全部健康，业务表清空）
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM prediction"))
        conn.execute(text("DELETE FROM alarm"))
        conn.execute(text("DELETE FROM work_order"))
        conn.execute(text("UPDATE equipment SET status='健康'"))
