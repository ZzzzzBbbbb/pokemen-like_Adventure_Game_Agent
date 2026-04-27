# schemas.py
# =============================================================================
# 🌍 Project Echo - 全功能数据契约
# 风格定位：第一次工业革命初期（蒸汽萌芽、人力为主、机械辅助）
# =============================================================================

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# ===== 基础枚举 =====

class SettlementType(str, Enum):
    CITY = "city"
    TOWN = "town"
    SETTLEMENT = "settlement"

class SettlementStatus(str, Enum):
    RUINED = "ruined"
    REBUILDING = "rebuilding"
    STABLE = "stable"
    PROSPERING = "prospering"

class RoadDifficulty(int, Enum):
    EASY_CLEAR = 1
    MEDIUM_CLEAR = 2
    HARD_CLEAR = 3
    EASY_PIONEER = 4
    MEDIUM_PIONEER = 5
    HARD_PIONEER = 6

class NodeType(str, Enum):
    COMBAT = "combat"
    GATHER = "gather"
    OBSTACLE = "obstacle"
    REST = "rest"
    MYSTERY = "mystery"
    TRADER = "trader"
    CONSTRUCTION = "construction"
    DISASTER = "disaster"

class BuildingCategory(str, Enum):
    SERVICE = "service"
    PRODUCTION = "production"
    INFRASTRUCTURE = "infrastructure"
    SPECIAL = "special"

class EventType(str, Enum):
    ENCOUNTER = "encounter"
    GATHER = "gather"
    REST = "rest"
    BATTLE = "battle"
    MYSTERY = "mystery"
    OBSTACLE = "obstacle"
    TRADER = "trader"
    # 模拟经营类
    SETTLEMENT_FOUND = "settlement_found"
    BUILD_CONSTRUCT = "build_construct"
    BUILD_REPAIR = "build_repair"
    RESOURCE_DEPOSIT = "resource_deposit"
    SETTLEMENT_EVENT = "settlement_event"
    NPC_RECRUIT = "npc_recruit"
    TRADE_ROUTE = "trade_route"
    QUEST_BOARD = "quest_board"
    FESTIVAL = "festival"
    INVASION_DEFENSE = "invasion_defense"
    EXPANSION = "expansion"

# ===== 宠物系统 =====

class PetAttributes(BaseModel):
    level: int = Field(default=1)
    hp: int
    hp_max: int
    attack: int
    defense: int
    speed: int
    skill_proficiency: Dict[str, int] = Field(default_factory=dict)

class PetPart(BaseModel):
    part_name: str
    is_major: bool
    evolved_count: int = Field(default=0)
    bonus: Dict[str, float] = Field(default_factory=dict)

class PetState(BaseModel):
    pet_id: str
    pet_name: str
    species: str
    element: str = Field(default="")
    potential: int = Field(default=50)
    persona: str
    attributes: PetAttributes
    parts: Dict[str, PetPart] = Field(default_factory=dict)
    trust_level: int = Field(default=50, ge=0, le=100)
    mood: int = Field(default=50, ge=0, le=100)
    hunger: int = Field(default=100, ge=0, le=100)
    thirst: int = Field(default=100, ge=0, le=100)
    skills: List[str] = Field(default_factory=list)
    status_effects: List[Dict] = Field(default_factory=list)

# ===== 互动系统 =====

class RaisingInteractRequest(BaseModel):
    pet_state: PetState
    action_type: str
    user_input: str

class RaisingInteractResponse(BaseModel):
    dialogue: str
    mood_change: int
    trust_change: int
    is_refused: bool = False

# ===== 离线挂机系统 =====

class OfflineTaskRequest(BaseModel):
    pet_state: PetState
    duration_hours: float
    environment_desc: str = Field(default="当前营地")
    player_message: Optional[str] = None

class TaskResult(BaseModel):
    task_name: str
    cost_hours: float
    journal: str
    reward_items: Dict[str, int]

class OfflineTaskResponse(BaseModel):
    summary_journal: str
    completed_tasks: List[TaskResult] = Field(default_factory=list)
    total_stamina_consumed: int
    injury_status: Optional[str] = None

# ===== 场景任务系统 =====

class LocationTaskRequest(BaseModel):
    pet_state: PetState
    location_category: str
    specific_node: str
    action_type: str
    duration_hours: float

class LocationTaskResponse(BaseModel):
    task_report: str
    reward_items: List[str]
    mood_change: int
    trust_change: int
    hp_change: int

# ===== 邮件系统 =====

class MailCheckRequest(BaseModel):
    pet_state: PetState
    # 未来可加入 player_id 等以查询真实数据库

class MailEntity(BaseModel):
    sender: str
    title: str
    content: str
    attached_items: List[str]

class MailCheckResponse(BaseModel):
    mails: List[MailEntity]

# ===== 聚集地与道路系统 =====

class LocationBase(BaseModel):
    location_id: str
    location_type: SettlementType
    name: str
    description: str
    cultural_tags: List[str] = Field(default_factory=list)
    landscape_features: List[str] = Field(default_factory=list)
    architectural_style: str = Field(default="")
    local_specialties: List[str] = Field(default_factory=list)
    security_level: float = Field(default=3.0, ge=0.0, le=6.0)
    population: int = Field(default=0)
    prosperity: int = Field(default=0)
    status: SettlementStatus = Field(default=SettlementStatus.REBUILDING)
    available_buildings: List[str] = Field(default_factory=list)
    constructed_buildings: Dict[str, int] = Field(default_factory=dict)
    resource_production: Dict[str, int] = Field(default_factory=dict)
    trade_routes: List[str] = Field(default_factory=list)
    event_pool: List[str] = Field(default_factory=list)
    disaster_impact: str = Field(default="")
    coordinates: Optional[Dict[str, float]] = None
    connected_roads: List[str] = Field(default_factory=list)

