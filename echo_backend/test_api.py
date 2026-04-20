# test_fastapi.py
import requests
import json

url = "http://127.0.0.1:8000/api/v1/combat/tactic"

# ======== 模拟案例 1：上帝视角传入一只怯懦的食草系 ========
payload_1_grass = {
    "pet_name": "胖胖草",
    "pet_element": "草系",
    "pet_persona": "极其胆小，是个爱哭鬼，遇到危险就想缩成一团。",
    "pet_hp_percent": 30,
    "pet_stress": 90, # 极度害怕
    "enemy_desc": "极其狂暴的喷火龙，属性火系，正在咆哮",
    "env_tags": ["干草垛", "岩石躲避物"],
    "player_input": "别怕！给我冲上去用飞叶快刀打它脸！",
    "allowed_skills": ["SKILL_LEAF_BLADE", "SKILL_HIDE_BEHIND_ROCK", "NONE"]
}

# ======== 模拟案例 2：上帝视角传入一只高贵的冰系女王 ========
payload_2_ice = {
    "pet_name": "冰绝女皇",
    "pet_element": "冰系",
    "pet_persona": "极其高冷毒舌，认为主人的智商不如狗，但关键时刻还是会出手",
    "pet_hp_percent": 100,
    "pet_stress": 10,
    "enemy_desc": "正在水坑里泡澡的弱小水跃鱼",
    "env_tags": ["水坑", "导电铁丝"],
    "player_input": "把它冻在水坑里！",
    "allowed_skills": ["SKILL_ICE_BEAM", "SKILL_WATER_FREEZE", "NONE"]
}

print("\n🚀 [游戏引擎] 开始发动：逼迫胆小的草系冲锋...")
res1 = requests.post(url, json=payload_1_grass)
print(json.dumps(res1.json(), ensure_ascii=False, indent=2))

print("-" * 50)

print("\n🚀 [游戏引擎] 开始发动：命令毒舌冰系冻结环境...")
res2 = requests.post(url, json=payload_2_ice)
print(json.dumps(res2.json(), ensure_ascii=False, indent=2))