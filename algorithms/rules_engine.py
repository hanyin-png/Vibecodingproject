# -*- coding: utf-8 -*-
"""模块3：故障诊断规则引擎（专家系统）。

形式：IF-THEN 正向推理，用字典列表定义规则，不引入外部规则框架。
输入：异常传感器列表 + 当前 RUL + 预警类型
输出：疑似故障部位 + 分层排查步骤（先软后硬、先外后内）+ 维修措施

规则分三类：
A 类：部件级故障规则（按异常传感器组合判断疑似故障部位）
B 类：寿命阈值规则（按 RUL 分级给出处置建议）
C 类：通用兜底规则（部件规则都不命中时的分层排查思路）
"""

# 每条规则：id / priority（数字越小越优先）/ condition（命中条件）
#          / fault（疑似故障部位）/ steps（分层排查步骤）/ action（维修措施）
RULES = [
    # ---------- A 类：部件级故障规则 ----------
    {
        "id": "A1", "priority": 1,
        "fault": "高压压气机（HPC）退化（FD001 主故障模式，多传感器确认）",
        "condition": lambda s, rul, t: {"s7", "s11", "s12"} <= s,
        "steps": ["① 排除传感器漂移（互换传感器或对比历史基线）",
                  "② 查 HPC 出口总压/静压实测值，确认性能衰减",
                  "③ 内窥镜检查压气机叶片磨损、积垢情况"],
        "action": "安排停机检修 HPC，必要时更换叶片",
    },
    {
        "id": "A2", "priority": 2,
        "fault": "疑似高压压气机（HPC）退化（部分传感器异常）",
        "condition": lambda s, rul, t: {"s7", "s11"} <= s,
        "steps": ["① 先核对 s7/s11 传感器读数是否漂移",
                  "② 持续监测 s12（燃油流量比值）是否联动异常",
                  "③ 趋势确认后安排内窥镜检查"],
        "action": "加强监测，纳入近期检修计划",
    },
    {
        "id": "A3", "priority": 3,
        "fault": "排气温度异常 / 涡轮效率下降",
        "condition": lambda s, rul, t: {"s3", "s4"} <= s,
        "steps": ["① 核对工况参数（setting1~3）是否变化",
                  "② 查燃油系统供油是否异常",
                  "③ 检查涡轮导向器与叶片"],
        "action": "清洗或检修涡轮部件",
    },
    {
        "id": "A4", "priority": 4,
        "fault": "转子系统异常（不平衡/轴承磨损）",
        "condition": lambda s, rul, t: {"s8", "s9"} <= s,
        "steps": ["① 查振动监测数据是否同步异常",
                  "② 查轴承温度与润滑状态",
                  "③ 做转子动平衡检查"],
        "action": "轴承更换或动平衡校正",
    },
    {
        "id": "A5", "priority": 5,
        "fault": "转速波动异常（单转速传感器，疑似早期转子问题）",
        "condition": lambda s, rul, t: bool({"s8", "s9"} & s),
        "steps": ["① 先排除转速传感器本身故障",
                  "② 对比另一路转速信号是否一致",
                  "③ 持续监测振动与轴承温度"],
        "action": "视复查结果决定是否检修",
    },
    {
        "id": "A6", "priority": 6,
        "fault": "冷却引气系统泄漏",
        "condition": lambda s, rul, t: bool({"s20", "s21"} & s),
        "steps": ["① 查引气管路有无泄漏点",
                  "② 查阀门密封状态"],
        "action": "管路密封检修",
    },
    {
        "id": "A7", "priority": 7,
        "fault": "风扇/外涵道系统异常",
        "condition": lambda s, rul, t: "s15" in s,
        "steps": ["① 查风扇叶片有无损伤",
                  "② 查外涵道压力是否正常"],
        "action": "风扇系统检修",
    },
    {
        "id": "A8", "priority": 8,
        "fault": "转速传感器故障（非设备本体故障）",
        "condition": lambda s, rul, t: bool({"s13", "s14"} & s) and not ({"s8", "s9"} & s),
        "steps": ["① 互换传感器验证读数是否跟随传感器走",
                  "② 查信号线缆与接插件"],
        "action": "更换传感器，无需动设备本体",
    },
    {
        "id": "A9", "priority": 9,
        "fault": "低压压气机（LPC）效率下降",
        "condition": lambda s, rul, t: "s2" in s,
        "steps": ["① 查 LPC 进口有无异物堵塞",
                  "② 查级间密封状态"],
        "action": "LPC 清洗检修",
    },
    # ---------- B 类：寿命阈值规则 ----------
    {
        "id": "B1", "priority": 10,
        "fault": "剩余寿命严重不足（RUL ≤ 30）",
        "condition": lambda s, rul, t: rul <= 30,
        "steps": ["① 立即评估停机窗口",
                  "② 调取近期传感器趋势复核退化速度",
                  "③ 准备备件与检修人力"],
        "action": "立即安排停机检修，生成最高优先级工单",
    },
    {
        "id": "B2", "priority": 11,
        "fault": "剩余寿命偏低（30 < RUL ≤ 60）",
        "condition": lambda s, rul, t: 30 < rul <= 60,
        "steps": ["① 纳入本周检修计划",
                  "② 提高监测频次（每班一次健康评估）"],
        "action": "一周内安排检修",
    },
    {
        "id": "B3", "priority": 12,
        "fault": "剩余寿命开始缩短（60 < RUL ≤ 90）",
        "condition": lambda s, rul, t: 60 < rul <= 90,
        "steps": ["① 关注退化趋势，每周评估一次",
                  "② 下次定检时复查关键传感器"],
        "action": "纳入下次定检计划",
    },
    # ---------- C 类：通用兜底规则（先软后硬、先外后内） ----------
    {
        "id": "C1", "priority": 20,
        "fault": "传感器异常但寿命正常：优先怀疑测量链路而非设备本体",
        "condition": lambda s, rul, t: bool(s) and rul > 90,
        "steps": ["① 先怀疑传感器本身：查读数是否跳变/卡死",
                  "② 查数据采集链路与接线",
                  "③ 都排除后才怀疑设备本体"],
        "action": "检修或更换传感器，设备本体继续观察",
    },
    {
        "id": "C2", "priority": 21,
        "fault": "多传感器同时异常：先查共性原因",
        "condition": lambda s, rul, t: len(s) >= 3,
        "steps": ["① 先查是否工况切换（setting1~3 是否突变）",
                  "② 再查数据采集系统是否故障",
                  "③ 最后才按部件逐一排查"],
        "action": "排除共性原因后重新评估",
    },
    {
        "id": "C3", "priority": 99,
        "fault": "暂无明确故障特征",
        "condition": lambda s, rul, t: True,  # 永远命中，作为兜底
        "steps": ["① 偶发异常：连续监测 3 个循环，复现才升级",
                  "② 保持现有巡检节奏"],
        "action": "暂不处理，持续观察",
    },
]


def diagnose(abnormal_sensors, rul, alarm_type=""):
    """正向推理：逐条匹配规则，返回命中的诊断结果（按优先级排序）。

    参数：
        abnormal_sensors: 异常传感器编号列表，如 ['s7', 's11']
        rul: 当前预测的剩余寿命
        alarm_type: 预警类型（传感器异常 / 剩余寿命不足）
    """
    s = set(abnormal_sensors)
    matched = []
    for rule in RULES:
        if rule["condition"](s, rul, alarm_type):
            matched.append({
                "rule_id": rule["id"],
                "fault": rule["fault"],
                "steps": rule["steps"],
                "action": rule["action"],
            })
    # 按 priority 排序（数字越小越靠前）
    order = {rule["id"]: rule["priority"] for rule in RULES}
    matched.sort(key=lambda r: order[r["rule_id"]])
    # C3 是兜底规则：有其他规则命中时就不展示了
    if len(matched) > 1 and matched[-1]["rule_id"] == "C3":
        matched = matched[:-1]
    return {
        "abnormal_sensors": sorted(s),
        "rul": rul,
        "matched": matched,
        "matched_count": len(matched),
    }
