# -*- coding: utf-8 -*-
"""模块4：异常检测（数据挖掘）。

方法：IsolationForest（孤立森林）在 train 集的"健康前段"数据上训练——
设备刚投运、退化还不明显的时期视为正常样本。运行时判断设备最近的
数据是否异常，异常则自动在 alarm 表生成"传感器异常"预警。

原理一句话：随机切分特征空间，正常点要切很多刀才能被孤立，
异常点切几刀就被分出来了，所以异常点的平均路径更短。
"""
import os
import sys

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # algorithms/
sys.path.insert(0, BASE_DIR)
from import_data import USED_SENSORS, load_txt  # noqa: E402

ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
MODEL_DIR = os.path.join(ROOT_DIR, "backend", "models")

HEALTHY_RATIO = 0.3   # 取每台设备前 30% 循环作为"健康样本"训练
WINDOW = 20           # 检测时看最近 20 个循环的均值


def train():
    """训练孤立森林并保存模型。只在健康前段数据上拟合（无监督）"""
    train_df = load_txt("train_FD001.txt")
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))

    healthy_rows = []
    for _, group in train_df.groupby("unit"):
        group = group.sort_values("cycle")
        n_healthy = max(10, int(len(group) * HEALTHY_RATIO))
        healthy_rows.append(group.iloc[:n_healthy])
    healthy_df = np.concatenate(
        [scaler.transform(g[USED_SENSORS]) for g in healthy_rows]
    )
    print(f"健康样本：{healthy_df.shape[0]} 行 × {healthy_df.shape[1]} 个传感器")

    model = IsolationForest(
        n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1
    )
    model.fit(healthy_df)

    model_path = os.path.join(MODEL_DIR, "isoforest.pkl")
    joblib.dump(model, model_path)
    print(f"模型已保存：{model_path}")


def detect(df):
    """检测设备最近的运行状态。

    参数 df：某台设备的传感器数据（DataFrame，含 cycle 和传感器列）
    返回：(是否异常, 异常传感器列表, 异常分数)
    """
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    model = joblib.load(os.path.join(MODEL_DIR, "isoforest.pkl"))

    recent = df.sort_values("cycle").iloc[-WINDOW:]
    values = scaler.transform(recent[USED_SENSORS])

    # 孤立森林对最近窗口逐点打分：-1 异常，1 正常
    preds = model.predict(values)
    scores = model.score_samples(values)  # 分数越低越异常
    is_anomaly = bool((preds == -1).any())

    # 3σ 辅助标注：用设备"自己的健康时期"（前 30% 循环）做基线，
    # 最近窗口均值偏离基线超过 3σ 的传感器列出来。
    # 为什么不用全 fleet 基线：不同设备的出厂基线差异比单台退化幅度还大，
    # 用自己的历史比，灵敏度才够。
    abnormal_sensors = []
    if is_anomaly:
        full = df.sort_values("cycle")
        baseline = full.iloc[: max(5, int(len(full) * 0.3))]
        base_values = scaler.transform(baseline[USED_SENSORS])
        base_mean = base_values.mean(axis=0)
        base_std = base_values.std(axis=0)
        recent_mean = values.mean(axis=0)
        for i, col in enumerate(USED_SENSORS):
            if base_std[i] > 0 and abs(recent_mean[i] - base_mean[i]) > 3 * base_std[i]:
                abnormal_sensors.append(col)

    return is_anomaly, abnormal_sensors, float(scores.min())


if __name__ == "__main__":
    train()
