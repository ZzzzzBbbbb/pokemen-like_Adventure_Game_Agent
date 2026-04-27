# tools/config/generation_rules.py
# =============================================================================
# 📐 生成规则配置 - 标准化生成约束
# =============================================================================

# 城市生成规则
CITY_RULES = {
    "count": 7,
    "id_format": "C{index}",
    "fusion_count": 5,  # 融合5个现实城市
    "max_reuse": 2,     # 每个现实城市最多被融合2次
    "required_fields": [
        "name", "description", "cultural_tags", "landscape_features",
        "architectural_style", "local_specialties", "security_level",
        "population", "districts", "event_pool", "disaster_impact"
    ],
    "constraints": {
        "security_range": [2.5, 4.5],
        "population_range": [5000, 20000],
        "prosperity_range": [20, 65],
        "style": "第一次工业革命初期，蒸汽萌芽，人力为主，无高科技",
        "tone": "积极正面，希望与重建，中立偏暖",
        "forbidden": ["政治", "宗教", "信仰", "现代科技", "魔法", "属性克制"]
    }
}

# 城镇生成规则
TOWN_RULES = {
    "count": 10,
    "id_format": "R{index}",
    "fusion_count": 3,  # 融合3个现实城镇/乡村
    "max_reuse": 2,
    "required_fields": [
        "name", "description", "cultural_tags", "landscape_features",
        "local_specialties", "security_level", "disaster_severity",
        "event_pool", "disaster_impact"
    ],
    "constraints": {
        "security_range": [1.0, 3.0],
        "disaster_severity_range": [3, 5],
        "prosperity_range": [10, 40],
        "style": "受灾严重，治安混乱，资源匮乏，需要帮助",
        "tone": "困境中仍有希望，人情温暖"
    }
}

# 道路生成规则
ROAD_RULES = {
    "difficulty_weights": {
        1: 0.15, 2: 0.20, 3: 0.25,  # 疏通 60%
        4: 0.15, 5: 0.15, 6: 0.10   # 开辟 40%
    },
    "node_count_by_difficulty": {
        1: [3, 5], 2: [4, 6], 3: [5, 7],
        4: [6, 8], 5: [7, 9], 6: [8, 10]
    },
    "event_type_weights": {
        "combat": 0.30,      # 兽灾/盗匪
        "gather": 0.20,      # 采集资源
        "obstacle": 0.15,    # 障碍需克服
        "rest": 0.10,        # 休息点
        "mystery": 0.10,     # 奇遇/剧情
        "trader": 0.08,      # 流动商人
        "construction": 0.05, # 修路/建设
        "disaster": 0.02     # 天灾残留
    },
    "security_init_range": [0.0, 2.5],  # 初始治安度较低
    "constraints": {
        "style": "战胜人祸兽灾，躲避天灾，修路建设，积极冒险",
        "forbidden": ["无意义死亡", "过度黑暗", "绝望叙事"]
    }
}

# 宠物生成规则
PET_RULES = {
    "count": 12,
    "id_format": "P{index}",
    "major_parts": 3,   # 3个大部位
    "minor_parts": 5,   # 5个小部位
    "required_fields": [
        "pet_id", "pet_name", "species", "potential", "persona",
        "attributes", "parts", "skills", "ecology"
    ],
    "constraints": {
        "potential_range": [30, 80],
        "style": "灵气进化，开智，可能暴躁，符合生态逻辑",
        "combat": "纯物理伤害，近程/远程区分，无属性克制",
        "evolution": "部位进化，随机可重复，重复概率低"
    }
}

# 世界观约束（通用）
WORLDVIEW_CONSTRAINTS = {
    "era": "大灾变后，第一次工业革命初期",
    "tech_level": "蒸汽萌芽，人力为主，机械辅助，无高科技",
    "energy": "灵气（暂名，后期套科学概念）",
    "tone": "希望与破碎并存，积极健康，中立偏正面",
    "theme": "文明重建，大航海机遇，冒险与羁绊",
    "forbidden_elements": [
        "政治敏感", "宗教争议", "现代科技产品",
        "魔法系统", "属性克制", "过度血腥"
    ]
}