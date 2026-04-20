import requests
import json
import time

base_url = "http://127.0.0.1:8000/api/v1/raising"
pet_id = "pet_test_memory_001"

base_state = {
    "pet_id": pet_id,
    "pet_name": "雷光犬",
    "species": "犬怪",
    "element": "电",
    "hp": 100,
    "persona": "极度傲娇，口嫌体正直，自尊心强",
    "trust_level": 50,
    "mood": 50
}

def send_interact(action, text):
    payload = {
        "pet_state": base_state,
        "action_type": action,
        "user_input": text
    }
    res = requests.post(f"{base_url}/interact", json=payload)
    print(f"\n玩家动作: [{action}] {text}")
    print("宠物反馈:\n", json.dumps(res.json(), ensure_ascii=False, indent=2))

print("========================================")
print("🚀 [阶段1] 初次建立负面记忆...")
send_interact("hit", "用树枝狠狠抽打它，大骂它是笨狗！")

print("\n等待记忆入库...")
time.sleep(2) # 稍微等待向量库计算并落盘

print("========================================")
print("🚀 [阶段2] 假装讨好，触发 RAG 记忆联想...")
send_interact("feed", "乖狗狗，给你吃最大最香的电烤大肉排！")

print("========================================")
print("🚀 [阶段3] 检查生成的纯文本历史记录 (History API)...")
res_history = requests.get(f"{base_url}/history/{pet_id}")
print("历史聊天面板数据:\n", json.dumps(res_history.json(), ensure_ascii=False, indent=2))