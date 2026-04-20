# agents/battle_agent.py
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from schemas import BattleTacticRequest, BattleActionResponse

load_dotenv()

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.getenv('DOUBAO_API_KEY'),
)
MODEL_NAME = os.getenv('DOUBAO_MODEL')

def generate_battle_action(req: BattleTacticRequest) -> dict:
    """极其泛化的战斗 Agent 计算机"""
    
    # 将列表转成好看的字符串
    env_str = ", ".join(req.env_tags) if req.env_tags else "空旷无物"
    skills_str = json.dumps(req.allowed_skills, ensure_ascii=False)
    
    sys_prompt = f"""
    【世界观设定】
    你处于一个名为《Project Echo》的游戏中，你是名为“{req.pet_state.pet_name}”的伙伴生物。
    你的属性是：{req.pet_state.element}。
    你当前的性格行为逻辑：{req.pet_state.persona}。
    当前状态：血量 {req.pet_state.hp}%，压力值 {(100 - req.pet_state.mood)/100}%。

    【当前战场环境】
    敌人：{req.enemy_desc}。
    周围可用环境/地势：{env_str}。

    【主人下达的战术指令】：
    “{req.player_input}”

    【你的任务与数据输出黑盒铁律】
    1. 你必须严格评估指令是否可行。结合你的性格、属性克制关系以及环境。
    2. 你必须从以下游戏引擎允许的技能ID中选择一项：{skills_str}。如果决定不行动或违抗指令，请填写 "NONE"。
    3. 你必须且只能输出合法的 JSON 格式。禁止任何 Markdown 记号和废话。

    输出 JSON 结构必须如下：
    {{
      "thought_process": "内在想法",
      "dialogue": "对主人说的话(符合性格和绝境情况)",
      "is_obedient": "(True/False)。玩家让它攻击，但如果它贪生怕死且好感度低，它可能会选择防御/无作为，此时返回 False.",
      "mood_delta": 整数(-10到10，代表听完这句话的心情变化),
      "skill_id": "选出的技能ID",
      "target": "技能选定的目标(敌人或环境物的名字)"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": sys_prompt}],
            temperature=0.2     # 偏向理智
        )
        
        raw_content = response.choices[0].message.content.strip()
        cleaned_content = re.sub(r"```[a-zA-Z]*", "", raw_content)
        cleaned_content = re.sub(r"```", "", cleaned_content).strip()
        
        return json.loads(cleaned_content)
        
    except Exception as e:
        print(f"Agent 调用异常: {e}")
        # 工业化兜底防崩
        return {
            "thought_process": "大脑混乱了",
            "dialogue": "啊头好痛，网络信号不好，我直接随便咬一口吧！",
            "is_obedient": "强制降级攻击",
            "mood_delta": 0,
            "skill_id": req.allowed_skills[0] if req.allowed_skills else "NONE",
            "target": "敌人本体"
        }