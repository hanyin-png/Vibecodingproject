# -*- coding: utf-8 -*-
"""数据可视化：画出单台设备关键传感器随循环数的退化趋势图。

用途：数据说明文档配图、设计报告"数据资源构建"章节插图。
挑 train 集中 1 号发动机，画 4 个有趋势的传感器（s2/s3/s7/s11）。
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")  # 不弹窗，直接存图
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from import_data import load_txt  # noqa: E402

# Windows 上让 matplotlib 正常显示中文和负号
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 要画的传感器：编号 -> 物理含义（FD001 中有明显退化趋势的列）
SENSORS = {
    "s2": "低压压气机出口温度 T24",
    "s3": "高压压气机出口温度 T30",
    "s7": "高压压气机出口总压 P30",
    "s11": "高压压气机出口静压 Ps30",
}


def main():
    train_df = load_txt("train_FD001.txt")
    # 取 1 号发动机从健康到失效的完整数据
    unit1 = train_df[train_df["unit"] == 1].sort_values("cycle")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (col, label) in zip(axes.flat, SENSORS.items()):
        ax.plot(unit1["cycle"], unit1[col], linewidth=1)
        ax.set_title(f"{col}：{label}")
        ax.set_xlabel("循环数")
        ax.set_ylabel("原始读数")
        ax.grid(alpha=0.3)
    fig.suptitle("C-MAPSS FD001：1 号发动机关键传感器退化趋势（从健康到失效）")
    fig.tight_layout()

    out_path = os.path.join(BASE_DIR, "..", "data", "传感器退化趋势图.png")
    fig.savefig(out_path, dpi=150)
    print(f"图已保存：{os.path.abspath(out_path)}")


if __name__ == "__main__":
    main()
