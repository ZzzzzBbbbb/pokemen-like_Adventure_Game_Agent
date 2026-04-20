extends Control

# --- 节点获取 ---
@onready var mail_api = $MailApi # HTTPRequest 节点
@onready var refresh_btn = $TopPanel/RefreshBtn
@onready var mail_list_container = $ScrollContainer/VBoxContainer # 用于竖向排列邮件的容器

# 假定你做了一个单独的邮件条目预制件（包含标题Label、发件人Label等）
@export var mail_item_scene: PackedScene 

const BASE_URL = "http://127.0.0.1:8000/api/v1/raising"

func _ready():
	refresh_btn.pressed.connect(_fetch_mails)
	mail_api.request_completed.connect(_on_mail_received)
	
	# 打开界面时自动请求一次
	_fetch_mails()

func _fetch_mails():
	refresh_btn.disabled = true
	# 清空当前的旧邮件列表
	for child in mail_list_container.get_children():
		child.queue_free()
		
	print("📫 [收发室] 正在向云端拉取邮件...")
	
	# 严格对齐后端 schemas.MailCheckRequest 契约
	var payload = {
		"pet_state": GameManager.pet_state
	}
	var headers = ["Content-Type: application/json"]
	mail_api.request(BASE_URL + "/mail/check", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))

func _on_mail_received(result, response_code, headers, body):
	refresh_btn.disabled = false
	
	if response_code == 200:
		var res = JSON.parse_string(body.get_string_from_utf8())
		var mails: Array = res.get("mails", [])
		
		if mails.is_empty():
			print("📭 当前没有新邮件。")
			# TODO: 可以在界面上显示一个 "暂无邮件" 的占位图
			return
			
		print("📬 收到 %d 封信件！" % mails.size())
		
		# 遍历解析数组，动态生成 UI
		for mail in mails:
			_create_mail_ui_item(mail)
	else:
		print("❌ 邮件拉取失败，状态码: ", response_code)

func _create_mail_ui_item(mail_data: Dictionary):
	# 【扩展性设计】不直接在这里拼凑 Label，而是实例化预制件
	if not mail_item_scene:
		print("未分配 mail_item_scene 预制件！仅打印数据：", mail_data)
		return
		
	var item = mail_item_scene.instantiate()
	mail_list_container.add_child(item)
	
	# 假设你的 mail_item_scene 根节点有一个 setup 函数，接受字典参数
	if item.has_method("setup"):
		item.setup(mail_data["title"], mail_data["sender"], mail_data["content"], mail_data["attached_items"])
