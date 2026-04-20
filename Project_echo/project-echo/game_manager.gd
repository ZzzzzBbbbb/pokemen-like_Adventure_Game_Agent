extends Node

const SAVE_PATH = "user://savegame.json"

# 👇 新增：定义一个离线结算完毕的全局信号
signal offline_report_ready(report_text: String)
var pending_offline_report: String = "" # 新增：用于暂存报告，防止页面还没切换时信号漏掉

# =========== 1. 核心游戏数据 ===========
var pet_state = {
	"pet_id": "pet_alpha_001",
	"pet_name": "雷光犬",
	"species": "犬怪",
	"element": "电",
	"hp": 100,
	"persona": "极度傲娇，口嫌体正直，自尊心强",
	"trust_level": 50,
	"mood": 50
}

# 玩家的资源背包
var inventory = {
	"旧金币": 0,
	"野果": 0,
	"以太颗粒": 0
}

# 游戏环境上下文（用于大模型感知）
var current_location_name: String = "阳光森林"
var current_env_tags: Array = ["微风", "草地", "阳光"]

# =========== 🆕 2. 根据地系统数据 ===========
var settlement_state = {
	"settlement_id": "",
	"name": "无名营地",
	"level": 1,
	"prosperity": 0,
	"buildings": {},
	"resource_nodes": {},
	"storage": {},
	"is_established": false,
	"last_tick_time": ""
}

# =========== 2. 生命周期 ===========
func _ready():
	# 游戏启动时，第一件事就是尝试加载本地存档
	load_game()

# =========== 3. 存档与读档系统 ===========
func save_game():
	var save_data = {
		"pet_state": pet_state,
		"inventory": inventory,
		"settlement_state": settlement_state,
		"last_save_time": Time.get_unix_time_from_system()
	}
	
	var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(save_data, "\t"))
		file.close()
		print("💾 [系统] 游戏进度已保存！")
	else:
		print("❌ [系统] 保存失败：", FileAccess.get_open_error())

func load_game():
	if not FileAccess.file_exists(SAVE_PATH):
		print("🌱 [系统] 未找到存档，将使用初始默认数据创建新游戏。")
		return
		
	var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file:
		var json_str = file.get_as_text()
		var json = JSON.new()
		var error = json.parse(json_str)
		if error == OK:
			var data = json.data
			pet_state = data.get("pet_state", pet_state)
			inventory = data.get("inventory", inventory)
			settlement_state = data.get("settlement_state", settlement_state)
			
			var last_time = data.get("last_save_time", Time.get_unix_time_from_system())
			var offline_seconds = Time.get_unix_time_from_system() - last_time
			var offline_hours = offline_seconds / 3600.0
			print("💾 [系统] 读档成功！距离上次下线过了 %.2f 小时。" % offline_hours)
			

			if offline_hours >= 2.0:
				_request_offline_settlement(offline_hours)
		else:
			print("❌ [系统] 存档已损坏。")
		file.close()

