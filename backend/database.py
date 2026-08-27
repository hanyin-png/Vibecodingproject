# -*- coding: utf-8 -*-
"""数据库连接：SQLite。

注意：数据库路径基于本文件的位置拼出来，
这样无论在哪个目录启动后端，都能找到 data/app.db。
"""
import os

from sqlalchemy import create_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/ 目录
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "app.db"))
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False)
