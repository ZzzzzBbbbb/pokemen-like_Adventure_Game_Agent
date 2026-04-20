# main.py
from fastapi import FastAPI, APIRouter
from schemas import BattleTacticRequest, RaisingInteractRequest, RaisingInteractResponse, OfflineTaskRequest, OfflineTaskResponse
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

app.include_router(raising_router)
app.include_router(memory_api.router)  
app.include_router(history_api.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)