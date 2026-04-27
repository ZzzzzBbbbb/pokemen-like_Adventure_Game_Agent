# tools/ai4road.py
# =============================================================================
# 🛤️ 道路 AI 生成器
# 根据连接的两端聚集地生成道路与节点
# =============================================================================

import json
import os
import sys
import random
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from resource_pool import get_resource_pool
from config.generation_rules import ROAD_RULES, WORLDVIEW_CONSTRAINTS
from your_llm_client import call_llm, extract_json

class RoadGenerator:
    """道路生成器"""
    
    def __init__(self):
        self.pool = get_resource_pool()
        self.output_dir = os.path.join(os.path.dirname(__file__), "output")
        self._load_locations()
    
    def _load_locations(self):
        """加载已生成的聚集地"""
        cities_file = os.path.join(self.output_dir, "cities.json")
        towns_file = os.path.join(self.output_dir, "towns.json")
        
        self.locations = {}
        
        if os.path.exists(cities_file):
            with open(cities_file, 'r', encoding='utf-8') as f:
                for city in json.load(f):
                    self.locations[city['location_id']] = city
        
        if os.path.exists(towns_file):
            with open(towns_file, 'r', encoding='utf-8') as f:
                for town in json.load(f):
                    self.locations[town['location_id']] = town
        
        print(f"📍 加载 {len(self.locations)} 个聚集地")
    
    def generate_road(self, road_id: str, from_loc: str, to_loc: str) -> Dict:
        """生成单条道路"""
        if self.pool.is_generated(road_id):
            print(f"⚠️ {road_id} 已存在，跳过")
            return None
        
        if from_loc not in self.locations or to_loc not in self.locations:
            print(f"❌ 聚集地不存在: {from_loc} -> {to_loc}")
            return None
        
        from_data = self.locations[from_loc]
        to_data = self.locations[to_loc]
        
        # 随机决定难度
        difficulty = self._sample_difficulty()
        
        # 决定节点数量
        min_n, max_n = ROAD_RULES['node_count_by_difficulty'][difficulty]
        node_count = random.randint(min_n, max_n)
        
        # 构建 Prompt
        prompt = self._build_road_prompt(road_id, from_data, to_data, difficulty, node_count)
        
        print(f"🛤️ 生成 {road_id}: {from_loc} -> {to_loc} (难度{difficulty}, {node_count}节点)")
        response = call_llm(prompt)
        result = extract_json(response)
        
        # 补全字段
        result = self._complete_road(result, road_id, from_loc, to_loc, difficulty, node_count)
        
        # 记录
        tags = [f"road_{difficulty}", from_loc, to_loc]
        self.pool.record_fusion([from_loc, to_loc], road_id, 'road', tags)
        
        return result
    
    def _sample_difficulty(self) -> int:
        """根据权重采样难度"""
        weights = ROAD_RULES['difficulty_weights']
        difficulties = list(weights.keys())
        probs = list(weights.values())
        return random.choices(difficulties, weights=probs)[0]
    
    def _build_road_prompt(self, road_id: str, from_loc: Dict, to_loc: Dict, 
                           difficulty: int, node_count: int) -> str:
        """构建道路生成 Prompt"""
        difficulty_desc = {
            1: "简单疏通 - 道路基本完好，少量障碍",
            2: "中等疏通 - 部分损毁，需清理",
            3: "困难疏通 - 严重损毁，大量障碍",
            4: "简单开辟 - 需开辟新路径，地形较平缓",
            5: "中等开辟 - 地形复杂，需克服自然障碍",
            6: "困难开辟 - 极端地形，危险重重"
        }
        
        return f"""
你是一个游戏关卡设计师。请为连接两个聚集地的道路生成配置。

【起点】{from_loc['location_id']} - {from_loc['name']}
描述: {from_loc['description']}
地貌: {', '.join(from_loc.get('landscape_features', []))}
特产: {', '.join(from_loc.get('local_specialties', []))}

【终点】{to_loc['location_id']} - {to_loc['name']}
描述: {to_loc['description']}
地貌: {', '.join(to_loc.get('landscape_features', []))}
特产: {', '.join(to_loc.get('local_specialties', []))}

【道路参数】
- 道路ID: {road_id}
- 难度: {difficulty} ({difficulty_desc[difficulty]})
- 节点数量: {node_count}

【生成要求】
1. 道路名称和描述要体现两端聚集地的特色和连接关系
2. 节点事件要与两端背景相关，体现:
   - 战胜人祸（盗匪/犯罪）
   - 战胜兽灾（野兽袭击）
   - 躲避天灾（地震/洪水/飓风残留）
   - 修路建设（疏通/开辟/驿站）
3. 事件类型分布参考:
   {json.dumps(ROAD_RULES['event_type_weights'], ensure_ascii=False)}
4. 初始治安度较低: {ROAD_RULES['security_init_range']}
5. 禁止: {', '.join(ROAD_RULES['constraints']['forbidden'])}

【输出格式】
必须返回严格 JSON:
{{
    "road_id": "{road_id}",
    "name": "道路名称",
    "description": "道路描述",
    "difficulty": {difficulty},
    "node_count": {node_count},
    "security_level": 1.5,
    "is_blocked": true,
    "is_pioneered": false,
    "base_food_cost": 5,
    "base_water_cost": 3,
    "danger_level": 3,
    "nodes": [
        {{
            "node_index": 0,
            "node_type": "combat",
            "event_name": "事件名称",
            "event_description": "事件描述",
            "event_options": [{{"option_text": "选项", "effect_hint": "效果提示"}}],
            "rewards": {{"物品": 数量}},
            "security_change": 0.2,
            "exp_reward": 50
        }}
    ]
}}
"""
    
    def _complete_road(self, result: Dict, road_id: str, from_loc: str, 
                       to_loc: str, difficulty: int, node_count: int) -> Dict:
        """补全道路字段"""
        result['road_id'] = road_id
        result['from_location'] = from_loc
        result['to_location'] = to_loc
        result['is_bidirectional'] = True
        result['difficulty'] = difficulty
        result['node_count'] = node_count
        
        # 补全节点字段
        for i, node in enumerate(result.get('nodes', [])):
            node['node_id'] = f"{road_id}_N{i}"
            node['node_index'] = i
            node.setdefault('min_security', 0.0)
            node.setdefault('max_security', 6.0)
            node.setdefault('required_items', [])
            node.setdefault('is_cleared', False)
            node.setdefault('cleared_count', 0)
        
        # 确保节点数量
        while len(result.get('nodes', [])) < node_count:
            result['nodes'].append(self._generate_fallback_node(road_id, len(result['nodes'])))
        
        result.setdefault('pioneer_requirements', {})
        result.setdefault('last_patrol_time', None)
        result.setdefault('patrol_bonus', 0.0)
        
        return result
    
    def _generate_fallback_node(self, road_id: str, index: int) -> Dict:
        """生成备用节点（LLM生成不足时）"""
        return {
            "node_id": f"{road_id}_N{index}",
            "node_index": index,
            "node_type": "gather",
            "event_name": "资源发现",
            "event_description": "你发现了一些可用的资源。",
            "event_options": [],
            "rewards": {"木材": 2},
            "security_change": 0.0,
            "exp_reward": 20,
            "is_cleared": False,
            "cleared_count": 0
        }
    
    def generate_road_network(self, connections: List[Tuple[str, str]]) -> List[Dict]:
        """生成道路网络"""
        roads = []
        for idx, (from_loc, to_loc) in enumerate(connections):
            road_id = f"L{idx}"
            result = self.generate_road(road_id, from_loc, to_loc)
            if result:
                roads.append(result)
        return roads
    
    def save_results(self, roads: List[Dict]):
        """保存道路结果"""
        with open(os.path.join(self.output_dir, "roads.json"), 'w', encoding='utf-8') as f:
            json.dump(roads, f, ensure_ascii=False, indent=2)
        print(f"✅ 保存 {len(roads)} 条道路到 roads.json")
        self.pool.save()


def main():
    generator = RoadGenerator()
    
    # 定义道路连接（可根据需要调整）
    connections = [
        ("R0", "C0"), ("C0", "R1"), ("R1", "C1"),
        ("C1", "R2"), ("R2", "C2"), ("C2", "R3"),
        ("R0", "R4"), ("R4", "C3"), ("C3", "R5"),
        ("R5", "C4"), ("C4", "R6"), ("R6", "C5"),
        ("C5", "R7"), ("R7", "C6"), ("C6", "R8"),
        ("R8", "R9"), ("R9", "C0"),
    ]
    
    print("=" * 60)
    print("🛤️ 开始生成道路网络")
    print("=" * 60)
    
    roads = generator.generate_road_network(connections)
    generator.save_results(roads)


if __name__ == "__main__":
    main()