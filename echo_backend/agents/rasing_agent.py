# agents/rasing_agent.py
import httpx
from schemas import (
    RaisingInteractResponse, OfflineTaskResponse, TaskResult,
    LocationTaskResponse, MailCheckResponse, MailEntity,
    SettlementActionResponse, BuildConstructRequest
)

client = None  # 初始化你的LLM客户端
raising_model = "your_model_name"

def extract_json(text: str) -> dict:
    import json, re
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {}

class PetRaisingAgent:
    @staticmethod
    async def handle_interaction(request) -> RaisingInteractResponse:
        prompt = f"""
        你是"{request.pet_state.pet_name}"，性格：{request.pet_state.persona}。
        玩家动作：[{request.action_type}] {request.user_input}
        当前心情：{request.pet_state.mood}，信任度：{request.pet_state.trust_level}
        请生成符合性格的回复，并返回JSON：
        {{"dialogue": "回复内容", "mood_change": 数值, "trust_change": 数值, "is_refused": true/false}}
        """
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "user", "content": prompt}]
        )
        data = extract_json(response.choices[0].message.content)
        return RaisingInteractResponse(
            dialogue=data.get("dialogue", "汪？"),
            mood_change=data.get("mood_change", 0),
            trust_change=data.get("trust_change", 0),
            is_refused=data.get("is_refused", False)
        )

    @staticmethod
    async def resolve_offline_task(request) -> OfflineTaskResponse:
        allowed_tasks = """
        【合法任务库】
        - "周边采集": 耗时2小时。产出: 野果, 木材, 石头。
        - "体能特训": 耗时3小时。产出: 怪物牙齿。高耗体力。
        - "营地站岗": 耗时4小时。产出: 旧金币, 以太颗粒。
        """
        prompt = f"""
        你是"{request.pet_state.pet_name}"，性格：{request.pet_state.persona}。
        主人离线 {request.duration_hours} 小时，环境：{request.environment_desc}。
        留言：{request.player_message or '无'}
        {allowed_tasks}
        规则：
        1. 有留言→主动规划，产出3~5个；无留言→被动摸鱼，产出1~2个。
        2. 任务耗时累加不能超过总时长，不足则作废。
        返回JSON：
        {{"summary_journal": "总结", "completed_tasks": [{{"task_name": "", "cost_hours": 0, "journal": "", "reward_items": {{}}}}], "total_stamina_consumed": 0}}
        """
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        data = extract_json(response.choices[0].message.content)
        tasks = [TaskResult(**t) for t in data.get("completed_tasks", [])]
        return OfflineTaskResponse(
            summary_journal=data.get("summary_journal", "发呆了一整天。"),
            completed_tasks=tasks,
            total_stamina_consumed=data.get("total_stamina_consumed", 0)
        )

    @staticmethod
    async def resolve_location_task(request) -> LocationTaskResponse:
        prompt = f"""
        你是"{request.pet_state.pet_name}"，性格：{request.pet_state.persona}。
        在 {request.location_category} 的 [{request.specific_node}] 完成 [{request.action_type}]，耗时 {request.duration_hours} 小时。
        约束：
        - town: 奖励旧金币/食物，不扣血。
        - wild: 奖励材料/怪物掉落，可能扣血。
        - mood/trust变化范围 -10~+15。
        返回JSON：
        {{"task_report": "", "reward_items": [], "mood_change": 0, "trust_change": 0, "hp_change": 0}}
        """
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "user", "content": prompt}]
        )
        data = extract_json(response.choices[0].message.content)
        return LocationTaskResponse(
            task_report=data.get("task_report", "任务完成。"),
            reward_items=data.get("reward_items", []),
            mood_change=data.get("mood_change", 0),
            trust_change=data.get("trust_change", 0),
            hp_change=data.get("hp_change", 0)
        )

    @staticmethod
    async def check_mail_events(request) -> MailCheckResponse:
        prompt = f"""
        为幻灵"{request.pet_state.pet_name}"生成1封奇遇信件。
        发件人可选：吟游诗人、流浪盗贼猫、风车镇镇长、神秘商人。
        附带1-2个道具。
        返回JSON：
        {{"mails": [{{"sender": "", "title": "", "content": "", "attached_items": []}}]}}
        """
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "user", "content": prompt}]
        )
        data = extract_json(response.choices[0].message.content)
        mails = [MailEntity(**m) for m in data.get("mails", [])]
        return MailCheckResponse(mails=mails)

    # ===== 模拟经营占位方法 =====
    @staticmethod
    async def handle_settlement_action(request) -> SettlementActionResponse:
        narrative_map = {
            "found": "哼，这片空地勉强能当营地吧！本大爷亲自选址，你可别浪费了啊！",
            "build": "建造？这种粗活也要本大爷帮忙？...算了，看在你笨手笨脚的份上。",
            "repair": "又坏了？你平时都不维护的吗！真是让人操心的笨蛋主人...",
        }
        return SettlementActionResponse(
            success=True,
            narrative=narrative_map.get(request.action_type, "行动完成。"),
            settlement_changes={},
            resource_cost={},
            resource_gain={},
            mood_change=5,
            trust_change=2
        )

    @staticmethod
    async def handle_building_construct(request: BuildConstructRequest) -> SettlementActionResponse:
        return SettlementActionResponse(
            success=True,
            narrative=f"建造 {request.building_type} 完成！（模拟数据）",
            settlement_changes={"buildings": {request.building_type: {"level": 1, "status": "normal"}}},
            unlock_flags=[]
        )

    @staticmethod
    async def handle_building_repair(request) -> SettlementActionResponse:
        return SettlementActionResponse(success=True, narrative="修复完成（占位）")

    @staticmethod
    async def handle_pet_assignment(request) -> SettlementActionResponse:
        return SettlementActionResponse(success=True, narrative="分配完成（占位）")

    @staticmethod
    async def handle_resource_collection(request) -> SettlementActionResponse:
        return SettlementActionResponse(success=True, narrative="收集完成（占位）")

    @staticmethod
    async def handle_settlement_tick(request) -> SettlementActionResponse:
        return SettlementActionResponse(success=True, narrative="周期结算完成（占位）")