# =========== 5. 离线结算专属逻辑 ===========
func _request_offline_settlement(hours: float):
	print("⏳ [离线系统] 开始向大模型云端请求挂机演算...")
	
	# 动态创建一个网络请求节点
	var http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(self._on_offline_settlement_completed.bind(http_request))
	
	var payload = {
		"pet_state": pet_state,
		"duration_hours": min(hours, 24.0), # 限制最多算24小时，防止数值爆炸
		"environment_desc": current_location_name,
		"player_message": "" # 预留字段，未来可以在退出游戏时做个弹窗让玩家留字条
	}
	var headers = ["Content-Type: application/json"]
	http_request.request("http://127.0.0.1:8000/api/v1/raising/offline_task", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func _on_offline_settlement_completed(result, response_code, headers, body, http_node):
	http_node.queue_free()
	
	if response_code == 200:
		var res = JSON.parse_string(body.get_string_from_utf8())
		print("\n====== 🌟 离线挂机大结算 ======")
		
		# 👇 新增：拼接将在前端展示的弹窗报告文字
		var report_text = "【挂机归来】\n\n" + res.get("summary_journal", "") + "\n\n[战利品]:\n"
		
		for task in res.get("completed_tasks", []):
			var rewards = task.get("reward_items", {})
			for item_name in rewards.keys():
				add_item(item_name, rewards[item_name])
				report_text += "📦 %s x%d   " % [item_name, rewards[item_name]]
				
		save_game()
		
		# 👇 暂存并触发信号
		pending_offline_report = report_text
		emit_signal("offline_report_ready", report_text)
	else:
		print("❌ 离线结算网络请求失败。")

# =========== 4. 辅助工具函数 ===========
func add_item(item_name: String, amount: int = 1):
	if inventory.has(item_name):
		inventory[item_name] += amount
	else:
		inventory[item_name] = amount
	print("🎒 [背包] 获得物品: %s x%d" % [item_name, amount])
	save_game() # 获得重要物品后自动保存

# =========== 🆕 5. 根据地系统 API 封装 ===========
const SETTLEMENT_BASE_URL = "http://127.0.0.1:8000/api/v1/settlement"

func settlement_found(location_info: Dictionary) -> void:
"""
🏗️ 开辟根据地
调用时机：玩家到达可开荒节点，满足条件后触发
"""
print("🏗️ [根据地] 准备开辟新根据地于：", location_info.get("name"))

var http_request = HTTPRequest.new()
add_child(http_request)
http_request.request_completed.connect(_on_settlement_action_completed.bind(http_request, "found"))

var payload = {
"pet_state": pet_state,
"settlement_state": settlement_state,
"action_type": "found",
"target_id": null,
"parameters": location_info
}
var headers = ["Content-Type: application/json"]
http_request.request(SETTLEMENT_BASE_URL + "/found", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func settlement_build(building_type: String, location_id: String) -> void:
"""
🏗️ 建造建筑
调用时机：玩家在建设界面点击建造按钮
"""
print("🏗️ [根据地] 请求建造：", building_type)

var http_request = HTTPRequest.new()
add_child(http_request)
http_request.request_completed.connect(_on_settlement_action_completed.bind(http_request, "build"))

var payload = {
"pet_state": pet_state,
"settlement_state": settlement_state,
"building_type": building_type,
"location_id": location_id,
"is_upgrade": false,
"target_building_id": null
}
var headers = ["Content-Type: application/json"]
http_request.request(SETTLEMENT_BASE_URL + "/build", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func settlement_repair(building_id: String) -> void:
"""
🔧 修复建筑
调用时机：建筑耐久度不足时
"""
print("🔧 [根据地] 请求修复建筑：", building_id)

var http_request = HTTPRequest.new()
add_child(http_request)
http_request.request_completed.connect(_on_settlement_action_completed.bind(http_request, "repair"))

var payload = {
"pet_state": pet_state,
"settlement_state": settlement_state,
"action_type": "repair",
"target_id": building_id,
"parameters": {}
}
var headers = ["Content-Type: application/json"]
http_request.request(SETTLEMENT_BASE_URL + "/repair", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func settlement_assign_pet(pet_id: String, building_id: String) -> void:
"""
🐾 分配幻灵到建筑
调用时机：玩家在建筑详情界面分配幻灵
"""
print("🐾 [根据地] 分配幻灵到建筑：", building_id)

var http_request = HTTPRequest.new()
add_child(http_request)
http_request.request_completed.connect(_on_settlement_action_completed.bind(http_request, "assign"))

var payload = {
"pet_state": pet_state,
"settlement_state": settlement_state,
"action_type": "assign",
"target_id": building_id,
"parameters": {"pet_id": pet_id}
}
var headers = ["Content-Type: application/json"]
http_request.request(SETTLEMENT_BASE_URL + "/assign", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func settlement_collect(target_id: String) -> void:
"""
📦 收集资源/产出
调用时机：玩家点击收集按钮
"""
print("📦 [根据地] 收集资源：", target_id)

var http_request = HTTPRequest.new()
add_child(http_request)
http_request.request_completed.connect(_on_settlement_action_completed.bind(http_request, "collect"))

var payload = {
"pet_state": pet_state,
"settlement_state": settlement_state,
"action_type": "collect",
"target_id": target_id,
"parameters": {}
}
var headers = ["Content-Type: application/json"]
http_request.request(SETTLEMENT_BASE_URL + "/collect", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func sync_settlement_state() -> void:
"""
📊 同步根据地状态
调用时机：进入游戏、切换场景、定期同步
"""
print("📊 [根据地] 同步根据地状态")

var http_request = HTTPRequest.new()
add_child(http_request)
http_request.request_completed.connect(_on_sync_settlement_state_completed.bind(http_request))

var headers = ["Content-Type: application/json"]
http_request.request(SETTLEMENT_BASE_URL + "/state/" + pet_state["pet_id"], headers, HTTPClient.METHOD_GET)

func _on_settlement_action_completed(result, response_code, headers, body, http_node, action_type: String):
http_node.queue_free()

if response_code == 200:
var res = JSON.parse_string(body.get_string_from_utf8())
print("====== 根据地行动完成：", action_type, " ======")
print("📜 叙事反馈：", res.get("narrative", ""))

# 更新根据地状态
var changes = res.get("settlement_changes", {})
if changes.size() > 0:
_merge_settlement_changes(changes)

# 处理资源消耗
var cost = res.get("resource_cost", {})
for item in cost.keys():
if inventory.has(item):
inventory[item] -= cost[item]
print("💸 消耗：", item, " x", cost[item])

# 处理资源获得
var gain = res.get("resource_gain", {})
for item in gain.keys():
add_item(item, gain[item])

# 更新幻灵状态
var mood_change = res.get("mood_change", 0)
var trust_change = res.get("trust_change", 0)
if mood_change != 0:
pet_state["mood"] += mood_change
if trust_change != 0:
pet_state["trust_level"] += trust_change

# 处理解锁标记
var unlock_flags = res.get("unlock_flags", [])
for flag in unlock_flags:
print("🔓 解锁新功能：", flag)

save_game()
else:
print("❌ 根据地行动失败，状态码：", response_code)

func _on_sync_settlement_state_completed(result, response_code, headers, body, http_node):
http_node.queue_free()

if response_code == 200:
var res = JSON.parse_string(body.get_string_from_utf8())
settlement_state = res
print("📊 [根据地] 状态同步成功")
save_game()
else:
print("❌ 根据地状态同步失败，状态码：", response_code)

func _merge_settlement_changes(changes: Dictionary) -> void:
"""
合并根据地状态变化
"""
for key in changes.keys():
if key == "buildings":
for building_id in changes[key].keys():
settlement_state["buildings"][building_id] = changes[key][building_id]
elif key == "resource_nodes":
for node_id in changes[key].keys():
settlement_state["resource_nodes"][node_id] = changes[key][node_id]
elif key == "storage":
for item in changes[key].keys():
settlement_state["storage"][item] = changes[key][item]
else:
settlement_state[key] = changes[key]

print("🔄 [根据地] 状态已更新")
