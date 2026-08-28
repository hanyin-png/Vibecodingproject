# -*- coding: utf-8 -*-
"""规则引擎与诊断接口测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "algorithms"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from rules_engine import diagnose
from sqlalchemy import text

from database import engine
from main import app

client = TestClient(app)


def test_rule_a1_hpc():
    """A1：s7+s11+s12 同时异常 → 高压压气机退化"""
    result = diagnose(["s7", "s11", "s12"], rul=100)
    rule_ids = [m["rule_id"] for m in result["matched"]]
    assert "A1" in rule_ids


def test_rule_b1_low_rul():
    """B1：RUL ≤ 30 → 剩余寿命严重不足"""
    result = diagnose([], rul=20)
    rule_ids = [m["rule_id"] for m in result["matched"]]
    assert "B1" in rule_ids


def test_rule_a6_bleed_air():
    """A6：s20 异常 → 冷却引气系统泄漏"""
    result = diagnose(["s20"], rul=100)
    rule_ids = [m["rule_id"] for m in result["matched"]]
    assert "A6" in rule_ids


def test_fallback_c3():
    """无任何特征时命中兜底规则 C3；有其他规则命中时 C3 不出现"""
    only_c3 = diagnose([], rul=100)
    assert [m["rule_id"] for m in only_c3["matched"]] == ["C3"]

    with_hit = diagnose(["s2"], rul=100)
    rule_ids = [m["rule_id"] for m in with_hit["matched"]]
    assert "A9" in rule_ids
    assert "C3" not in rule_ids


def test_diagnose_endpoint():
    """诊断接口：先制造一条预警，再诊断它"""
    client.post("/api/predict/20")  # unit=20 会触发严重预警
    with engine.connect() as conn:
        aid = conn.execute(
            text("SELECT id FROM alarm WHERE equipment_id=20 ORDER BY id DESC LIMIT 1")
        ).scalar()

    resp = client.post(f"/api/diagnose/{aid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["matched_count"] >= 1
    assert data["matched"][0]["rule_id"] == "A1"  # FD001 主故障模式应排第一

    # 清理测试数据，恢复设备状态
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM prediction WHERE equipment_id=20"))
        conn.execute(text("DELETE FROM alarm WHERE equipment_id=20"))
        conn.execute(text("UPDATE equipment SET status='健康' WHERE id=20"))
