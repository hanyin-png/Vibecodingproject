# -*- coding: utf-8 -*-
"""骨架接口测试：验证 /api/hello 能正常返回"""
import os
import sys

# 把 backend/ 加进模块搜索路径，这样才能 import main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_hello():
    resp = client.get("/api/hello")
    assert resp.status_code == 200
    assert resp.json()["message"] == "后端联通成功"
