# tools/ai4pet_wild.py
# =============================================================================
# 🐾 宠物/野兽 AI 生成器
# 基于生物分类生成灵宠配置
# =============================================================================

import json
import os
import sys
import random
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from resource_pool import get_resource_pool
from config.generation_rules import PET_RULES, WORLDVIEW_CONSTRAINTS
from your_llm_client import call_llm, extract_json

class PetGenerator:
    """宠物生成器"""
    
    def __init__(self):
        self.pool = get_resource_pool()
        self.output_dir = os.path.join(os.path.dirname(__file__), "output")
        self._load_species_data()
    
    def _load_species_data(self):
        """加载生物分类源数据"""
        species_file = os.path.join(os.path.dirname(__file__), "config", "species_bases.json")
        
        with open(species_file, 'r', encoding='utf-8') as f:
            self.species = json.load(f)
        
        for sp in self.species:
            self.pool.register_source(
                sp['id'], 'species',
                sp.get('tags', []) + [sp.get('category', '')]
            )
    
    def generate_pet(self, pet_index: int) -> Dict:
        """生成单个宠物"""
        pet_id = PET_RULES['id_format'].format(index=pet_index)
        
        if self.pool.is_generated(pet_id):
            print(f"⚠️ {pet_id} 已存在，跳过")
            return None
        
        # 获取可用物种
        source_ids = self.pool.get_available_sources('species', 1)
        if not source_ids:
            print("❌ 无可用物种源")
            return None
        
        species = next((s for s in self.species if s['id'] == source_ids[0]), None)
        if not species:
            return None
        
        prompt = self._build_pet_prompt(pet_id, species)
        
        print(f"🐾 生成 {pet_id}，基于: {species['name']}")
        response = call_llm(prompt)
        result = extract_json(response)
        
        result = self._validate_and_complete(result, pet_id, species)
        
        tags = result.get('tags', []) + [species['category']]
        self.pool.record_fusion(source_ids, pet_id, 'pet', tags)
        
        return result
    
    def _build_pet_prompt(self, pet_id: str, species: Dict) -> str:
        """构建宠物生成 Prompt"""
        return f"""
你是一个生物设计师。请基于以下现实生物，设计一个游戏中的灵宠。

【基础物种】
名称: {species['name']}
分类: {species['category']}
特征: {', '.join(species.get('features', []))}
习性: {species.get('habits', '')}
栖息地: {species.get('habitat', '')}

【生成要求】
1. 宠物ID: {pet_id}
2. 世界观: 大灾变后，动物吸收"灵气"开智进化，多数暴躁
3. 战斗: 纯物理伤害，近程/远程区分，无属性克制
4. 进化: 部位进化系统
   - 3个大部位（重要，大幅提升）
   - 5个小部位（次要，小幅提升）
   - 随机可重复，重复概率低
5. 性格影响任务擅长和战斗倾向
6. 技能组同时用于战斗和建设，共享熟练度
7. 禁止: 魔法、属性克制、高科技

【输出格式】
必须返回严格 JSON:
{{
    "pet_id": "{pet_id}",
    "pet_name": "灵宠名称",
    "species": "种族名称",
    "potential": 60,
    "persona": "性格描述",
    "description": "外观与背景描述",
    "tags": ["标签1", "标签2"],
    "attributes": {{
        "hp_base": 100,
        "attack_base": 20,
        "defense_base": 15,
        "speed_base": 12
    }},
    "combat_type": "melee",
    "skills": [
        {{
            "skill_id": "skill_001",
            "name": "技能名称",
            "description": "技能描述",
            "combat_effect": "战斗效果",
            "build_effect": "建设效果",
            "type": "active"
        }}
    ],
    "parts": {{
        "major": ["大部位1", "大部位2", "大部位3"],
        "minor": ["小部位1", "小部位2", "小部位3", "小部位4", "小部位5"]
    }},
    "ecology": {{
        "habitat": "栖息地",
        "diet": "食性",
        "behavior": "行为习性",
        "temperament": " temperament"
    }},
    "task_affinity": {{
        "preferred": ["擅长任务1", "擅长任务2"],
        "disliked": ["不擅长任务"]
    }}
}}
"""
    
    def _validate_and_complete(self, result: Dict, pet_id: str, species: Dict) -> Dict:
        """验证并补全宠物数据"""
        result['pet_id'] = pet_id
        
        # 边界检查
        if 'potential' in result:
            min_p, max_p = PET_RULES['constraints']['potential_range']
            result['potential'] = max(min_p, min(max_p, result['potential']))
        
        # 补全默认值
        result.setdefault('element', '')
        result.setdefault('status_effects', [])
        result.setdefault('trust_level', 50)
        result.setdefault('mood', 50)
        result.setdefault('hunger', 100)
        result.setdefault('thirst', 100)
        
        return result
    
    def generate_all_pets(self) -> List[Dict]:
        """生成所有宠物"""
        pets = []
        for i in range(PET_RULES['count']):
            result = self.generate_pet(i)
            if result:
                pets.append(result)
        return pets
    
    def save_results(self, pets: List[Dict]):
        """保存宠物结果"""
        with open(os.path.join(self.output_dir, "pets.json"), 'w', encoding='utf-8') as f:
            json.dump(pets, f, ensure_ascii=False, indent=2)
        print(f"✅ 保存 {len(pets)} 个宠物到 pets.json")
        self.pool.save()


def main():
    generator = PetGenerator()
    
    print("=" * 60)
    print("🐾 开始生成宠物")
    print("=" * 60)
    
    pets = generator.generate_all_pets()
    generator.save_results(pets)


if __name__ == "__main__":
    main()