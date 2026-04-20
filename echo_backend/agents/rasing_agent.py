# echo_backend/agents/pet_raising_agent.py
import json
import re, os
from dotenv import load_dotenv
from openai import OpenAI
from schemas import RaisingInteractRequest, RaisingInteractResponse, OfflineTaskRequest, OfflineTaskResponse, LocationTaskRequest, LocationTaskResponse, SettlementActionRequest, SettlementActionResponse, BuildConstructRequest, SettlementEventRequest

# 为了模块化，我们假设你可以直接调用 router 内部函数，但在工业界通常提取 RAG 逻辑放到 core 中。
# 这里我们采用一种优雅的做法：通过 HTTP 内部调用或直接复用依赖功能。

import httpx # 

load_dotenv()

api_key = os.getenv('DOUBAO_API_KEY')
raising_model = os.getenv('DOUBAO_MODEL')
client = OpenAI(
    api_key=api_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)


def extract_json(text: str) -> dict:
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    if match: return json.loads(match.group(1))
    return json.loads(text)


def recall_memory_internal(pet_id: str, context: str) -> str:
    """提取相关记忆的内部包裹函数"""
    try:
        # 这里请求本地开启的 API
        resp = httpx.post("http://127.0.0.1:8000/api/v1/memory/recall", json={
            "pet_id": pet_id,
            "current_context": context,
            "top_k": 2
        })
        if resp.status_code == 200:
            memories = resp.json().get("memories", [])
            if memories:
                # 将结构化的记忆拼接成文本给大模型看
                return "\n".join([f"- 当时发生的事：{m['memory']} (情绪烙印: {m['emotion']})" for m in memories])
    except Exception as e:
        print(f"[记忆提取错误] {e}")
    return "脑子里一片空白，这似乎是第一次遇到这种事。"

def store_memory_internal(pet_id: str, event_text: str, emotion: str = "neutral"):
    """存储记忆的内部包裹函数"""
    try:
        httpx.post("http://127.0.0.1:8000/api/v1/memory/store", json={
            "pet_id": pet_id,
            "event_summary": event_text,
            "emotion_tag": emotion
        })
    except Exception as e:
        print(f"[记忆存储错误] {e}")


