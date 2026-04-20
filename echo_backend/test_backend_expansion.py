import requests
import json

base_url = "http://127.0.0.1:8000/api/v1/raising"

base_state = {
    "pet_id": "pet_test_001",
    "pet_name": "雷光犬",
    "species": "犬怪",
    "element": "电",
    "hp": 100,
    "persona": "极度傲娇，口嫌体正直，自尊心强",
    "trust_level": 50,
    "mood": 50
}

print("========================================")
print("🚀 [测试1] 城镇场景交互：去酒馆打工")
location_payload = {
    "pet_state": base_state,
    "location_category": "town",
    "specific_node": "风车酒馆",
    "action_type": "驻唱打工",
    "duration_hours": 4.0
}
res_loc = requests.post(f"{base_url}/location_task", json=location_payload)
print(json.dumps(res_loc.json(), ensure_ascii=False, indent=2))

print("\n========================================")
print("🚀 [测试2] 社交与邮箱系统：检查奇遇信件")
mail_payload = {
    "pet_state": base_state
}
res_mail = requests.post(f"{base_url}/mail/check", json=mail_payload)
print(json.dumps(res_mail.json(), ensure_ascii=False, indent=2))