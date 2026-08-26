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
├── data/               # C-MAPSS 原始数据与 app.db（数据文件不上传仓库）
├── tests/              # pytest 自动化测试
├── prompt日志/          # vibe coding 过程档案（prompt 记录、AI 出错案例）
├── 选题说明.md          # 阶段交付：题目、目标、技术方向
├── 方案设计.md          # 阶段交付：需求分析、方案论证、技术路线、计划
├── 需求规格说明书.md     # 系统需求规格
├── PROJECT_RULES.md    # 项目开发规则（AI 协作约定）
└── README.md
```

## 数据集说明

使用 NASA C-MAPSS 数据集的 FD001 子集：

- `train_FD001.txt`：100 台发动机完整寿命数据，用于训练模型
- `test_FD001.txt`：100 台设备中途数据，模拟在役设备，用于系统演示
- `RUL_FD001.txt`：test 集真实剩余寿命，用于验证预测精度

获取渠道：飞桨 AI Studio / 魔搭 ModelScope 搜索"C-MAPSS"，或 [NASA Prognostics Data Repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/) 第 6 项。

## 运行方式

项目开发中，骨架搭好后补充启动步骤。

## 开发进度

- [x] D1~D2：工具配置、vibe coding 学习、选题调研（见 学习笔记.md）
- [x] D3~D5：选题说明、方案设计、需求规格说明书
