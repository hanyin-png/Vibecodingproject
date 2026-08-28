# -*- coding: utf-8 -*-
"""设备台账接口：设备的增删改查"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from database import engine

router = APIRouter(prefix="/api/equipment", tags=["设备台账"])


class EquipmentIn(BaseModel):
    """新增/修改设备时前端传过来的字段"""
    code: str                                  # 设备编号，如 ENG-001
    model: str = "Turbofan 涡扇发动机"          # 型号
    install_date: str = "2024-01-01"           # 投运日期
    status: str = "健康"                        # 健康状态


@router.get("")
def list_equipment():
    """查询全部设备列表"""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM equipment ORDER BY id")
        ).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def create_equipment(item: EquipmentIn):
    """新增一台设备"""
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT id FROM equipment WHERE code = :code"), {"code": item.code}
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail=f"设备编号 {item.code} 已存在")
        conn.execute(
            text("INSERT INTO equipment (code, model, install_date, status) "
                 "VALUES (:code, :model, :install_date, :status)"),
            item.model_dump(),
        )
    return {"message": f"设备 {item.code} 添加成功"}


@router.put("/{equipment_id}")
def update_equipment(equipment_id: int, item: EquipmentIn):
    """修改设备信息"""
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE equipment SET code=:code, model=:model, "
                 "install_date=:install_date, status=:status WHERE id=:id"),
            {**item.model_dump(), "id": equipment_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="设备不存在")
    return {"message": "修改成功"}


@router.delete("/{equipment_id}")
def delete_equipment(equipment_id: int):
    """删除设备"""
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM equipment WHERE id=:id"), {"id": equipment_id}
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="设备不存在")
    return {"message": "删除成功"}
