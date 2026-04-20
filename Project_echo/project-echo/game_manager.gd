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

# =========== 2. 生命周期 ===========
func _ready():
	# 游戏启动时，第一件事就是尝试加载本地存档
	load_game()

# =========== 3. 存档与读档系统 ===========
func save_game():
	var save_data = {
		"pet_state": pet_state,
		"inventory": inventory,
		"last_save_time": Time.get_unix_time_from_system() # 记录下线时间，用于未来算离线挂机收益
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
