@echo off
chcp 65001 >nul
REM ==================================================
REM 一键启动：工业设备智能运维与预测性维护平台
REM 双击运行。会自动初始化数据库（首次）、启动后端和前端。
REM 注意：下面的 Anaconda 路径如果换了电脑，需要改成对应电脑上的实际路径。
REM ==================================================

set CONDA_ACTIVATE=D:\admin\Anaconda\Scripts\activate.bat
set ENV_NAME=phm

cd /d %~dp0

REM ① 数据库不存在时先初始化（data\app.db 不上传仓库，克隆后必跑）
if not exist data\app.db (
    echo [提示] 未找到数据库，正在初始化数据（约1分钟）...
    call %CONDA_ACTIVATE% %ENV_NAME%
    python algorithms\import_data.py
)

REM ② 启动后端（新窗口）
start "PHM-后端 FastAPI :8000" cmd /k "call %CONDA_ACTIVATE% %ENV_NAME% && cd backend && python -m uvicorn main:app --port 8000"

REM ③ 启动前端（新窗口）
start "PHM-前端 Vite :5173" cmd /k "cd frontend && npm run dev"

echo.
echo 后端: http://127.0.0.1:8000/api/equipment
echo 前端: http://localhost:5173
echo 两个服务窗口请保持开启，关闭即停止服务。
pause
