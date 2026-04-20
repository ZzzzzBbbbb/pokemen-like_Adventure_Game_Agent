extends Control

# --- 节点获取 ---
@onready var api = $ActionApi
@onready var history_api = $HistoryApi

@onready var pet_name_label = $VBoxContainer/TopBar/PetName
@onready var change_btn = $VBoxContainer/TopBar/Change
@onready var return_btn = $VBoxContainer/TopBar/Return
@onready var chat_bubble = $VBoxContainer/CenterStage/ChatBubble
@onready var bubble_text = $VBoxContainer/CenterStage/ChatBubble/BubbleText
@onready var chat_history_btn = $VBoxContainer/CenterStage/ChatHistory
@onready var mood_label = $VBoxContainer/CenterStage/StatsBox/MoodLabel
@onready var trust_label = $VBoxContainer/CenterStage/StatsBox/TrustLabel
@onready var player_input = $VBoxContainer/BottomPanel/InputArea/PlayerInput
@onready var confirm_btn = $VBoxContainer/BottomPanel/InputArea/ConfirmBtn

@onready var drawer_layer = $DrawerLayer
@onready var dark_mask = $DrawerLayer/DarkMask
@onready var side_panel = $DrawerLayer/SidePanel
@onready var history_list = $DrawerLayer/SidePanel/ScrollContainer/HistoryList


@onready var item_list = $VBoxContainer/BottomPanel/ScrollContainer/ItemList

const BACKEND_URL = "http://127.0.0.1:8000/api/v1/raising/interact"
const PANEL_WIDTH = 800

var pet_state = {
	"pet_id": "pet_alpha_001",
	"pet_name": "雷光犬",
	"species": "犬怪",
	"element": "电",
	"hp": 100,
	"persona": "极度傲娇，口嫌体正直，自尊心强",
	"trust_level": 40,
	"mood": 50
}

func _ready():
	# 隐藏气泡，等有话说了再显示
	chat_bubble.visible = false 
	_update_ui_stats()
	
	# 连接网络回调
	api.request_completed.connect(_on_api_response)
	
	# 连接底部输入框聊天按钮
	confirm_btn.pressed.connect(_on_send_chat)
	
	# 动态连接滑动栏里的所有物品按钮
	for btn in item_list.get_children():
		if btn is Button:
			# 当点击物品时，发送 "feed" / "reward" 等动作，内容带上按钮的文字（比如"苹果"）
			btn.pressed.connect(_on_item_used.bind(btn.text))

	drawer_layer.visible = false
	side_panel.position.x = -PANEL_WIDTH
	
	# 2. 绑定抽屉按钮和遮罩点击
	chat_history_btn.pressed.connect(_on_open_history)
	dark_mask.gui_input.connect(_on_mask_clicked)
	history_api.request_completed.connect(_on_history_received)
	
	
	_setup_offline_overlay()
	GameManager.offline_report_ready.connect(_show_offline_report)
	if GameManager.pending_offline_report != "":
		_show_offline_report(GameManager.pending_offline_report)
		GameManager.pending_offline_report = "" # 播完就清空
	
func _update_ui_stats():
	pet_name_label.text = GameManager.pet_state["pet_name"]
	mood_label.text = "心情: " + str(GameManager.pet_state["mood"])
	trust_label.text = "信任度: " + str(GameManager.pet_state["trust_level"])

# --- 发起操作 ---
func _on_send_chat():
	var text = player_input.text.strip_edges()
	if text == "": return
	
	player_input.text = ""
	_send_action_to_brain("chat", text)

func _on_item_used(item_name: String):
	# 你可以根据设计，给不同物品分配 action_type，这里统称为 interact
	_send_action_to_brain("interact", "给宠物使用了: " + item_name)

func _send_action_to_brain(action_type: String, user_input: String):
	# 模拟 UI 禁用和加载状态
	confirm_btn.disabled = true
	chat_bubble.visible = true
	bubble_text.text = "..." # 显示加载动画或省略号
	
	var request_data = {
		"pet_state": GameManager.pet_state,
		"action_type": action_type,
		"user_input": user_input
	}
	
	var headers = ["Content-Type: application/json"]
	api.request(BACKEND_URL, headers, HTTPClient.METHOD_POST, JSON.stringify(request_data))

# --- 处理大脑回传 ---
func _on_api_response(result, response_code, headers, body):
	confirm_btn.disabled = false
	
	if response_code == 200:
		var res = JSON.parse_string(body.get_string_from_utf8())
		var data = res.get("data", res) 
		
		# 1. 更新文字并打字机效果显示气泡
		bubble_text.text = data.get("dialogue", "嗯？")
		
		# 2. 结算数值
		GameManager.pet_state["mood"] = clamp(GameManager.pet_state["mood"] + data.get("mood_change", 0), 0, 100)
		GameManager.pet_state["trust_level"] = clamp(GameManager.pet_state["trust_level"] + data.get("trust_change", 0), 0, 100)
		GameManager.save_game()
		_update_ui_stats()
		
		# 3. 如果拒绝了，可以触发屏幕碎裂/红光等特效
		if data.get("is_refused", false):
			print("【被宠物嫌弃了！】播放拒绝动画")
			_play_screen_shake()
	else:
		bubble_text.text = "[网络断开] ......"

