# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# ----- 养成状态基础模型 -----
class PetState(BaseModel):
    pet_id: str = Field(..., description="引擎生成的全服唯一ID，方便记忆系统关联")
    pet_name: str
    species: str
    element: str
    # level: int = Field(..., description="当前等级")
    hp: int = Field(..., description="当前血量")
    persona: str # 例如：傲娇、胆小、贪吃
    trust_level: int = Field(..., description="好感度(0-100)")
    mood: int = Field(..., description="心情值(0-100)")

# -------------- 泛化的战斗请求包 ----------------
class BattleTacticRequest(BaseModel):
    # 幻灵(宝可梦)基础设定
    pet_state: PetState
    
    # 环境与敌人设定
    enemy_desc: str       # 引擎传过来的怪物描述 (例: "满血、狂暴、火属性的巨猿")
    env_tags: List[str]   # 战场上的可用交互物 (例: ["毒池", "尖锐钟乳石", "易燃藤蔓"])
    
    # 玩家指令
    player_input: str     # 玩家在屏幕上打的字
    
    # 引擎许可的动作池 (限制 AI 不能瞎扯不存在的技能)
    allowed_skills: List[Dict]  # (例: ["SKILL_THUNDER_STRIKE", "ACT_FLEE", "ENV_INTERACT"])

# -------------- 回传给引擎的响应包 ----------------
class BattleActionResponse(BaseModel):
    thought_process: str
    dialogue: str
    action_decision: str
    emotion_delta: int       # -10 到 10
    skill_to_invoke: str     # 从 allowed_skills 里选出来的 ID (如没事就发 NONE)
    target_object: str       # 发动技能的对象



# ----- 1. 聊天与交互 (Chat & Interact) -----
class RaisingInteractRequest(BaseModel):
    pet_state: PetState
    action_type: str = Field(..., description="交互类型，如: chat(聊天), feed(喂食), pet(抚摸)")
    user_input: Optional[str] = Field(None, description="玩家说的话或给的物品名称")

class RaisingInteractResponse(BaseModel):
    dialogue: str = Field(..., description="宠物说的话或动作描述")
    mood_change: int = Field(..., description="心情变化量，如 5 或 -2")
    trust_change: int = Field(..., description="好感度变化量")
    is_refused: bool = Field(..., description="是否拒绝了玩家的交互（比如傲娇性格低好感度时拒绝吃东西）")

# ----- 2. 离线任务 (Offline Task) -----
class OfflineTaskRequest(BaseModel):
    pet_state: PetState
    duration_hours: float = Field(..., description="挂机总时长(小时)")
    environment_desc: str = Field("当前营地", description="离线所在环境")
    player_message: Optional[str] = Field(None, description="主人下线前的留言指令")

class TaskResult(BaseModel):
    task_name: str = Field(..., description="引擎合法的任务名(如: 采集草药/体能特训)")
    cost_hours: float = Field(..., description="该任务消耗的时间")
    journal: str = Field(..., description="该任务阶段的第一人称日记")
    reward_items: Dict[str, int] = Field(..., description="具体获得的物品与数量")

class OfflineTaskResponse(BaseModel):
    summary_journal: str = Field(..., description="对整个挂机过程的最终总结留言")
    completed_tasks: List[TaskResult] = Field(default_factory=list, description="完整执行完的任务列单")
    total_stamina_consumed: int = Field(..., description="总共消耗的体力")
    injury_status: Optional[str] = Field(None, description="是否受伤，如 '扭伤了脚'，没受伤为 null")

# ----- 3. 场景专属探索任务 (Location Task) -----
class LocationTaskRequest(BaseModel):
    pet_state: PetState
    location_category: str  # 场景大类：如 "town" (城镇), "wild" (野外)
    specific_node: str      # 具体节点：如 "酒馆", "铁匠铺", "外围草地", "训练场"
    action_type: str        # 任务类型：如 "打工", "采药", "站岗", "特训"
    duration_hours: float   # 任务耗时

class LocationTaskResponse(BaseModel):
    task_report: str               # 任务结束后宠物给出的汇报(LLM生成)
    reward_items: List[str]        # 获得的资源/道具
    mood_change: int
    trust_change: int
    hp_change: int                 # 比如打怪特训可能会掉血

# ----- 4. 邮件与好友系统 (Mail System) -----
class MailCheckRequest(BaseModel):
    pet_state: PetState
    # 未来可加入 player_id 等以查询真实数据库

class MailEntity(BaseModel):
    sender: str
    title: str
    content: str
    attached_items: List[str]

class MailCheckResponse(BaseModel):
    mails: List[MailEntity]        # 查收到的邮件列表