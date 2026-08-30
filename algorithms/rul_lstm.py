# -*- coding: utf-8 -*-
"""模块2：LSTM 时序建模预测 RUL（深度学习路线，与随机森林对比）。

做法：
- 滑动窗口：长度 30 循环 × 14 个有效传感器，标签 = 窗口末尾的 RUL；
- 网络：两层 LSTM（隐藏维度 64，层间 Dropout 0.2）+ 全连接层输出寿命值；
- 数据纪律同随机森林：train 集训练、test 集评估，绝不混用；
- CPU 训练，几分钟跑完。

按保底策略：本模块只产出报告对比数据，不接进系统接口。
"""
import os
import sys

import joblib
import numpy as np
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # algorithms/
sys.path.insert(0, BASE_DIR)
from import_data import USED_SENSORS, load_txt  # noqa: E402
from rul_rf import add_rul_label  # noqa: E402

ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
MODEL_DIR = os.path.join(ROOT_DIR, "backend", "models")

WINDOW = 30       # 滑动窗口长度
EPOCHS = 30       # 训练轮数
BATCH = 64
torch.manual_seed(42)
np.random.seed(42)


class LSTMRulModel(nn.Module):
    """两层 LSTM + 全连接：输入 (批次, 30, 14)，输出剩余寿命"""

    def __init__(self, n_features):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features, hidden_size=64,
            num_layers=2, dropout=0.2, batch_first=True,
        )
        self.fc = nn.Linear(64, 1)

    def forward(self, x):
        out, _ = self.lstm(x)      # out: (批次, 30, 64)
        last = out[:, -1, :]       # 取最后一个时间步的输出
        return self.fc(last).squeeze(-1)


def make_windows(df, with_label):
    """把每台设备的数据切成 (样本数, 30, 14) 的窗口张量"""
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    X_all, y_all = [], []
    for _, group in df.groupby("unit"):
        group = group.sort_values("cycle")
        values = scaler.transform(group[USED_SENSORS])
        for end in range(WINDOW, len(group) + 1):
            X_all.append(values[end - WINDOW:end])
            if with_label:
                y_all.append(group["rul"].values[end - 1])
    X = torch.tensor(np.array(X_all), dtype=torch.float32)
    y = torch.tensor(np.array(y_all), dtype=torch.float32) if with_label else None
    return X, y


def main():
    # 1. 准备训练数据（train 集，带 RUL 标签）
    train_df = add_rul_label(load_txt("train_FD001.txt"))
    X_train, y_train = make_windows(train_df, with_label=True)
    print(f"训练样本：{X_train.shape[0]} 个，窗口形状：{tuple(X_train.shape[1:])}")

    # 2. 训练
    model = LSTMRulModel(n_features=len(USED_SENSORS))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.MSELoss()
    loader = DataLoader(TensorDataset(X_train, y_train), batch_size=BATCH, shuffle=True)
    model.train()
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(xb)
        if epoch % 10 == 0:
            print(f"epoch {epoch:3d}/{EPOCHS}  训练损失 MSE = {total_loss / len(X_train):.1f}")

    # 3. test 集评估：每台设备取它最后一个窗口
    test_df = load_txt("test_FD001.txt")
    X_last = []
    for _, group in test_df.groupby("unit"):
        group = group.sort_values("cycle")
        if len(group) >= WINDOW:
            X_last.append(group.iloc[-WINDOW:])
    # 手动拼最后窗口（带 scaler 归一化）
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    X_test = torch.tensor(
        np.array([scaler.transform(g[USED_SENSORS]) for g in X_last]),
        dtype=torch.float32,
    )
    model.eval()
    with torch.no_grad():
        rul_pred = model(X_test).numpy()
    rul_true = np.loadtxt(os.path.join(ROOT_DIR, "data", "RUL_FD001.txt"))

    mae = mean_absolute_error(rul_true, rul_pred)
    rmse = np.sqrt(mean_squared_error(rul_true, rul_pred))
    print(f"LSTM  test 集：MAE = {mae:.2f}，RMSE = {rmse:.2f}")
    print(f"随机森林对照组：MAE = 11.84，RMSE = 15.50")

    # 4. 保存模型
    model_path = os.path.join(MODEL_DIR, "lstm_rul.pth")
    torch.save(model.state_dict(), model_path)
    print(f"模型已保存：{model_path}")


if __name__ == "__main__":
    main()
