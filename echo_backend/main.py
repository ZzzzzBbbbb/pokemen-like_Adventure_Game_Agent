# main.py
from fastapi import FastAPI, APIRouter
from datetime import datetime
import schemas
from agents.rasing_agent import PetRaisingAgent
from routers import memory_api, history_api

app = FastAPI(title="Project Echo - Universal AI Gateway")

raising_router = APIRouter(prefix="/api/v1/raising", tags=["Pet Raising"])
settlement_router = APIRouter(prefix="/api/v1/settlement", tags=["Settlement & Building"])

# ===== 互动接口 =====
@raising_router.post("/interact", response_model=schemas.RaisingInteractResponse)
async def pet_interact_endpoint(request: schemas.RaisingInteractRequest):
    result = await PetRaisingAgent.handle_interaction(request)
    from routers.history_api import append_to_history
    time_str = datetime.now().strftime("%H:%M")
    if request.user_input:
        append_to_history(request.pet_state.pet_id, {
            "sender": "player",
            "name": "玩家",
            "text": f"[{request.action_type}] {request.user_input}",
            "time": time_str
        })
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": result.dialogue,
        "time": time_str
    })
    return result

# ===== 离线挂机接口 =====
@raising_router.post("/offline_task", response_model=schemas.OfflineTaskResponse)
async def pet_offline_task_endpoint(request: schemas.OfflineTaskRequest):
    result = await PetRaisingAgent.resolve_offline_task(request)
    from routers.history_api import append_to_history
    time_str = datetime.now().strftime("%H:%M")
    task_details = "，".join([f"[{t.task_name}]({t.cost_hours}h)" for t in result.completed_tasks])
    log_text = f"【离线汇总】{result.summary_journal} (完成: {task_details or '无事发生'})"
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": log_text,
        "time": time_str
    })
    return result

# ===== 场景任务接口 =====
@raising_router.post("/location_task", response_model=schemas.LocationTaskResponse)
async def location_task_endpoint(request: schemas.LocationTaskRequest):
    result = await PetRaisingAgent.resolve_location_task(request)
    from routers.history_api import append_to_history
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【任务汇报】{result.task_report}",
        "time": time_str
    })
    return result

# ===== 邮件接口 =====
@raising_router.post("/mail/check", response_model=schemas.MailCheckResponse)
async def mail_check_endpoint(request: schemas.MailCheckRequest):
    result = await PetRaisingAgent.check_mail_events(request)
    return result

# ===== 根据地接口 =====
@settlement_router.post("/found", response_model=schemas.SettlementActionResponse)
async def settlement_found_endpoint(request: schemas.SettlementActionRequest):
    result = await PetRaisingAgent.handle_settlement_action(request)
    from routers.history_api import append_to_history
    time_str = datetime.now().strftime("%H:%M")
    append_to_history(request.pet_state.pet_id, {
        "sender": "pet",
        "name": request.pet_state.pet_name,
        "text": f"【开荒】{result.narrative}",
        "time": time_str
    })
    return result

@settlement_router.post("/build", response_model=schemas.SettlementActionResponse)
async def settlement_build_endpoint(request: schemas.BuildConstructRequest):
    result = await PetRaisingAgent.handle_building_construct(request)
    return result

@settlement_router.post("/repair", response_model=schemas.SettlementActionResponse)
async def settlement_repair_endpoint(request: schemas.SettlementActionRequest):
    result = await PetRaisingAgent.handle_building_repair(request)
    return result

@settlement_router.post("/assign", response_model=schemas.SettlementActionResponse)
async def settlement_assign_endpoint(request: schemas.SettlementActionRequest):
    result = await PetRaisingAgent.handle_pet_assignment(request)
    return result

@settlement_router.post("/collect", response_model=schemas.SettlementActionResponse)
async def settlement_collect_endpoint(request: schemas.SettlementActionRequest):
    result = await PetRaisingAgent.handle_resource_collection(request)
    return result

@settlement_router.post("/event/tick", response_model=schemas.SettlementActionResponse)
async def settlement_event_tick_endpoint(request: schemas.SettlementEventRequest):
    result = await PetRaisingAgent.handle_settlement_tick(request)
    return result

@settlement_router.get("/state/{pet_id}")
async def settlement_state_endpoint(pet_id: str):
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
app.include_router(settlement_router)
app.include_router(memory_api.router)
app.include_router(history_api.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)