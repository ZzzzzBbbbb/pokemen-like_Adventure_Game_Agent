# echo_backend/routers/memory_api.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import chromadb, os
from openai import OpenAI
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from datetime import datetime
import uuid
import time,torch

# ============ RAG 路由器 ============
router = APIRouter(prefix="/api/v1/memory", tags=["RAG Memory"])


_chroma_client = None

class LocalQwenEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        
        print("💡 [系统] 正在将 Qwen-Embedding 载入 A800 显卡存...")
        self.model = SentenceTransformer(
            "Qwen/Qwen3-Embedding-8B",
            model_kwargs={
                "attn_implementation": "eager",
                "torch_dtype": torch.bfloat16,              
                "trust_remote_code": True,              
            }
        )
        print("✅ [系统] 模型已就绪，GPU 加速已激活。")

    def __call__(self, input: Documents) -> Embeddings:
        # 直接利用显卡将一批文本转换为高维矩阵，速度非常快
        # tolist() 是因为 ChromaDB 要求输入原生的 Python List
        embeddings = self.model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()

# ----------------- 路由配置 -----------------
router = APIRouter(prefix="/api/v1/memory", tags=["宠物长期记忆库"])

_chroma_client = None

def get_db():
    global _chroma_client
    if _chroma_client is None:
        db_path = os.path.join(os.getcwd(), "server_storage", "memories")
        _chroma_client = chromadb.PersistentClient(path=db_path)
    
    # 将包含 A800 的函数传递给数据库，彻底掌控翻译大权
    return _chroma_client.get_or_create_collection(
        name="global_pet_memories_qwen", 
        embedding_function=LocalQwenEmbeddingFunction()
    )

# ============ 2. 数据契约 ============
class MemorizeRequest(BaseModel):
    pet_id: str = Field(..., description="宠物全局唯一且含时间戳的实体ID (例: pet_user123_dog1)")
    event_summary: str = Field(..., description="要求：已凝练过的核心记忆文本，切忌输入废话")
    emotion_tag: str = Field("neutral", description="情绪标签：happy/angry/fear/sad")
    importance: int = Field(1, ge=1, le=5, description="1(日常小事) - 5(生离死别)")

class RecallRequest(BaseModel):
    pet_id: str
    current_context: str = Field(..., description="当前发生的事件，用于语义相似度匹配")
    top_k: int = 3

# ============ 3. 核心 API 端点 ============

@router.post("/store", summary="写入长期记忆 (烙印)")
async def store_memory(req: MemorizeRequest, collection = Depends(get_db)):
    """
    商业实践：存入时，除了文本，必须带上多维 metadata 以备极其复杂的联合检索
    """
    try:
        # 生成基于时间戳排序的粗略 UUID，防止碰撞
        doc_id = f"mem_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"
        
        collection.add(
            documents=[req.event_summary],
            metadatas=[{
                "pet_id": req.pet_id,              # 🔑 多租户核心：用于严格隔离数据
                "emotion": req.emotion_tag,        # 用于日后只检索“开心”的回忆
                "importance": req.importance,      # 用于优先提取重要记忆
                "timestamp": datetime.now().isoformat()
            }],
            ids=[doc_id]
        )
        return {"status": "success", "memory_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write error: {str(e)}")

@router.post("/recall", summary="唤醒联想记忆")
async def recall_memory(req: RecallRequest, collection = Depends(get_db)):
    """
    商业实践：并非查出来就完事，还要对查出的记忆做按时间排序或去重处理
    """
    try:
        results = collection.query(
            query_texts=[req.current_context],
            n_results=req.top_k,
            where={"pet_id": req.pet_id} # 🔑 多租户核心：绝对不能查出其他玩家宠物的记忆
        )
        
        memories = results.get("documents", [[]])[0]
        metadata_list = results.get("metadatas", [[]])[0]
        
        # 封装为前端或 AI 容易理解的格式
        structured_memories = [
            {"memory": text, "emotion": meta["emotion"], "time": meta["timestamp"]}
            for text, meta in zip(memories, metadata_list)
        ]
        
        return {
            "status": "success", 
            "memories": structured_memories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))