func _on_open_history():
	# 1. 显示层
	drawer_layer.visible = true
	
	# 2. 清空旧列表，请求新数据
	for child in history_list.get_children():
		child.queue_free()
	
	var url = "http://127.0.0.1:8000/api/v1/raising/history/" + pet_state["pet_id"]
	history_api.request(url)
	
	# 3. 丝滑滑入动画 (Tween)
	var tween = create_tween().set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	# 把侧边栏的X坐标从 -800 移动到 0，耗时 0.4 秒
	tween.tween_property(side_panel, "position:x", 0.0, 0.4)

func _close_history():
	# 丝滑滑出动画
	var tween = create_tween().set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	# 把侧边栏移回 -800
	tween.tween_property(side_panel, "position:x", -float(PANEL_WIDTH), 0.3)
	
	# 动画播完后隐藏整个层（防止遮罩挡住点击）
	tween.finished.connect(func(): drawer_layer.visible = false)

func _on_mask_clicked(event: InputEvent):
	# 当玩家点击右侧半透明的暗层时，触发的检测
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_close_history()

# ========== 接收聊天记录并生成气泡 ==========

func _on_history_received(result, response_code, headers, body):
	if response_code == 200:
		var data = JSON.parse_string(body.get_string_from_utf8())
		if data and data.has("messages"):
			# 遍历 Python 传过来的历史记录列表
			for msg in data["messages"]:
				_create_chat_item(msg["sender"], msg["name"], msg["text"], msg["time"])

func _create_chat_item(sender: String, role_name: String, text: String, time: String):
	# 用代码动态生成类似于 QQ 的气泡结构 (头像 + 名字 + 内容)
	var margin_container = MarginContainer.new()
	margin_container.add_theme_constant_override("margin_bottom", 15)
	margin_container.add_theme_constant_override("margin_left", 20 if sender == "pet" else 100)
	margin_container.add_theme_constant_override("margin_right", 100 if sender == "pet" else 20)
	
	var panel = PanelContainer.new()
	margin_container.add_child(panel)
	
	var vbox = VBoxContainer.new()
	panel.add_child(vbox)
	
	# 名字与时间
	var name_label = Label.new()
	name_label.text = role_name + "  " + time
	name_label.add_theme_color_override("font_color", Color.GRAY)
	vbox.add_child(name_label)
	
	# 内容
	var text_label = RichTextLabel.new()
	text_label.text = text
	text_label.fit_content = true # 自动根据字数撑开高度
	text_label.custom_minimum_size.x = 400 # 限制一下气泡最大宽度
	vbox.add_child(text_label)
	
	# 添加到左侧面板的列表里
	history_list.add_child(margin_container)

# ========== 离线结算全屏纯文字弹窗 (支持双击关闭) ==========
var offline_overlay: ColorRect
var report_label: Label

func _setup_offline_overlay():
	offline_overlay = ColorRect.new()
	offline_overlay.color = Color(0, 0, 0, 0.9) # 极深的黑色半透明遮罩
	offline_overlay.set_anchors_preset(PRESET_FULL_RECT)
	offline_overlay.visible = false
	add_child(offline_overlay) # 加到最顶层
	
	var center = CenterContainer.new()
	center.set_anchors_preset(PRESET_FULL_RECT)
	offline_overlay.add_child(center)
	
	report_label = Label.new()
	report_label.add_theme_font_size_override("font_size", 36)
	report_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	report_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	report_label.custom_minimum_size = Vector2(700, 0)
	center.add_child(report_label)
	
	# 监听全屏底板的输入事件
	offline_overlay.gui_input.connect(_on_offline_overlay_input)

func _show_offline_report(text: String):
	report_label.text = text + "\n\n\n( 快速双击屏幕关闭 )"
	offline_overlay.visible = true

func _on_offline_overlay_input(event: InputEvent):
	var is_double_tapped = false
	if event is InputEventScreenTouch and event.pressed and event.double_tap:
		is_double_tapped = true
	elif event is InputEventMouseButton and event.pressed and event.double_click:
		is_double_tapped = true
		
	if is_double_tapped:
		var tween = create_tween()
		tween.tween_property(offline_overlay, "modulate:a", 0.0, 0.3) # 淡出效果
		tween.finished.connect(func(): offline_overlay.visible = false; offline_overlay.modulate.a = 1.0)

func _play_screen_shake():
	var tween = create_tween()
	var original_pos = position

	for i in range(5):
		var random_offset = Vector2(randf_range(-15, 15), randf_range(-15, 15))
		tween.tween_property(self, "position", original_pos + random_offset, 0.05)
	
	tween.tween_property(self, "position", original_pos, 0.05)
