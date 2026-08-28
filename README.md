# 工业设备智能运维与预测性维护平台

《制造智能技术》课程设计项目，采用 vibe coding（AI 协作）方式开发。

## 项目简介

面向制造场景中的设备运维环节，基于 NASA C-MAPSS 涡扇发动机退化数据集（FD001 子集），开发一套 B/S 架构的设备健康管理系统。

系统业务流程：设备台账 → 传感器数据监测 → 健康评估（剩余寿命 RUL 预测）→ 异常预警 → 智能诊断建议 → 维修工单，形成完整的预测性维护闭环。

## 涉及的课程技术方向

| 技术方向 | 具体方法                  | 在系统中的作用                     |
| -------- | ------------------------- | ---------------------------------- |
| 机器学习 | 随机森林回归              | 预测设备剩余寿命（RUL）            |
| 深度学习 | LSTM 时序网络             | 退化趋势建模，与随机森林对比       |
| 专家系统 | IF-THEN 规则引擎          | 根据异常征兆给出故障定位与排查建议 |
| 数据挖掘 | Isolation Forest 异常检测 | 发现传感器异常，驱动预警生成       |

## 技术栈

- 前端：Vue 3 + Element Plus + ECharts
- 后端：FastAPI（Python 3.10+）
- 数据库：SQLite
- 算法：scikit-learn + PyTorch（CPU 版）
- 测试：pytest

全部功能在一台个人电脑上本地运行，不依赖外部硬件和云服务器。

## 目录结构

```
Vibecodingproject/
├── backend/            # FastAPI 后端（接口、数据库、模型文件）
├── algorithms/         # 算法模块（RUL 预测、规则引擎、异常检测、数据入库）
├── frontend/           # Vue3 前端
├── data/               # C-MAPSS FD001 原始数据（train/test/RUL 三个文件；app.db 等生成文件不上传仓库）
├── docs/               # 项目文档（需求规格说明书、开发规则等）
├── tests/              # pytest 自动化测试
├── prompt/             # AI 会话记录备份（jsonl，每阶段同步更新）
├── 学习笔记.md          # 阶段1：AI 工具学习、harness 与模型选型、git 原理、选题调研
├── 选题说明.md          # 阶段2：题目、目标、技术方向（含业务闭环图、技术方向映射图）
├── 方案设计.md          # 阶段2：需求分析、方案论证、技术路线（含架构图）、计划
└── README.md
```

## 数据集说明

使用 NASA C-MAPSS 数据集的 FD001 子集（公开数据集）：

- `train_FD001.txt`：100 台发动机完整寿命数据，用于训练模型
- `test_FD001.txt`：100 台设备中途数据，模拟在役设备，用于系统演示
- `RUL_FD001.txt`：test 集真实剩余寿命，用于验证预测精度

来源链接：[NASA Prognostics Data Repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)（第 6 项，介绍页）；实际文件获取自 [GitHub 开源镜像](https://github.com/mapr-demos/predictive-maintenance/tree/master/notebooks/jupyter/Dataset/CMAPSSData)（NASA 官方直链已失效，内容一致）。

**数据预处理**：由 `algorithms/import_data.py` 完成——剔除 7 个恒定传感器列、min-max 归一化（参数存 `backend/models/scaler.pkl`）、构造 RUL 标签（截断 125）、导入 SQLite。预处理后的数据文件在 `data/processed/`（train_clean.csv / test_clean.csv），详细说明见 `data/README.md`。

## 运行方式

项目开发中，骨架搭好后补充启动步骤。

## 开发进度

- [x] D1~D2：工具配置、vibe coding 学习、选题调研（见 学习笔记.md）
- [x] D3~D5（方案文档）：选题说明、方案设计（含业务闭环图 / 架构图 / 技术方向映射图）、需求规格说明书
- [ ] D3~D5（收尾）：前后端骨架搭建与联通
- [x] 阶段3（数据准备）：数据集与预处理结果入库 `data/`、`data/README.md` 说明、`prompt/` 会话记录备份（每阶段同步更新）
- [ ] D6：数据清洗入库 SQLite、随机森林模型训练（输出 MAE/RMSE）
- [ ] D7~D8：后端接口、前端页面、算法模块接入
- [ ] D9：集成测试、设计报告、演示视频
- [ ] D10：答辩