class CityInfo(LocationBase):
    location_type: SettlementType = SettlementType.CITY
    districts: List[str] = Field(default_factory=list)
    city_guard_level: int = Field(default=1, ge=1, le=5)
    reconstruction_progress: float = Field(default=0.0, ge=0.0, le=1.0)

class TownInfo(LocationBase):
    location_type: SettlementType = SettlementType.TOWN
    disaster_severity: int = Field(default=3, ge=1, le=5)
    awakened_children: int = Field(default=0)
    local_hero: Optional[str] = None

class SettlementInfo(LocationBase):
    location_type: SettlementType = SettlementType.SETTLEMENT
    founder: str = Field(default="player")
    established_at: Optional[str] = None
    pioneer_conditions: Dict[str, any] = Field(default_factory=dict)
    development_stage: int = Field(default=0, ge=0, le=5)

class NodeInfo(BaseModel):
    node_id: str
    node_index: int
    node_type: NodeType
    event_name: str
    event_description: str
    event_options: List[Dict[str, str]] = Field(default_factory=list)
    min_security: float = Field(default=0.0)
    max_security: float = Field(default=6.0)
    required_items: List[str] = Field(default_factory=list)
    rewards: Dict[str, int] = Field(default_factory=dict)
    security_change: float = Field(default=0.0)
    exp_reward: int = Field(default=0)
    is_cleared: bool = Field(default=False)
    cleared_count: int = Field(default=0)

class RoadInfo(BaseModel):
    road_id: str
    name: str
    description: str
    from_location: str
    to_location: str
    is_bidirectional: bool = Field(default=True)
    difficulty: RoadDifficulty
    security_level: float = Field(default=0.0, ge=0.0, le=6.0)
    is_blocked: bool = Field(default=True)
    is_pioneered: bool = Field(default=False)
    node_count: int
    nodes: List[NodeInfo] = Field(default_factory=list)
    base_food_cost: int = Field(default=5)
    base_water_cost: int = Field(default=3)
    danger_level: int = Field(default=1, ge=1, le=5)
    pioneer_requirements: Dict[str, any] = Field(default_factory=dict)
    last_patrol_time: Optional[str] = None
    patrol_bonus: float = Field(default=0.0)

class BuildingTemplate(BaseModel):
    building_type: str
    category: BuildingCategory
    name: str
    description: str
    min_settlement_level: int = Field(default=1)
    prerequisite_buildings: List[str] = Field(default_factory=list)
    construction_cost: Dict[str, int]
    construction_time_hours: float = Field(default=1.0)
    max_level: int = Field(default=5)
    level_up_costs: Dict[int, Dict[str, int]] = Field(default_factory=dict)
    effects: Dict[str, float] = Field(default_factory=dict)
    unlock_features: List[str] = Field(default_factory=list)
    production_items: List[str] = Field(default_factory=list)
    production_rate: float = Field(default=1.0)
    service_types: List[str] = Field(default_factory=list)
    service_costs: Dict[str, int] = Field(default_factory=dict)

class BuildingInstance(BaseModel):
    instance_id: str
    building_type: str
    location_id: str
    level: int = Field(default=1)
    status: str = Field(default="normal")
    hp_current: int = Field(default=100)
    hp_max: int = Field(default=100)
    constructed_at: str
    assigned_workers: List[str] = Field(default_factory=list)
    production_progress: float = Field(default=0.0)
    stored_output: Dict[str, int] = Field(default_factory=dict)

class WorldMapState(BaseModel):
    cities: Dict[str, CityInfo] = Field(default_factory=dict)
    towns: Dict[str, TownInfo] = Field(default_factory=dict)
    settlements: Dict[str, SettlementInfo] = Field(default_factory=dict)
    roads: Dict[str, RoadInfo] = Field(default_factory=dict)
    discovered_locations: List[str] = Field(default_factory=list)
    current_location: str = Field(default="R0")
    current_road: Optional[str] = None
    current_node: Optional[int] = None
    global_security: float = Field(default=0.0)
    civilization_progress: float = Field(default=0.0)
    last_update_time: str

# ===== 请求/响应模型 =====

class SettlementActionRequest(BaseModel):
    pet_state: PetState
    settlement_state: dict
    action_type: str
    target_id: Optional[str] = None
    parameters: Dict = Field(default_factory=dict)

class SettlementActionResponse(BaseModel):
    success: bool
    narrative: str
    settlement_changes: Dict = Field(default_factory=dict)
    resource_cost: Dict[str, int] = Field(default_factory=dict)
    resource_gain: Dict[str, int] = Field(default_factory=dict)
    mood_change: int = Field(default=0)
    trust_change: int = Field(default=0)
    unlock_flags: List[str] = Field(default_factory=list)

class BuildConstructRequest(BaseModel):
    pet_state: PetState
    settlement_state: dict
    building_type: str
    location_id: str
    is_upgrade: bool = Field(default=False)
    target_building_id: Optional[str] = None

class SettlementEventRequest(BaseModel):
    pet_state: PetState
    settlement_state: dict
    duration_hours: float
    assigned_tasks: List[Dict] = Field(default_factory=list)

class RoadAdvanceRequest(BaseModel):
    pet_state: dict
    road_id: str
    direction: str = Field(default="forward")
    expedition_mode: bool = Field(default=False)

class RoadAdvanceResponse(BaseModel):
    success: bool
    new_node: int
    triggered_event: Optional[NodeInfo] = None
    resource_consumption: Dict[str, int] = Field(default_factory=dict)
    narrative: str