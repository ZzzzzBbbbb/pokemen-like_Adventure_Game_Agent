import requests
import json

base_url = "http://127.0.0.1:8000/api/v1/raising"
pet_id = "pet_offline_test_001"

# ======== 基础宠物档案 ========
pet_state = {
    "pet_id": pet_id,
    "pet_name": "雷光犬",
    "species": "犬怪",
    "element": "电",
    "hp": 100,
    "persona": "极度傲娇，口嫌体正直，自尊心强，容易偷懒",
    "trust_level": 40,
    "mood": 50
}

print("========================================")
print("🚀 [测试1] 离线挂机：【被动摸鱼模式】(无留言，离线 3.5 小时)")
# 预期：由于不足 4 小时，只能完成一个 2 或 3 小时的任务，产出少
offline_payload_passive = {
    "pet_state": pet_state,
    "duration_hours": 3.5,
    "environment_desc": "阳光森林营地",
    "player_message": None
}
res_passive = requests.post(f"{base_url}/offline_task", json=offline_payload_passive)
print(json.dumps(res_passive.json(), ensure_ascii=False, indent=2))

print("\n========================================")
print("🚀 [测试2] 离线挂机：【主动规划模式】(有留言，离线 8 小时)")
# 预期：宠物会按照指令组合几个任务（比如采果子+站岗），把 8 小时排满，产出多
offline_payload_active = {
    "pet_state": pet_state,
    "duration_hours": 8.0,
    "environment_desc": "风车镇外围",
    "player_message": "我去上学了，你今天重点去周边采集物资，有多余的时间再去营地站岗，多弄点旧金币回来！"
}
res_active = requests.post(f"{base_url}/offline_task", json=offline_payload_active)
print(json.dumps(res_active.json(), ensure_ascii=False, indent=2))

print("\n========================================")
print("🚀 [测试3] 检查历史总线：验证挂机总结是否成功写入...")
# 修改这里：使用 base_url 来拼接正确的路径
res_history = requests.get(f"{base_url}/history/{pet_id}")
print(json.dumps(res_history.json(), ensure_ascii=False, indent=2))