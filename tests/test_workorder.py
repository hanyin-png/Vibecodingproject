# -*- coding: utf-8 -*-
"""维修工单接口 + 业务闭环联调测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import engine
from main import app

client = TestClient(app)


def test_business_closed_loop():
    """业务闭环一条龙：预测 -> 预警 -> 诊断 -> 工单 -> 状态流转"""
    # ① 健康评估：设备20 会触发严重预警
    resp = client.post("/api/predict/20")
    assert resp.status_code == 200
    assert resp.json()["rul"] <= 30

    # ② 预警中心：查到自动生成的预警
    with engine.connect() as conn:
        alarm = conn.execute(
            text("SELECT id, level FROM alarm WHERE equipment_id=20 ORDER BY id DESC LIMIT 1")
        ).first()
    assert alarm is not None and alarm[1] == "严重"
    alarm_id = alarm[0]

    # ③ 智能诊断：规则引擎给出建议
    resp = client.post(f"/api/diagnose/{alarm_id}")
    assert resp.status_code == 200
    assert resp.json()["matched_count"] >= 1

    # ④ 一键生成工单：诊断建议自动带入
    resp = client.post(f"/api/workorders/from-alarm/{alarm_id}")
    assert resp.status_code == 201
    wo_id = resp.json()["work_order_id"]
    with engine.connect() as conn:
        wo = conn.execute(
            text("SELECT title, suggestion, status FROM work_order WHERE id=:id"),
            {"id": wo_id},
        ).first()
    assert "ENG-020" in wo[0]
    assert "HPC" in wo[1]          # 建议里应包含规则引擎的诊断结论
    assert wo[2] == "待处理"

    # ⑤ 状态流转：待处理 -> 维修中 -> 已完成；倒退应报错
    assert client.put(f"/api/workorders/{wo_id}/status", json={"status": "维修中"}).status_code == 200
    assert client.put(f"/api/workorders/{wo_id}/status", json={"status": "待处理"}).status_code == 400
    assert client.put(f"/api/workorders/{wo_id}/status", json={"status": "已完成"}).status_code == 200

    # ⑥ 预警标记已处理
    assert client.put(f"/api/alarms/{alarm_id}/resolve").status_code == 200

    # 清理测试数据，恢复设备状态
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM prediction WHERE equipment_id=20"))
        conn.execute(text("DELETE FROM alarm WHERE equipment_id=20"))
        conn.execute(text("DELETE FROM work_order WHERE equipment_id=20"))
        conn.execute(text("UPDATE equipment SET status='健康' WHERE id=20"))
