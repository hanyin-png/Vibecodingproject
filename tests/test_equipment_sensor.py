# -*- coding: utf-8 -*-
"""设备台账与传感器查询接口测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_equipment_crud():
    """设备增删改查一条龙"""
    # 查列表：库里应有 100 台导入的设备
    resp = client.get("/api/equipment")
    assert resp.status_code == 200
    assert len(resp.json()) >= 100

    # 新增
    resp = client.post("/api/equipment", json={"code": "ENG-PYTEST"})
    assert resp.status_code == 201

    # 找到它的 id
    items = client.get("/api/equipment").json()
    tid = [x["id"] for x in items if x["code"] == "ENG-PYTEST"][0]

    # 修改（含中文状态）
    resp = client.put(f"/api/equipment/{tid}", json={"code": "ENG-PYTEST", "status": "预警"})
    assert resp.status_code == 200
    check = [x for x in client.get("/api/equipment").json() if x["id"] == tid][0]
    assert check["status"] == "预警"

    # 删除
    resp = client.delete(f"/api/equipment/{tid}")
    assert resp.status_code == 200


def test_sensor_query():
    """传感器数据查询：unit=1 应有数据，且支持范围过滤"""
    resp = client.get("/api/sensor/1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0  # test 集设备只跑到中途，unit=1 实际有 31 条记录

    # 范围过滤：1~10 循环应恰好 10 条
    data2 = client.get("/api/sensor/1?start=1&end=10").json()
    assert len(data2) == 10
    assert data2[0]["cycle"] == 1
