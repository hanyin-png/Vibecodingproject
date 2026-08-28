# -*- coding: utf-8 -*-
"""RUL 预测接口测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import engine
from main import app

client = TestClient(app)


def test_predict_rul():
    """对设备18做预测：应返回合理的 RUL 和健康度，且写入 prediction 表"""
    resp = client.post("/api/predict/18")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unit"] == 18
    assert 0 < data["rul"] <= 125        # RUL 在截断范围内
    assert 0 <= data["health_score"] <= 100

    # 历史记录里能查到刚才这次预测
    history = client.get("/api/predict/history/18").json()
    assert len(history) >= 1
    assert history[0]["method"] == "random_forest"


def test_predict_not_found():
    """对不存在的设备预测，应返回 404"""
    resp = client.post("/api/predict/9999")
    assert resp.status_code == 404


def teardown_module():
    """测试收尾：清掉测试产生的预测和预警记录，恢复设备状态"""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM prediction WHERE equipment_id = 18"))
        conn.execute(text("DELETE FROM alarm WHERE equipment_id = 18"))
        conn.execute(text("UPDATE equipment SET status = '健康' WHERE id = 18"))
