# -*- coding: utf-8 -*-
"""首页统计与异常点接口测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_stats():
    """总览统计：应返回设备数、预警数、工单数、状态分布"""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["equipment_total"] == 100
    assert data["alarm_open"] >= 0
    assert len(data["status_dist"]) >= 1
    total_in_dist = sum(d["count"] for d in data["status_dist"])
    assert total_in_dist == 100  # 分布加起来应等于设备总数


def test_abnormal_points():
    """异常点接口：退化末期的 unit=20 应能标出异常点，健康的早期 unit 应该少"""
    resp = client.get("/api/sensor/20/abnormal-points")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"s3", "s7", "s11", "s12"}
    assert sum(len(v) for v in data.values()) > 0  # 快失效的设备一定有异常点
