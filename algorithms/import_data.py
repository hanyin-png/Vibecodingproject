# -*- coding: utf-8 -*-
"""C-MAPSS FD001 数据清洗入库脚本。

做的事：
1. 读取 data/ 下的原始 txt 文件（空格分隔、无表头，每行 26 列）；
2. 加上列名：unit, cycle, setting1~3, s1~s21；
3. 把 test 集（跑到一半的数据，模拟在役设备）的原始数据导入 sensor_data 表；
4. 生成 100 台设备台账，写入 equipment 表；
5. 用 train 集拟合 min-max 归一化参数，存到 backend/models/scaler.pkl。

注意：库里存的是原始值；归一化只在建模/推理时做，且必须用这里存的 scaler。
"""
import os
import sys

import joblib
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import text

sys.stdout.reconfigure(encoding="utf-8")  # Windows 终端中文不乱码

# ---------- 路径 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # algorithms/
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
MODEL_DIR = os.path.join(ROOT_DIR, "backend", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT_DIR, "backend"))
from database import engine  # noqa: E402  复用后端的绝对路径数据库连接

# ---------- 列定义 ----------
COLUMNS = ["unit", "cycle", "setting1", "setting2", "setting3"] + [
    f"s{i}" for i in range(1, 22)
]
# FD001 中从头到尾数值不变的 7 个传感器列（无信息量，建模时剔除）
CONSTANT_SENSORS = ["s1", "s5", "s6", "s10", "s16", "s18", "s19"]
SENSOR_COLS = [f"s{i}" for i in range(1, 22)]
USED_SENSORS = [c for c in SENSOR_COLS if c not in CONSTANT_SENSORS]


def load_txt(filename):
    """读取一个 C-MAPSS 原始文件，返回带列名的 DataFrame"""
    path = os.path.join(DATA_DIR, filename)
    return pd.read_csv(path, sep=r"\s+", header=None, names=COLUMNS)


def create_tables():
    """建表：设备台账 + 传感器数据（已存在则先清空重建，保证脚本可重复运行）"""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS sensor_data"))
        conn.execute(text("DROP TABLE IF EXISTS equipment"))
        conn.execute(text("""
            CREATE TABLE equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,      -- 设备编号，如 ENG-001
                model TEXT,            -- 型号
                install_date TEXT,     -- 投运日期
                status TEXT            -- 健康状态：健康/预警/故障
            )
        """))
        conn.execute(text("""
            CREATE TABLE sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit INTEGER,          -- 设备编号（对应 test 集 unit）
                cycle INTEGER,         -- 循环数
                setting1 REAL, setting2 REAL, setting3 REAL,
                s1 REAL, s2 REAL, s3 REAL, s4 REAL, s5 REAL, s6 REAL, s7 REAL,
                s8 REAL, s9 REAL, s10 REAL, s11 REAL, s12 REAL, s13 REAL,
                s14 REAL, s15 REAL, s16 REAL, s17 REAL, s18 REAL, s19 REAL,
                s20 REAL, s21 REAL
            )
        """))


def main():
    train_df = load_txt("train_FD001.txt")  # 完整寿命数据：训练用
    test_df = load_txt("test_FD001.txt")    # 中途数据：模拟在役设备，入库存演示
    print(f"train 集 {len(train_df)} 行，test 集 {len(test_df)} 行")

    # 1. 建表
    create_tables()

    # 2. test 集原始数据 -> sensor_data 表
    test_df.to_sql("sensor_data", engine, if_exists="append", index=False)

    # 3. 生成 100 台设备台账 -> equipment 表
    units = sorted(test_df["unit"].unique())
    equipment = pd.DataFrame({
        "code": [f"ENG-{u:03d}" for u in units],
        "model": "Turbofan 涡扇发动机",
        "install_date": "2024-01-01",
        "status": "健康",
    })
    equipment.to_sql("equipment", engine, if_exists="append", index=False)

    # 4. 用 train 集拟合归一化参数并保存（建模只用 14 个有效传感器列）
    scaler = MinMaxScaler()
    scaler.fit(train_df[USED_SENSORS])
    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)

    print(f"sensor_data 入库 {len(test_df)} 行，equipment 入库 {len(equipment)} 台")
    print(f"归一化参数已保存：{scaler_path}（覆盖 {len(USED_SENSORS)} 个有效传感器列）")


if __name__ == "__main__":
    main()
