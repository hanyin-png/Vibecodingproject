# -*- coding: utf-8 -*-
"""后端入口：FastAPI 应用与各模块路由注册"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import alarms, anomaly, diagnose, equipment, predict, sensor, workorders

app = FastAPI(title="工业设备智能运维与预测性维护平台")

# 允许前端开发服务器（Vite 默认 5173 端口）跨域访问本后端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册各模块路由
app.include_router(equipment.router)
app.include_router(sensor.router)
app.include_router(predict.router)
app.include_router(diagnose.router)
app.include_router(alarms.router)
app.include_router(anomaly.router)
app.include_router(workorders.router)

# 启动时确保业务表（prediction / alarm / work_order）存在
from database import create_business_tables  # noqa: E402

create_business_tables()


@app.get("/api/hello")
def hello():
    """骨架验证接口：前端能拿到这段 JSON，就说明前后端链路是通的"""
    return {"message": "后端联通成功", "project": "工业设备智能运维与预测性维护平台"}
