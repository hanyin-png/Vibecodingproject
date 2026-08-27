# -*- coding: utf-8 -*-
"""模块1：随机森林 RUL 预测（训练 + 评估 + 保存模型）。

特征工程：
- 每台设备取长度 20 的滑动窗口；
- 对 14 个有效传感器列各算 4 个统计量：均值、标准差、末值、趋势斜率；
- 再加上窗口末尾的 cycle，共 14×4 + 1 = 57 维特征；
- 标签 = 窗口末尾对应的 RUL（最大循环数 − 当前循环数，截断到 125）。

数据纪律：train 集训练，test 集评估，两者绝不混用。
"""
import os
import sys

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

sys.stdout.reconfigure(encoding="utf-8")  # Windows 终端中文不乱码

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # algorithms/
sys.path.insert(0, BASE_DIR)
from import_data import USED_SENSORS, load_txt  # noqa: E402  复用读取函数与列定义

ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
MODEL_DIR = os.path.join(ROOT_DIR, "backend", "models")

RUL_CAP = 125   # RUL 标签上限（健康初期退化信号弱，截断防标签失真）
WINDOW = 20     # 滑动窗口长度（取最近 20 个循环）


def add_rul_label(df):
    """给训练数据加 RUL 标签：该设备最大 cycle − 当前 cycle，截断到 125"""
    max_cycle = df.groupby("unit")["cycle"].transform("max")
    df = df.copy()
    df["rul"] = (max_cycle - df["cycle"]).clip(upper=RUL_CAP)
    return df


def window_stats(window):
    """对一个 (20, 14) 的窗口算统计量：均值、标准差、末值、斜率，拼成 56 维"""
    means = window.mean(axis=0)
    stds = window.std(axis=0)
    lasts = window[-1]
    # 每列对时间做一次线性拟合，斜率反映这个传感器在窗口内是上升还是下降
    slopes = np.polyfit(np.arange(WINDOW), window, 1)[0]
    return np.concatenate([means, stds, lasts, slopes])


def extract_features(df):
    """滑动窗口提取特征。返回特征矩阵 X 和标签 y（没有 rul 列时 y 为 None）"""
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    X, y = [], []
    for _, group in df.groupby("unit"):
        group = group.sort_values("cycle")
        values = scaler.transform(group[USED_SENSORS])  # 用入库时保存的同一个 scaler
        cycles = group["cycle"].values
        ruls = group["rul"].values if "rul" in group.columns else None
        # 从第 WINDOW 个循环开始，每个位置取它之前 20 个循环做一个样本
        for end in range(WINDOW, len(group) + 1):
            stats = window_stats(values[end - WINDOW:end])
            X.append(np.concatenate([stats, [cycles[end - 1]]]))
            if ruls is not None:
                y.append(ruls[end - 1])
    return np.array(X), (np.array(y) if y else None)


def extract_last_window(df):
    """推理用：每台设备只取它"跑到今天为止"的最后一个窗口"""
    X, units = [], []
    for unit, group in df.groupby("unit"):
        group = group.sort_values("cycle")
        if len(group) < WINDOW:
            continue  # 数据不足一个窗口，跳过
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        values = scaler.transform(group[USED_SENSORS])
        stats = window_stats(values[-WINDOW:])
        X.append(np.concatenate([stats, [group["cycle"].values[-1]]]))
        units.append(unit)
    return np.array(X), units


def main():
    # 1. 训练集：加标签 -> 提特征
    train_df = add_rul_label(load_txt("train_FD001.txt"))
    X_train, y_train = extract_features(train_df)
    print(f"训练样本：{X_train.shape[0]} 个，特征维度：{X_train.shape[1]}")

    # 2. 训练随机森林（限制深度和叶子样本数：控制模型文件体积，防止过拟合）
    model = RandomForestRegressor(
        n_estimators=100, max_depth=12, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # 3. test 集评估：每台在役设备取最后一个窗口，预测结果和真实 RUL 对比
    test_df = load_txt("test_FD001.txt")
    X_test, _ = extract_last_window(test_df)
    rul_true = np.loadtxt(os.path.join(ROOT_DIR, "data", "RUL_FD001.txt"))
    rul_pred = model.predict(X_test)

    mae = mean_absolute_error(rul_true, rul_pred)
    rmse = np.sqrt(mean_squared_error(rul_true, rul_pred))
    print(f"test 集评估：MAE = {mae:.2f}，RMSE = {rmse:.2f}（单位：循环数）")

    # 4. 保存模型
    model_path = os.path.join(MODEL_DIR, "rf_rul.pkl")
    joblib.dump(model, model_path)
    print(f"模型已保存：{model_path}")


if __name__ == "__main__":
    main()
