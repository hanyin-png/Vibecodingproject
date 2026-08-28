# -*- coding: utf-8 -*-
"""数据库连接：SQLite。

注意：数据库路径基于本文件的位置拼出来，
这样无论在哪个目录启动后端，都能找到 data/app.db。
"""
import os

from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/ 目录
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "app.db"))
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False)


def create_business_tables():
    """建业务表：prediction / alarm / work_order（IF NOT EXISTS，重复执行无害）。

    设备台账和传感器数据两张表由 algorithms/import_data.py 建，
    这三张业务表由后端启动时建。
    """
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prediction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER,   -- 对应 equipment.id
                rul REAL,               -- 预测剩余寿命（循环数）
                health_score REAL,      -- 健康度评分 0~100
                method TEXT,            -- 使用的模型：random_forest / lstm
                created_at TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alarm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER,
                alarm_type TEXT,        -- 传感器异常 / 剩余寿命不足
                level TEXT,             -- 提示 / 警告 / 严重
                message TEXT,
                status TEXT,            -- 未处理 / 已处理
                created_at TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS work_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alarm_id INTEGER,       -- 来源预警
                equipment_id INTEGER,
                title TEXT,
                suggestion TEXT,        -- 规则引擎给出的诊断建议
                status TEXT,            -- 待处理 / 维修中 / 已完成
                created_at TEXT
            )
        """))
