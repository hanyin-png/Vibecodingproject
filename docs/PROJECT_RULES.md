# PROJECT_RULES.md · 项目规则（AI 协作者必读）

> 本文件是项目的单一事实来源。AI 参与本项目任何开发/写作任务前必须先读本文件。
> 需求变更时先改本文件，再改代码。

## 1. 项目一句话

用 NASA C-MAPSS 涡扇发动机数据集（FD001 子集），做 B/S 架构设备健康管理系统：

**设备台账 → 数据监测 → 健康评估(RUL) → 异常预警 → 规则引擎诊断 → 维修工单**

这条业务闭环是演示主线，必须能完整走通。评分侧重架构完整与业务闭环，而非功能数量。

## 2. 技术栈（已冻结，不得更换）

- 前端：Vue 3 + Element Plus + ECharts
- 后端：FastAPI（Python 3.10+），RESTful API
- 数据库：SQLite（`data/app.db`）
- 算法：scikit-learn + PyTorch（CPU 版），离线训练存模型文件，运行时只加载推理
- 测试：pytest（`tests/`）
- 工具：git + GitHub；Kimi Code + Kimi K3

**依赖克制**：不引入本文件之外的框架和重依赖（不要 Celery / Redis / Docker / 外部规则引擎框架）。

## 3. 目录结构

```
Vibecodingproject/
├── backend/            # FastAPI 后端
│   ├── main.py         # 入口与路由（必须配置 CORS 允许 localhost:5173）
│   ├── database.py     # 数据库连接与建表（用基于文件位置的绝对路径）
│   ├── models/         # 训练好的模型文件（.pkl/.pth）
│   └── routers/        # 各模块 API
├── algorithms/         # 算法模块
│   ├── rul_rf.py       # 模块1：随机森林 RUL
│   ├── rul_lstm.py     # 模块2：LSTM RUL（可降级为只出报告数据）
│   ├── rules_engine.py # 模块3：诊断规则引擎
│   ├── anomaly.py      # 模块4：异常检测
│   └── import_data.py  # 数据清洗入库脚本
├── frontend/           # Vue3 前端
├── data/               # C-MAPSS 原始数据与 app.db
├── tests/              # pytest
├── prompt/             # AI 会话记录备份（jsonl，每阶段同步更新）
├── docs/
│   ├── PROJECT_RULES.md    # 本文件
│   └── 需求规格说明书.md
├── README.md
└── requirements.txt
```

## 4. 四个算法模块（≥3 个技术方向的硬性要求，装饰性引入不算数）

| 模块 | 技术方向 | 文件 | 模型文件 |
|---|---|---|---|
| 随机森林 RUL 预测 | 机器学习 | `algorithms/rul_rf.py` | `backend/models/rf_rul.pkl` |
| LSTM RUL 预测 | 深度学习 | `algorithms/rul_lstm.py` | `backend/models/lstm_rul.pth` |
| 故障诊断规则引擎 | 专家系统（IF-THEN，15~30 条，字典/列表实现，不引框架） | `algorithms/rules_engine.py` | — |
| Isolation Forest 异常检测 | 数据挖掘（驱动预警生成） | `algorithms/anomaly.py` | `backend/models/isoforest.pkl` |

调用链：异常检测发现问题 → RUL 评估严重度 → 规则引擎给建议 → 工单闭环。

## 5. 数据库（5 张表）

- **equipment**：id / code 唯一（ENG-001~ENG-100，对应 unit）/ model / install_date / status（健康/预警/故障）
- **sensor_data**：id / unit / cycle / setting1~3 / s1~s21（存原始值，归一化在建模时做）
- **prediction**：id / equipment_id / rul / health_score（0~100）/ method / created_at
- **alarm**：id / equipment_id / alarm_type（传感器异常/剩余寿命不足）/ level（提示/警告/严重）/ message / status / created_at
- **work_order**：id / alarm_id / equipment_id / title / suggestion（来自规则引擎）/ status（待处理/维修中/已完成）/ created_at

## 6. 数据处理关键规则（违反必出 bug）

1. 只用 C-MAPSS **FD001**；train 训练、test 模拟在役设备做演示、RUL_FD001 验证；
2. 剔除 7 个恒定传感器列：`s1, s5, s6, s10, s16, s18, s19`，建模只用 14 列；
3. RUL 标签 = 该 unit 的 max(cycle) − 当前 cycle，截断到 **125**；
4. 健康度评分统一公式：`health_score = max(0, min(100, rul / 125 * 100))`；
5. 归一化用训练集 min/max，**scaler 必须 joblib 存盘**（`backend/models/scaler.pkl`），推理用同一个；
6. 预警阈值统一：RUL ≤ 30 严重；30 < RUL ≤ 60 警告；60 < RUL ≤ 90 提示。

## 7. 开发规则（每次生成代码必须遵守）

1. **先读再改**：改任何文件前先读现有内容，禁止凭空重写整个文件；
2. **小步实现**：一次只做一个功能点，每步给出验证方法（命令 + 预期输出），人类验证通过再下一步；
3. **代码可讲解**：全中文注释、写法朴素、禁止炫技——答辩时老师随机指代码段让学生讲；
4. **禁止造假**：禁止 mock 数据冒充功能（数据必须真实来自 SQLite 或模型推理）；
5. **测试同步**：每个后端接口和算法模块写 pytest 用例；
6. **出错止损**：同一 bug 连续两次修不好，停止再改，给出最小复现和原因分析，交人类决策；
7. **过程留痕**：每完成一个功能点提醒 git 小步提交（commit 说明写清干了什么，禁止 "update"）；关键 prompt 与 AI 出错案例备份到 `prompt/`（jsonl 会话记录 + 截图）。

## 8. 新手必踩的坑（预防清单）

1. FastAPI 必须加 `CORSMiddleware` 允许 `http://localhost:5173`；
2. PyTorch 装 CPU 版：`pip install torch --index-url https://download.pytorch.org/whl/cpu`；
3. npm 卡死换源：`npm config set registry https://registry.npmmirror.com`；
4. 项目路径避免中文和空格；
5. SQLite 路径用基于 `__file__` 的绝对路径，不要依赖启动目录；
6. 前端调后端的 baseURL 写成可配置项（5173 被占时 Vite 会换端口）；
7. Windows 终端打印中文乱码：脚本开头 `sys.stdout.reconfigure(encoding='utf-8')`；
8. GitHub push 失败优先换手机热点，别在代理配置上耗超过 10 分钟。

## 9. 常用命令

```bash
# 后端启动（backend/ 目录）
uvicorn main:app --reload
# 测试（项目根目录）
pytest tests/ -v
# 前端（frontend/ 目录）
npm install && npm run dev
# 接口验证示例
curl http://127.0.0.1:8000/api/equipment
```
