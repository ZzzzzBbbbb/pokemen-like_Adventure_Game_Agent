# echo_backend/routers/history_api.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import json
import os

router = APIRouter(prefix="/api/v1/raising", tags=["聊天记录总线"])

# ==========================================
# 🚀 这就是【持久化存储层】的抽象接口预留
# 未来如果要换成 MySQL/Redis，仅需在这里重写这两个核心函数即可
# ==========================================
class ChatHistoryRepository:
    """临时用 JSON 文件模拟数据库表，未来将重构为真实的 SQL 操作"""
    def __init__(self, file_path: str = "server_storage/chat_history.json"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def load_history(self, pet_id: str, limit: int = 50) -> list:
        """
        TODO: 未来重构为 SQL (例如: SELECT * FROM chat_history WHERE pet_id=? ORDER BY time DESC LIMIT ?)
        目前：从 JSON 解析。
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            full_data = json.load(f)
        return full_data.get(pet_id, [])

    def save_message(self, pet_id: str, message: dict):
        """
        TODO: 未来重构为 SQL (例如: INSERT INTO chat_history (pet_id, sender, text, time) VALUES (?,?,?,?))
        目前：追加到 JSON 字典并进行简单的数组长度截断。
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            full_data = json.load(f)
            
        if pet_id not in full_data:
            full_data[pet_id] = []
            
        full_data[pet_id].append(message)
        
        # 保护机制：本地文件只存最新50条
        if len(full_data[pet_id]) > 50:
            full_data[pet_id] = full_data[pet_id][-50:]
            
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

# 实例化全局数据访问对象 (DAO)
db_repo = ChatHistoryRepository()


# ==========================================
# 📊 API 模型与路由层
# 这部分是暴露给外部 (Godot) 的契约，无论未来底层用什么数据库，这里的结构坚决不变
# ==========================================
class ChatMessage(BaseModel):
    sender: str  # 取值: "player" 或 "pet"
    name: str    # 用于界面展示的名字
    text: str    # 具体的对话内容
    time: str    # 格式如：14:30

class HistoryResponse(BaseModel):
    messages: List[ChatMessage]

@router.get("/history/{pet_id}", summary="拉取指定宠物的近期聊天记录", response_model=HistoryResponse)
async def get_chat_history(pet_id: str):
    """
    提供给 Godot 引擎侧边栏抽屉的数据源接口。
    不会进行语义联想分析，仅严格返回时间线上发生的事件。
    """
    messages = db_repo.load_history(pet_id)
    return HistoryResponse(messages=messages)


# 【给其他模块调用的便捷函数】 -> 供 main.py 中的互动路由直接调用
def append_to_history(pet_id: str, msg_dict: dict):
    """
    接收一个 msg_dict 格式并存入数据库，期望格式如下：
    {"sender": "player", "name": "玩家", "text": "你好", "time": "12:00"}
    """
    db_repo.save_message(pet_id, msg_dict)