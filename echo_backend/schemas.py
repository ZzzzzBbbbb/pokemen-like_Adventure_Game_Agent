# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

# ----- 事件类型枚举 -----
class EventType(Enum):
    # ===== 原有冒险类事件 =====
    ENCOUNTER = "encounter"      # 遭遇野怪/NPC
    GATHER = "gather"            # 采集资源
    REST = "rest"                # 休息恢复
    BATTLE = "battle"            # 战斗
    MYSTERY = "mystery"          # 奇遇/剧情事件
    OBSTACLE = "obstacle"        # 障碍需要克服
    TRADER = "trader"            # 遇到商人
    
    # ===== 🆕 模拟经营/建设类事件 =====
    SETTLEMENT_FOUND = "settlement_found"      # 发现可建立根据地的地点
    BUILD_CONSTRUCT = "build_construct"        # 建造/升级建筑
    BUILD_REPAIR = "build_repair"              # 修复损坏建筑
    RESOURCE_DEPOSIT = "resource_deposit"      # 发现资源矿脉/采集点
    SETTLEMENT_EVENT = "settlement_event"      # 根据地内部事件（幻灵互动/突发状况）
    
    # 📌 未来扩展：聚落发展阶段
    NPC_RECRUIT = "npc_recruit"                # 招募流浪 NPC 入驻
    TRADE_ROUTE = "trade_route"                # 建立贸易路线
    QUEST_BOARD = "quest_board"                # 发布/接收委托任务
    FESTIVAL = "festival"                      # 举办聚落庆典活动
    INVASION_DEFENSE = "invasion_defense"      # 防御外敌入侵
    EXPANSION = "expansion"                    # 扩张根据地范围


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


# ===== 🆕 模拟经营/根据地系统数据契约 =====

class BuildingInfo(BaseModel):
    """建筑信息 - 单个建筑的完整状态"""
    building_id: str = Field(..., description="建筑唯一 ID，如 'workshop_001'")
    building_type: str = Field(..., description="建筑类型，如 '帐篷', '工坊', '仓库', '训练场'")
    level: int = Field(default=1, description="建筑等级")
    status: str = Field(default="normal", description="状态：normal/damaged/under_construction")
    hp_current: int = Field(default=100, description="当前耐久")
    hp_max: int = Field(default=100, description="最大耐久")
    effects: Dict[str, float] = Field(default_factory=dict, description="建筑效果，如 {'storage_capacity': 100, 'crafting_speed': 1.2}")
    assigned_pets: List[str] = Field(default_factory=list, description="分配到此建筑的幻灵 ID 列表")
    constructed_at: str = Field(..., description="建造完成时间戳")

class ResourceNode(BaseModel):
    """资源点信息 - 地图上的可采集资源"""
    node_id: str = Field(..., description="资源点 ID")
    resource_type: str = Field(..., description="资源类型，如 '木材', '石矿', '以太泉'")
    abundance: int = Field(..., description="资源丰度，决定可采集次数")
    regen_rate: float = Field(..., description="每小时自然恢复量")
    difficulty: int = Field(default=1, description="采集难度，影响耗时和幻灵体力消耗")
    discovered: bool = Field(default=True, description="是否已发现")

class SettlementState(BaseModel):
    """根据地完整状态 - 存档核心结构"""
    settlement_id: str = Field(..., description="根据地 ID")
    name: str = Field(default="无名营地", description="根据地名称，可由玩家命名")
    level: int = Field(default=1, description="聚落等级，影响可建造建筑类型和 NPC 容量")
    prosperity: int = Field(default=0, description="繁荣度，由建筑/NPC/贸易等综合计算")
    
    # 建筑系统
    buildings: Dict[str, BuildingInfo] = Field(default_factory=dict, description="已建造建筑字典")
    building_queue: List[Dict] = Field(default_factory=list, description="建造队列，支持并行建造")
    
    # 资源系统
    resource_nodes: Dict[str, ResourceNode] = Field(default_factory=dict, description="已发现的资源点")
    storage: Dict[str, int] = Field(default_factory=dict, description="根据地仓库存储，独立于玩家背包")
    
    # NPC 系统（未来扩展）
    resident_npcs: List[str] = Field(default_factory=list, description="入驻 NPC 列表")
    visitor_npcs: List[str] = Field(default_factory=list, description="临时访客 NPC")
    
    # 状态标记
    is_established: bool = Field(default=False, description="是否已正式建立根据地")
    established_at: Optional[str] = Field(None, description="建立时间戳")
    last_tick_time: str = Field(..., description="上次结算时间，用于离线资源产出计算")

# ===== 建设相关请求/响应 =====

class SettlementActionRequest(BaseModel):
    """根据地行动请求 - 通用结构"""
    pet_state: PetState
    settlement_state: SettlementState
    action_type: str = Field(..., description="行动类型：found/build/repair/assign/collect")
    target_id: Optional[str] = Field(None, description="目标 ID，如建筑 ID 或资源点 ID")
    parameters: Dict = Field(default_factory=dict, description="额外参数，如建筑类型、分配幻灵等")

class SettlementActionResponse(BaseModel):
    """根据地行动响应"""
    success: bool = Field(..., description="行动是否成功")
    narrative: str = Field(..., description="大模型生成的叙事文本，带幻灵性格")
    settlement_changes: Dict = Field(default_factory=dict, description="根据地状态变化，用于前端更新")
    resource_cost: Dict[str, int] = Field(default_factory=dict, description="消耗的资源")
    resource_gain: Dict[str, int] = Field(default_factory=dict, description="获得的资源")
    mood_change: int = Field(default=0, description="幻灵心情变化")
    trust_change: int = Field(default=0, description="幻灵信任变化")
    unlock_flags: List[str] = Field(default_factory=list, description="解锁的新功能/建筑/区域标记")

class BuildConstructRequest(BaseModel):
    """建造/升级建筑请求"""
    pet_state: PetState
    settlement_state: SettlementState
    building_type: str = Field(..., description="要建造的建筑类型")
    location_id: str = Field(..., description="建造位置 ID")
    is_upgrade: bool = Field(default=False, description="是否为升级操作")
    target_building_id: Optional[str] = Field(None, description="升级时的目标建筑 ID")

class SettlementEventRequest(BaseModel):
    """根据地内部事件请求 - 类似离线挂机但发生在根据地"""
    pet_state: PetState
    settlement_state: SettlementState
    duration_hours: float = Field(..., description="事件持续时间")
    assigned_tasks: List[Dict] = Field(default_factory=list, description="幻灵被分配的任务列表")