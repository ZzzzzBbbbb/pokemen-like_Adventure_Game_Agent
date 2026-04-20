extends Control

@onready var bg_color = $Background
@onready var dynamic_slot = $DynamicLocationUI
@onready var interact_btn = $FixedUI/InteractBtn
@onready var inventory_btn = $FixedUI/InventoryBtn
@onready var inventory_ui = $Inventory_UI

func _ready():
	# 绑定固定功能：比如右下角的聊天大按钮
	interact_btn.pressed.connect(_on_interact_pressed)
	
	
	_change_location_to({
		"name": "风车小镇",
		"ui_scene_path": "res://town_ui.tscn", # 确保这里的路径和你实际存的名称一致
		"env_tags": ["城镇", "酒馆", "石板路", "集市"],
		"task_type": "在镇上打工"
	})

func _change_location_to(location_info: Dictionary):
	# 1. 保存当前去哪了，方便其他场景读取
	GameManager.current_location_name = location_info["name"]
	GameManager.current_env_tags = location_info["env_tags"]
	GameManager.offline_task_type = location_info["task_type"]
	
	# 先清空旧的环境专属界面的所有按钮或装饰
	for child in dynamic_slot.get_children():
		child.queue_free()
		
	# 如果这个地方有特别的 UI ，就动态插入
	if ResourceLoader.exists(location_info["ui_scene_path"]):
		var local_ui_scene = load(location_info["ui_scene_path"]).instantiate()
		dynamic_slot.add_child(local_ui_scene)

func _toggle_inventory():
	inventory_ui.visible = !inventory_ui.visible
	
	if inventory_ui.visible and inventory_ui.has_method("_refresh_inventory"):
		inventory_ui._refresh_inventory()
		print("🎒 [UI] 玩家打开了背包")


func _on_interact_pressed():
	# ==== 此处就是魔法纽带，进入陪伴场景！ ====
	print("准备进入陪伴车厢/营地特写模式，此时我在：", GameManager.current_env_tags)
	
	# Godot 的换场指令，直接跳到你做好的 chat_page.tscn
	# （请根据你昨天存放chat_page.tscn 的实际路径调整下方字符串）
	get_tree().change_scene_to_file("res://chat_page.tscn")
