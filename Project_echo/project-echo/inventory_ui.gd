extends Control

@onready var grid = $Panel/ScrollContainer/GridContainer
@onready var api = $InteractApi

const BASE_URL = "http://127.0.0.1:8000/api/v1/raising"

func _ready():
	api.request_completed.connect(_on_item_used_response)
	_refresh_inventory()

func _refresh_inventory():
	# 清空旧视图
	for child in grid.get_children():
		child.queue_free()
		
	var has_items = false
	# 彻底数据驱动：遍历 GameManager 中的本地背包
	for item_name in GameManager.inventory.keys():
		var amount = GameManager.inventory[item_name]
		if amount > 0:
			has_items = true
			var btn = Button.new()
			btn.text = "%s (x%d)" % [item_name, amount]
			btn.custom_minimum_size = Vector2(160, 60)
			
			# 点击后触发泛化使用接口
			btn.pressed.connect(_try_use_item.bind(item_name))
			grid.add_child(btn)
			
	if not has_items:
		var empty_label = Label.new()
		empty_label.text = "背包空空如也，快去打工吧！"
		grid.add_child(empty_label)

func _try_use_item(item_name: String):
	# 【未来迁移点】目前是本地直接扣除；未来这里只需改成向后端发 /consume 验证请求
	if GameManager.inventory.get(item_name, 0) <= 0: return
	GameManager.inventory[item_name] -= 1
	GameManager.save_game()
	
	_refresh_inventory()
	_set_buttons_disabled(true)
	print("🎒 [背包] 玩家对宠物使用了物品: ", item_name)
	
	# 复用之前写好的 interact 接口！
	var payload = {
		"pet_state": GameManager.pet_state,
		"action_type": "use_item", # 泛化动作词
		"user_input": "对你使用了物品：[" + item_name + "]"
	}
	var headers = ["Content-Type: application/json"]
	api.request(BASE_URL + "/interact", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func _on_item_used_response(result, response_code, headers, body):
	_set_buttons_disabled(false)
	
	if response_code == 200:
		var res = JSON.parse_string(body.get_string_from_utf8())
		
		# 结算情绪与好感度，更新本地状态
		GameManager.pet_state["mood"] += res.get("mood_change", 0)
		GameManager.pet_state["trust_level"] += res.get("trust_change", 0)
		GameManager.save_game()
		
		print("====== 物品互动反馈 ======")
		print("🐶 宠物说: ", res["dialogue"])
		if res["is_refused"]:
			print("⚠️ [系统] 宠物嫌弃并拒绝了这个物品！")
			# TODO: 未来可在此处播放屏幕震动或闪红光特效
	else:
		print("❌ 请求失败，状态码: ", response_code)

func _set_buttons_disabled(is_disabled: bool):
	for child in grid.get_children():
		if child is Button:
			child.disabled = is_disabled
