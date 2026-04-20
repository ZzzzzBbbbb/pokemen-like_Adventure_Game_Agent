extends Control

# --- 节点获取 ---
@onready var task_api = $TaskApi 
@onready var vbox = $VBoxContainer # 我们只需要一个空的盒子容器

const BASE_URL = "http://127.0.0.1:8000/api/v1/raising"

# 🌟 【核心扩展点】环境衍生的任务配置表 (想加什么功能，直接在这里加一行)
var available_tasks = [
	{"node": "风车酒馆", "action": "驻唱打工", "duration": 4.0, "label": "🍻 去酒馆打工"},
	{"node": "铁匠铺", "action": "搬运矿石", "duration": 2.0, "label": "⚒️ 去铁匠铺干活"},
	{"node": "中心集市", "action": "摆摊打杂", "duration": 3.0, "label": "💰 去集市摆摊"} # 新增任务完全不需要改 Godot 界面！
]

var active_buttons = [] # 用来存储动态生成的按钮，方便后续统一禁用

func _ready():
	task_api.request_completed.connect(_on_task_response)
	_generate_buttons_dynamically()

func _generate_buttons_dynamically():
	# 1. 确保盒子是空的（如果你在编辑器里拖了占位按钮，这里先删掉）
	for child in vbox.get_children():
		child.queue_free()
	active_buttons.clear()
	
	# 2. 遍历配置表，动态创建按钮
	for task in available_tasks:
		var btn = Button.new()
		
		# ---- 顺便用代码解决按钮外观问题 ----
		btn.text = task["label"]
		btn.custom_minimum_size = Vector2(250, 80) # 强制按钮又宽又高
		btn.add_theme_font_size_override("font_size", 28) # 强制字体变成 28 号大字
		
		# 3. 魔术绑定：将这个任务的专属参数绑定到点击事件上
		btn.pressed.connect(_send_location_task.bind(task["node"], task["action"], task["duration"]))
		
		# 4. 加入场景树
		vbox.add_child(btn)
		active_buttons.append(btn)

func _send_location_task(specific_node: String, action_type: String, duration_hours: float):
	_set_buttons_disabled(true)
	print("🚀 [发起任务] 宠物前往: ", specific_node)
	
	var payload = {
		"pet_state": GameManager.pet_state, 
		"location_category": "town",        
		"specific_node": specific_node,
		"action_type": action_type,
		"duration_hours": duration_hours
	}
	
	var headers = ["Content-Type: application/json"]
	task_api.request(BASE_URL + "/location_task", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func _on_task_response(result, response_code, headers, body):
	_set_buttons_disabled(false) 
	
	if response_code == 200:
		var res = JSON.parse_string(body.get_string_from_utf8())
		
		GameManager.pet_state["mood"] += res["mood_change"]
		GameManager.pet_state["hp"] += res["hp_change"]
		GameManager.pet_state["trust_level"] += res["trust_change"]
		
		for item in res["reward_items"]:
			GameManager.add_item(item, 1)
		GameManager.save_game()	
		
		print("====== 城镇任务完成 ======")
		print("📜 剧情反馈: ", res["task_report"])
		print("🎁 获得道具: ", res["reward_items"])
	else:
		print("❌ 任务请求失败，状态码: ", response_code)

func _set_buttons_disabled(is_disabled: bool):
	# 遍历所有生成的按钮进行开关
	for btn in active_buttons:
		btn.disabled = is_disabled
