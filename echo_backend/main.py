# main.py
from fastapi import FastAPI, APIRouter
from schemas import BattleTacticRequest, RaisingInteractRequest, RaisingInteractResponse, OfflineTaskRequest, OfflineTaskResponse, SettlementActionRequest, SettlementActionResponse, BuildConstructRequest, SettlementEventRequest
from agents.battle_agent import generate_battle_action
from agents.rasing_agent import PetRaisingAgent
from routers import memory_api, history_api
import schemas
from routers.history_api import append_to_history
from datetime import datetime

app = FastAPI(title="Project Echo - Universal AI Gateway")

raising_router = APIRouter(prefix="/api/v1/raising", tags=["Pet Raising"])

@app.post("/api/v1/combat/tactic", summary="通用战斗战术分析网关")
async def combat_tactic_endpoint(payload: BattleTacticRequest):
    """
    游戏引擎只需要把战场参数包装好 POST 到这个接口。
    """
    print(f"🔌 [收到引擎请求] 幻灵: {payload.pet_state.pet_name} | 属性: {payload.pet_state.element}")
    
    # 丢进 Agent 进行脑力验算
    result_dict = generate_battle_action(payload)
    
    # 返回标准组装好的信封给游戏引擎
    return result_dict

@raising_router.post("/interact", summary="宠物互动接口", response_model=RaisingInteractResponse)
async def pet_interact_endpoint(request : RaisingInteractRequest):
    # 丢进 Agent 进行脑力验算
    result = await PetRaisingAgent.handle_interaction(request)
    
    # 自动将互动记录存入历史总线
    
    
    time_str = datetime.now().strftime("%H:%M")
    
    # 记录玩家行为 (如果有具体输入)
    if request.user_input:
        append_to_history(request.pet_state.pet_id, {
            "sender": "player",
            "name": "玩家",
            "text": f"[{request.action_type}] {request.user_input}",
            "time": time_str
        })
        
    # 记录宠物回复
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": result.dialogue,
        "time": time_str
    })
    
    return result

@raising_router.post("/offline_task", summary="离线挂机结算接口", response_model=OfflineTaskResponse)
async def pet_offline_task_endpoint(request : OfflineTaskRequest):
    result_dict = await PetRaisingAgent.resolve_offline_task(request)
    
    time_str = datetime.now().strftime("%H:%M")
    
    # 将多个任务拼成一段话存入历史总线
    task_details = "，".join([f"[{t.task_name}]({t.cost_hours}h)" for t in result_dict.completed_tasks])
    log_text = f"【离线汇总】{result_dict.summary_journal} (完成: {task_details or '无事发生'})"
    
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": log_text,
        "time": time_str
    })
    
    return result_dict

@raising_router.post("/location_task", summary="场景专属探索任务", tags=["地点交互"])
async def location_task_endpoint(request: schemas.LocationTaskRequest):
    """用于 Godot 切换场景后，点击 [去酒馆打工] 或 [去林地特训] 等差分化任务"""
    result = await PetRaisingAgent.resolve_location_task(request)
    
    # 可以在这里自动扣除/增加相应的宠物资源库
    from routers.history_api import append_to_history
    from datetime import datetime
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【任务汇报】{result.task_report}",
        "time": datetime.now().strftime("%H:%M")
    })
    return result

@raising_router.post("/mail/check", summary="收发室：检查好友邮件", tags=["社交与邮箱"])
async def mail_check_endpoint(request: schemas.MailCheckRequest):
    """好友互动系统，获取以邮件形式发送的留言和物品"""
    result = await PetRaisingAgent.check_mail_events(request)
    return result

# ===== 🆕 模拟经营/根据地路由组 =====
settlement_router = APIRouter(prefix="/api/v1/settlement", tags=["Settlement & Building"])

@settlement_router.post("/found", summary="开辟根据地", response_model=SettlementActionResponse)
async def settlement_found_endpoint(request: SettlementActionRequest):
    """
    🏗️ 开辟新根据地
    
    触发条件：玩家到达特定节点，满足开荒条件
    功能：初始化根据地状态，生成开荒叙事，扣除开荒资源
    
    📌 未来扩展：
    - 多根据地支持
    - 根据地特色加成（根据地理位置）
    - 开荒难度选择
    """
    result = await PetRaisingAgent.handle_settlement_action(request)
    
    # 写入历史总线
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【开荒】{result.narrative}",
        "time": time_str
    })
    
    return result