class PetRaisingAgent:
    @staticmethod
    async def handle_interaction(request: RaisingInteractRequest) -> RaisingInteractResponse:
        # 1. 玩家跟宠物发生的事
        current_event = f"玩家对我使用了：{request.action_type}。玩家说：{request.user_input or '无'}"
        
        # 2. 【RAG 环节】唤醒往事！根据这件事去查 ChromaDB
        past_memories = recall_memory_internal(request.pet_state.pet_id, current_event)

        system_prompt = f"""
        你是一个游戏中的宠物模拟引擎。当前宠物档案：
        名字: {request.pet_state.pet_name} | 物种: {request.pet_state.species} | 属性: {request.pet_state.element}
        性格: {request.pet_state.persona} | 好感度: {request.pet_state.trust_level}/100 | 心情: {request.pet_state.mood}/100
        
        【宠物脑海里浮现的往事回忆】：
        {past_memories}
        
        玩家现在的操作：【{request.action_type}】 (补充信息: {request.user_input or '无'})
        
        请结合性格分析，特别是联系上述的【往事回忆】，决定宠物的反应和数值变化。
        例如：如果回忆中主人打骂过你，即使现在喂你喜欢的东西，你也应该傲娇拒绝(is_refused=true)并在对话中翻旧账；
        如果回忆中你们有羁绊，对话就要显得亲昵。
        
        必须返回纯正的 JSON，格式如下：
        {{
            "dialogue": "文本描述或对话（请融合性格和回忆）",
            "mood_change": int,
            "trust_change": int,
            "is_refused": boolean,
            "sentiment_summary": "一句话总结这只宠物现在觉得发生了什么"
        }}
        """
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7
        )
        
        data = extract_json(response.choices[0].message.content)
        
        # 3. 将此次互动的结论形成长期记忆存入库中！
        # 我们用大模型总结出的 sentiment_summary 作为核心记忆，极致省流
        if "sentiment_summary" in data:
            emotion_tag = "happy" if data.get("trust_change", 0) >= 0 else "angry"
            store_memory_internal(request.pet_state.pet_id, data["sentiment_summary"], emotion_tag)

        return RaisingInteractResponse(**data)

    @staticmethod
    async def resolve_offline_task(request: OfflineTaskRequest) -> OfflineTaskResponse:
        # 定义引擎目前支持的合法操作字典（预留扩展性）
        allowed_tasks_info = """
        【合法任务库】
        - "周边采集": 耗时 2 小时。产出: 野果, 木材, 石头。
        - "体能特训": 耗时 3 小时。产出: 怪物牙齿。高耗体力。
        - "营地站岗": 耗时 4 小时。产出: 旧金币, 以太颗粒。
        """

        prompt = f"""
        你是游戏里的中央调度器和那只名叫"{request.pet_state.pet_name}"的幻灵(性格:{request.pet_state.persona})。
        主人离线了总共 {request.duration_hours} 小时。环境: {request.environment_desc}。
        {allowed_tasks_info}

        业务逻辑要求：
        1. 【模式判断】：
           - 玩家留言："{request.player_message or '无'}"
           - 如果有留言：进入【主动规划模式】。提取留言关键词，重新编排逻辑顺序。每次任务产出数量在 3~5 个。
           - 如果无留言：进入【被动摸鱼模式】。宠物每隔约 2 小时自己决定干一件事(根据性格)。由于没干劲，每次产出数量在 1~2 个。
        2. 【时间中断约束】：
           - 依次累加要做的任务耗时，不能超过 {request.duration_hours} 小时！如果当前任务执行到一半主人上线了(即剩余没凑够耗时)，该任务作废，不计入完成列表，拿不到奖励。
        
        必须严格返回 JSON 格式：
        {{
            "summary_journal": "宠物对这几个小时的总体逼逼叨(第一人称带性格)",
            "completed_tasks": [
                {{
                    "task_name": "周边采集", 
                    "cost_hours": 2, 
                    "journal": "摘了点果子", 
                    "reward_items": {{"野果": 2}}
                }}
            ],
            "total_stamina_consumed": 20
        }}
        """

        # 去掉 response_format，使用我们强大的 extract_json
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4 # 降低温度以保证逻辑算力和时间加法的严谨性
        )
        data = extract_json(response.choices[0].message.content)
        
        from schemas import OfflineTaskResponse, TaskResult
        
        tasks = []
        for t in data.get("completed_tasks", []):
            try:
                tasks.append(TaskResult(**t))
            except Exception:
                continue

        return OfflineTaskResponse(
            summary_journal=data.get("summary_journal", "发呆了一整天。"),
            completed_tasks=tasks,
            total_stamina_consumed=data.get("total_stamina_consumed", 0)
        )

    @staticmethod
    async def resolve_location_task(request: LocationTaskRequest) -> "LocationTaskResponse":
        """处理不同场景（城镇/野外营地）衍生的专属任务 (真实大模型介入)"""
        # 利用设定字典，限制大模型生成的奖励名称和数值范围
        prompt = f"""
        你是"{request.pet_state.pet_name}"(性格:{request.pet_state.persona})。
        你刚刚在 {request.location_category} 的 [{request.specific_node}] 完成了 [{request.action_type}] 任务，花费了{request.duration_hours}小时。
        
        【掉落与数值约束】
        1. 城镇任务(town)：通常奖励 "旧金币"、"黑面包"、"烤肉排"。心情容易变好，不会扣血(hp_change=0)。
        2. 野外任务(wild)：通常奖励 "怪物牙齿"、"古代遗迹碎片"、"曼德拉草"。可能有战斗导致扣血(-10到-30)。
        3. 数值限制：mood_change 和 trust_change 在 -10 到 +15 之间。
        
        请写一段生动的第一人称汇报(50字以内)。必须严格返回 JSON：
        {{
            "task_report": "任务汇报...",
            "reward_items": ["物品1", "物品2"],
            "mood_change": 5,
            "trust_change": 2,
            "hp_change": -5
        }}
        """
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "user", "content": prompt}],
        )
        data = extract_json(response.choices[0].message.content)
        
        from schemas import LocationTaskResponse
        return LocationTaskResponse(
            task_report=data.get("task_report", "任务完成了。"),
            reward_items=data.get("reward_items", []),
            mood_change=data.get("mood_change", 0),
            trust_change=data.get("trust_change", 0),
            hp_change=data.get("hp_change", 0)
        )

    @staticmethod
    async def check_mail_events(request: "MailCheckRequest") -> "MailCheckResponse":
        """处理好友交互/奇遇信件 (真实大模型介入)"""
        prompt = f"""
        请为幻灵 "{request.pet_state.pet_name}" 随机生成1封来自游戏世界NPC或野生生物的奇遇信件。
        发件人可以是："吟游诗人", "流浪的盗贼猫", "风车镇镇长", "神秘商人"。
        信件通常会附带1-2个对应身份的特有道具（如："盗贼的旧匕首"、"过期的劣质麦酒"、"锈迹斑斑的钥匙"）。
        内容要符合暗黑但带点幽默的旅行风。
        
        必须严格返回 JSON：
        {{
            "mails": [
                {{
                    "sender": "发件人名字",
                    "title": "信件标题",
                    "content": "信件正文",
                    "attached_items": ["道具A", "道具B"]
                }}
            ]
        }}
        """
        response = client.chat.completions.create(
            model=raising_model,
            messages=[{"role": "user", "content": prompt}],
        )
        data = extract_json(response.choices[0].message.content)
        
        from schemas import MailCheckResponse, MailEntity
        mails = [MailEntity(**m) for m in data.get("mails", [])]
        return MailCheckResponse(mails=mails)

    # ===== 🆕 模拟经营/根据地系统处理方法 =====
    
    @staticmethod
    async def handle_settlement_action(request: SettlementActionRequest) -> SettlementActionResponse:
        """
        🏗️ 处理根据地通用行动
        
        📌 当前实现：基础框架，返回模拟数据
        📌 未来扩展：
        - 接入大模型生成动态叙事
        - 根据幻灵性格影响建设效率/结果
        - 建设过程中触发特殊事件
        - 多幻灵协作叙事
        """
        # TODO: 接入大模型 Prompt
        # prompt = f"""
        # 幻灵 {request.pet_state.pet_name} (性格：{request.pet_state.persona}) 
        # 正在参与根据地行动：{request.action_type}
        # 请生成符合性格的叙事文本，描述幻灵的反应和行动过程。
        # """
        
        # 模拟返回
        narrative_map = {
            "found": f"哼，这片空地勉强能当营地吧！本大爷亲自选址，你可别浪费了啊！",
            "build": f"建造？这种粗活也要本大爷帮忙？...算了，看在你笨手笨脚的份上。",
            "repair": f"又坏了？你平时都不维护的吗！真是让人操心的笨蛋主人...",
            "assign": f"又要工作？好吧好吧，别拖我后腿就行。",
            "collect": f"收获还不错嘛，也不看看是谁在管理。",
        }
        
        return SettlementActionResponse(
            success=True,
            narrative=narrative_map.get(request.action_type, "行动完成。"),
            settlement_changes={},
            resource_cost={},
            resource_gain={},
            mood_change=5,
            trust_change=2,
            unlock_flags=[]
        )
    
    @staticmethod
    async def handle_building_construct(request: BuildConstructRequest) -> SettlementActionResponse:
        """
        🏗️ 处理建筑建造/升级
        
        📌 当前实现：占位方法
        📌 未来扩展：
        - 建筑配置表加载（成本/效果/前置条件）
        - 资源检查与扣除
        - 建造队列管理
        - 大模型生成建造叙事（幻灵吐槽/期待/自豪）
        - 建造完成解锁新功能提示
        """
        # TODO: 实现完整建造逻辑
        # 1. 检查资源是否充足
        # 2. 检查前置建筑/等级条件
        # 3. 扣除资源
        # 4. 创建/升级建筑
        # 5. 生成叙事
        
        return SettlementActionResponse(
            success=True,
            narrative=f"建造 {request.building_type} 完成！（模拟数据）",
            settlement_changes={
                "buildings": {
                    request.building_type: {
                        "level": 1,
                        "status": "normal"
                    }
                }
            },
            resource_cost={},
            resource_gain={},
            mood_change=3,
            trust_change=1,
            unlock_flags=[]
        )
    
    @staticmethod
    async def handle_building_repair(request: SettlementActionRequest) -> SettlementActionResponse:
        """
        🔧 处理建筑修复
        
        📌 未来扩展：
        - 修复成本计算
        - 幻灵修复效率差异
        - 修复叙事
        """
        # TODO: 实现修复逻辑
        return SettlementActionResponse(
            success=True,
            narrative="修复完成（占位）",
            settlement_changes={},
            resource_cost={},
            resource_gain={},
            mood_change=2,
            trust_change=1,
            unlock_flags=[]
        )
    
    @staticmethod
    async def handle_pet_assignment(request: SettlementActionRequest) -> SettlementActionResponse:
        """
        🐾 处理幻灵分配
        
        📌 未来扩展：
        - 幻灵属性/性格与建筑匹配度计算
        - 分配后效率加成
        - 幻灵工作心情变化
        - 分配叙事（幻灵喜欢/讨厌某工作）
        """
        # TODO: 实现分配逻辑
        return SettlementActionResponse(
            success=True,
            narrative="分配完成（占位）",
            settlement_changes={},
            resource_cost={},
            resource_gain={},
            mood_change=1,
            trust_change=1,
            unlock_flags=[]
        )
    
    @staticmethod
    async def handle_resource_collection(request: SettlementActionRequest) -> SettlementActionResponse:
        """
        📦 处理资源收集
        
        📌 未来扩展：
        - 建筑产出计算
        - 资源点采集逻辑
        - 离线累积产出
        - 暴击/额外收获
        """
        # TODO: 实现收集逻辑
        return SettlementActionResponse(
            success=True,
            narrative="收集完成（占位）",
            settlement_changes={},
            resource_cost={},
            resource_gain={"木材": 5, "石头": 3},
            mood_change=2,
            trust_change=1,
            unlock_flags=[]
        )
    
    @staticmethod
    async def handle_settlement_tick(request: SettlementEventRequest) -> SettlementActionResponse:
        """
        ⏱️ 处理根据地周期结算
        
        📌 未来扩展：
        - 建筑产出结算
        - 随机事件触发
        - 资源自然恢复
        - 幻灵工作状态结算
        - 大模型生成事件叙事
        """
        # TODO: 实现周期结算逻辑
        return SettlementActionResponse(
            success=True,
            narrative="周期结算完成（占位）",
            settlement_changes={},
            resource_cost={},
            resource_gain={},
            mood_change=0,
            trust_change=0,
            unlock_flags=[]
        )
