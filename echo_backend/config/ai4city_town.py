# tools/ai4city_town.py
# =============================================================================
# 🌍 城市/城镇 AI 生成器
# 融合现实城市文化特色，生成符合世界观的聚集地
# =============================================================================

import json
import os
import sys
import random
from typing import List, Dict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from resource_pool import get_resource_pool
from config.generation_rules import CITY_RULES, TOWN_RULES, WORLDVIEW_CONSTRAINTS

# 假设你有 LLM 客户端
from your_llm_client import call_llm, extract_json

class CityTownGenerator:
    """城市/城镇生成器"""
    
    def __init__(self):
        self.pool = get_resource_pool()
        self.output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(self.output_dir, exist_ok=True)
        self._load_source_data()
    
    def _load_source_data(self):
        """加载现实城市/城镇源数据"""
        cities_file = os.path.join(os.path.dirname(__file__), "config", "real_cities.json")
        towns_file = os.path.join(os.path.dirname(__file__), "config", "real_towns.json")
        
        with open(cities_file, 'r', encoding='utf-8') as f:
            self.cities = json.load(f)
        with open(towns_file, 'r', encoding='utf-8') as f:
            self.towns = json.load(f)
        
        # 注册到资源池
        for city in self.cities:
            self.pool.register_source(
                city['id'], 'city', 
                city.get('tags', []) + city.get('cultural_features', [])
            )
        for town in self.towns:
            self.pool.register_source(
                town['id'], 'town',
                town.get('tags', []) + town.get('cultural_features', [])
            )
    
    def generate_city(self, city_index: int) -> Dict:
        """生成单个城市"""
        city_id = CITY_RULES['id_format'].format(index=city_index)
        
        if self.pool.is_generated(city_id):
            print(f"⚠️ {city_id} 已存在，跳过")
            return None
        
        # 从资源池获取可用的现实城市
        source_ids = self.pool.get_available_sources(
            'city', 
            CITY_RULES['fusion_count'],
            max_reuse=CITY_RULES['max_reuse']
        )
        
        if len(source_ids) < CITY_RULES['fusion_count']:
            print(f"❌ 可用城市源不足，需要 {CITY_RULES['fusion_count']} 个，只有 {len(source_ids)} 个")
            return None
        
        # 获取源城市详细信息
        source_cities = [c for c in self.cities if c['id'] in source_ids]
        
        # 构建 Prompt
        prompt = self._build_city_prompt(source_cities, city_id)
        
        # 调用 LLM
        print(f"🏙️ 生成 {city_id}，融合: {[c['name'] for c in source_cities]}")
        response = call_llm(prompt)
        result = extract_json(response)
        
        # 验证并补全字段
        result = self._validate_and_complete(result, city_id, 'city')
        
        # 记录到资源池
        tags = result.get('cultural_tags', []) + result.get('landscape_features', [])
        self.pool.record_fusion(source_ids, city_id, 'city', tags)
        
        return result
    
    def generate_town(self, town_index: int) -> Dict:
        """生成单个城镇"""
        town_id = TOWN_RULES['id_format'].format(index=town_index)
        
        if self.pool.is_generated(town_id):
            print(f"⚠️ {town_id} 已存在，跳过")
            return None
        
        source_ids = self.pool.get_available_sources(
            'town',
            TOWN_RULES['fusion_count'],
            max_reuse=TOWN_RULES['max_reuse']
        )
        
        if len(source_ids) < TOWN_RULES['fusion_count']:
            print(f"❌ 可用城镇源不足")
            return None
        
        source_towns = [t for t in self.towns if t['id'] in source_ids]
        prompt = self._build_town_prompt(source_towns, town_id)
        
        print(f"🏘️ 生成 {town_id}，融合: {[t['name'] for t in source_towns]}")
        response = call_llm(prompt)
        result = extract_json(response)
        
        result = self._validate_and_complete(result, town_id, 'town')
        
        tags = result.get('cultural_tags', []) + result.get('landscape_features', [])
        self.pool.record_fusion(source_ids, town_id, 'town', tags)
        
        return result
    
    def _build_city_prompt(self, source_cities: List[Dict], city_id: str) -> str:
        """构建城市生成 Prompt"""
        sources_desc = "\n".join([
            f"- {c['name']}: {c['description']} | 文化: {', '.join(c.get('cultural_features', []))} | "
            f"地貌: {', '.join(c.get('landscape', []))} | 特产: {', '.join(c.get('specialties', []))}"
            for c in source_cities
        ])
        
        return f"""
你是一个游戏世界构建专家。请融合以下 {len(source_cities)} 个现实城市的文化特色，生成一个游戏城市配置。

【源城市信息】
{sources_desc}

【生成要求】
1. 城市ID: {city_id}
2. 只提取文化/风景/地理/历史建筑/饮食元素，融合创造新城市
3. 严格符合世界观:
   - 时代: {WORLDVIEW_CONSTRAINTS['era']}
   - 技术: {WORLDVIEW_CONSTRAINTS['tech_level']}
   - 基调: {WORLDVIEW_CONSTRAINTS['tone']}
   - 主题: {WORLDVIEW_CONSTRAINTS['theme']}
4. 禁止包含: {', '.join(WORLDVIEW_CONSTRAINTS['forbidden_elements'])}
5. 数值约束:
   - security_level: {CITY_RULES['constraints']['security_range']}
   - population: {CITY_RULES['constraints']['population_range']}
   - prosperity: {CITY_RULES['constraints']['prosperity_range']}

【输出格式】
必须返回严格 JSON:
{{
    "location_id": "{city_id}",
    "location_type": "city",
    "name": "城市名称",
    "description": "背景描述，体现灾后重建与希望",
    "cultural_tags": ["文化标签1", "文化标签2"],
    "landscape_features": ["地貌特征1", "地貌特征2"],
    "architectural_style": "建筑风格描述",
    "local_specialties": ["特产1", "特产2"],
    "security_level": 3.5,
    "population": 10000,
    "prosperity": 50,
    "status": "rebuilding",
    "districts": ["城区1", "城区2"],
    "event_pool": ["事件标签1", "事件标签2"],
    "disaster_impact": "大灾变影响描述",
    "available_buildings": ["tavern", "blacksmith", "market"]
}}
"""
    
    def _build_town_prompt(self, source_towns: List[Dict], town_id: str) -> str:
        """构建城镇生成 Prompt"""
        sources_desc = "\n".join([
            f"- {t['name']}: {t['description']} | 特色: {', '.join(t.get('features', []))}"
            for t in source_towns
        ])
        
        return f"""
你是一个游戏世界构建专家。请融合以下 {len(source_towns)} 个现实城镇/乡村的特色，生成一个游戏城镇配置。

【源城镇信息】
{sources_desc}

【生成要求】
1. 城镇ID: {town_id}
2. 城镇受灾更严重，治安更混乱，资源更匮乏
3. 严格符合世界观约束（同上）
4. 数值约束:
   - security_level: {TOWN_RULES['constraints']['security_range']}
   - disaster_severity: {TOWN_RULES['constraints']['disaster_severity_range']}
   - prosperity: {TOWN_RULES['constraints']['prosperity_range']}

【输出格式】
必须返回严格 JSON:
{{
    "location_id": "{town_id}",
    "location_type": "town",
    "name": "城镇名称",
    "description": "背景描述，体现困境与希望",
    "cultural_tags": [],
    "landscape_features": [],
    "architectural_style": "",
    "local_specialties": [],
    "security_level": 2.0,
    "population": 2000,
    "prosperity": 25,
    "status": "ruined",
    "disaster_severity": 4,
    "awakened_children": 1,
    "event_pool": [],
    "disaster_impact": "",
    "available_buildings": []
}}
"""
    
    def _validate_and_complete(self, result: Dict, loc_id: str, loc_type: str) -> Dict:
        """验证并补全生成结果"""
        # 确保必需字段
        result['location_id'] = loc_id
        result['location_type'] = loc_type
        
        # 补全默认值
        result.setdefault('status', 'rebuilding' if loc_type == 'city' else 'ruined')
        result.setdefault('constructed_buildings', {})
        result.setdefault('resource_production', {})
        result.setdefault('trade_routes', [])
        result.setdefault('connected_roads', [])
        result.setdefault('coordinates', None)
        
        # 数值边界检查
        rules = CITY_RULES if loc_type == 'city' else TOWN_RULES
        if 'security_level' in result:
            min_s, max_s = rules['constraints']['security_range']
            result['security_level'] = max(min_s, min(max_s, result['security_level']))
        
        return result
    
    def generate_all_cities(self) -> List[Dict]:
        """生成所有城市"""
        cities = []
        for i in range(CITY_RULES['count']):
            result = self.generate_city(i)
            if result:
                cities.append(result)
        return cities
    
    def generate_all_towns(self) -> List[Dict]:
        """生成所有城镇"""
        towns = []
        for i in range(TOWN_RULES['count']):
            result = self.generate_town(i)
            if result:
                towns.append(result)
        return towns
    
    def save_results(self, cities: List[Dict], towns: List[Dict]):
        """保存生成结果"""
        if cities:
            with open(os.path.join(self.output_dir, "cities.json"), 'w', encoding='utf-8') as f:
                json.dump(cities, f, ensure_ascii=False, indent=2)
            print(f"✅ 保存 {len(cities)} 个城市到 cities.json")
        
        if towns:
            with open(os.path.join(self.output_dir, "towns.json"), 'w', encoding='utf-8') as f:
                json.dump(towns, f, ensure_ascii=False, indent=2)
            print(f"✅ 保存 {len(towns)} 个城镇到 towns.json")
        
        self.pool.save()
        print(f"✅ 资源池状态已保存")


def main():
    """主入口"""
    generator = CityTownGenerator()
    
    print("=" * 60)
    print("🏙️ 开始生成城市和城镇")
    print("=" * 60)
    
    cities = generator.generate_all_cities()
    towns = generator.generate_all_towns()
    
    generator.save_results(cities, towns)
    
    # 输出多样性报告
    report = generator.pool.get_tag_diversity_report()
    print("\n📊 多样性报告:")
    print(f"   总生成数: {report['total_generations']}")
    print(f"   唯一标签数: {report['unique_tags']}")
    print(f"   未使用源: {report['reuse_stats']['sources_never_used']}")
    print(f"   重复使用源: {report['reuse_stats']['sources_reused']}")


if __name__ == "__main__":
    main()