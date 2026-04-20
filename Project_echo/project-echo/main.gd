extends Node2D

@onready var api = $AIApi
@onready var btn = $TestBattleBtn
@onready var console = $OutputConsole

# Python FastAPI 的本地调试地址
const BACKEND_URL = "http://127.0.0.1:8000/api/v1/combat/tactic"

func _ready():
	# 连接按钮点击信号和 HTTP 请求完成信号 (Godot 4.x 语法)
	btn.pressed.connect(_on_test_battle_btn_pressed)
	api.request_completed.connect(_on_api_request_completed)
	
	console.text = "前端系统初始化完毕。等待发送给左脑...\n"

func _on_test_battle_btn_pressed():
	btn.disabled = true
	console.text += "\n[前端] 思考中... 发送战场状态到 Python 后端...\n"
	
	# 构建严格符合我们在 schema.py 里要求的数据字典
	# 在你的 _on_test_battle_btn_pressed 函数里：
	var request_data = {
		"pet_state": {
			"pet_id":"uuid_00001",
			"pet_name": "雷光犬",
			"species": "犬怪",
			"element": "电",
			"hp": 80,                 # 匹配你新加的 hp
			#"level": 60,
			"persona": "狂躁、好战但很聪明",
			"trust_level": 80,        # 匹配必填
			"mood": 65                # 匹配必填
		},
		"enemy_desc": "一只浑身散发着毒气的巨大沼泽史莱姆，移动缓慢但物理防御极高。",
		"env_tags": ["雨天", "泥泞", "导电环境"],
		"player_input": "用尽全力攻击！", # 匹配你的玩家指令
		"allowed_skills": [
			{"skill_id": "s1", "name": "雷咬", "description": "近战物理伤害，附带电属性", "cost": 15},
			{"skill_id": "s2", "name": "高压电网", "description": "AOE范围法术伤害，在雨天威力翻倍", "cost": 30},
			{"skill_id": "s3", "name": "防卫姿态", "description": "恢复精力，减免下次受到的伤害", "cost": 0}
		]
	}
	
	# 转换为 JSON 文本
	var json_str = JSON.stringify(request_data)
	var headers = ["Content-Type: application/json"]
	
	# 发起 POST 请求
	var error = api.request(BACKEND_URL, headers, HTTPClient.METHOD_POST, json_str)
	if error != OK:
		console.text += "[错误] 无法连接到服务器。请检查 Python 后端是否启动。\n"
		btn.disabled = false

func _on_api_request_completed(result, response_code, headers, body):
	btn.disabled = false
	
	if response_code == 200:
		var response_str = body.get_string_from_utf8()
		console.text += "\n[调试原始数据]" + response_str + "\n"
		var data = JSON.parse_string(response_str)
		
		if typeof(data) == TYPE_DICTIONARY:
			console.text += "\n[⚡ 大脑指令解析成功 ⚡]\n"
			console.text += "【动作执行】 技能ID: " + str(data.get("skill_id", "未知")) + "  | 目标: " + str(data.get("target", "无")) + "\n"
			console.text += "【抗命判定】 听话?: " + str(data.get("is_obedient", true)) + " | 心情变化: " + str(data.get("mood_delta", 0)) + "\n"
			console.text += "【角色台词】 「" + str(data.get("dialogue", "无")) + "」\n"
			console.text += "【战术日志】 " + str(data.get("thought_process", "无")) + "\n\n"
			
			# 💡 未来游戏引擎里的真实逻辑接入点：
			# if not data_dict.get("is_obedient", true):
			#     play_animation("head_shake_refuse")
			# else:
			#     cast_skill(data_dict["skill_id"], data_dict["target"])
			# update_mood(data_dict.get("mood_delta", 0))
				
		else:
			console.text += "[错误] JSON 解析格式不符合预期\n"
	else:
		console.text += "[错误] 后端返回错误码: " + str(response_code) + "\n"
		console.text += body.get_string_from_utf8() + "\n"