@settlement_router.post("/build", summary="建造/升级建筑", response_model=SettlementActionResponse)
async def settlement_build_endpoint(request: BuildConstructRequest):
    """
    🏗️ 建造或升级建筑
    
    功能：
    - 检查资源是否充足
    - 检查前置条件（等级/前置建筑）
    - 加入建造队列或立即完成
    - 生成幻灵参与建造的叙事
    
    📌 未来扩展：
    - 建造时间机制（实时/加速）
    - 多幻灵协作建造加速
    - 建筑皮肤/外观自定义
    - 建筑连锁加成效果
    """
    result = await PetRaisingAgent.handle_building_construct(request)
    
    # 写入历史总线
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【建造】{result.narrative}",
        "time": time_str
    })
    
    return result

@settlement_router.post("/repair", summary="修复建筑", response_model=SettlementActionResponse)
async def settlement_repair_endpoint(request: SettlementActionRequest):
    """
    🔧 修复受损建筑
    
    触发场景：
    - 自然灾害事件后
    - 外敌入侵后
    - 建筑耐久自然衰减
    
    📌 未来扩展：
    - 自动修复机制（高级建筑）
    - 修复材料选择影响修复质量
    """
    result = await PetRaisingAgent.handle_building_repair(request)
    
    # 写入历史总线
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【修复】{result.narrative}",
        "time": time_str
    })
    
    return result

@settlement_router.post("/assign", summary="分配幻灵到建筑", response_model=SettlementActionResponse)
async def settlement_assign_endpoint(request: SettlementActionRequest):
    """
    🐾 分配幻灵到建筑工作
    
    功能：
    - 幻灵入驻建筑，提供加成效果
    - 根据幻灵性格/种族/属性产生不同效率
    - 生成幻灵工作叙事
    
    📌 未来扩展：
    - 幻灵工作疲劳度
    - 幻灵技能与建筑匹配度
    - 幻灵工作心情影响效率
    - 自动分配 AI
    """
    result = await PetRaisingAgent.handle_pet_assignment(request)
    
    # 写入历史总线
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【分配】{result.narrative}",
        "time": time_str
    })
    
    return result

@settlement_router.post("/collect", summary="收集资源/产出", response_model=SettlementActionResponse)
async def settlement_collect_endpoint(request: SettlementActionRequest):
    """
    📦 收集建筑产出或资源点采集
    
    功能：
    - 收集建筑定时产出
    - 采集资源点资源
    - 结算离线期间累积产出
    
    📌 未来扩展：
    - 仓库容量限制
    - 资源品质差异
    - 采集暴击/额外收获
    """
    result = await PetRaisingAgent.handle_resource_collection(request)
    
    # 写入历史总线
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【收集】{result.narrative}",
        "time": time_str
    })
    
    return result

@settlement_router.post("/event/tick", summary="根据地事件结算", response_model=SettlementActionResponse)
async def settlement_event_tick_endpoint(request: SettlementEventRequest):
    """
    ⏱️ 根据地事件周期结算
    
    触发时机：
    - 玩家上线时结算离线期间事件
    - 定期自动触发
    
    功能：
    - 计算建筑产出
    - 触发随机事件（正面/负面）
    - 幻灵工作状态结算
    - 资源自然恢复
    
    📌 未来扩展：
    - 事件链系统（连续事件）
    - 玩家选择影响事件走向
    - 聚落声望系统影响事件概率
    """
    result = await PetRaisingAgent.handle_settlement_tick(request)
    
    # 写入历史总线
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【结算】{result.narrative}",
        "time": time_str
    })
    
    return result

@settlement_router.get("/state/{pet_id}", summary="获取根据地状态")
async def settlement_state_endpoint(pet_id: str):
    """
    📊 获取根据地完整状态
    
    📌 未来扩展：
    - 分页加载大型聚落数据
    - 增量同步机制
    """
    # TODO: 从数据库加载根据地状态
    # 当前返回空状态占位
    return {
        "settlement_id": f"settlement_{pet_id}",
        "name": "无名营地",
        "level": 1,
        "prosperity": 0,
        "buildings": {},
        "resource_nodes": {},
        "storage": {},
        "is_established": False,
        "last_tick_time": datetime.now().isoformat()
    }

# 挂载路由
app.include_router(raising_router)
app.include_router(memory_api.router)  
app.include_router(history_api.router)
app.include_router(settlement_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)