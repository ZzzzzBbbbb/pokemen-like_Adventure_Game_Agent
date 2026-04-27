import json, os
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class FusionRecord:
    source_id: str
    source_type: str
    used_in: List[str] = field(default_factory=list)
    fusion_count: int = 0
    last_used: str = ""
    tag_extracted: List[str] = field(default_factory=list)

@dataclass
class GenerationRecord:
    """生成物记录 - 追踪已生成的内容"""
    generated_id: str
    generated_type: str
    source_elements: List[str] = field(default_factory=list)
    tags:List[str] = field(default_factory=list)             
    created_at: str = ""

class ResourcePool:
    def __init__(self, pool_file: str = "./output/resource_pool_state.json"):
        self.pool_file = os.path.join(os.path.dirname(__file__), pool_file)
        self.fusion_records: Dict[str, FusionRecord] = {}
        self.generation_records: Dict[str, GenerationRecord] = {}
        self.global_tags:Dict[str, int] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.pool_file):
            with open(self.pool_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.fusion_records = {k: FusionRecord(**v) for k, v in data.get("fusion_records", {}).items()}
                self.generation_records = {k: GenerationRecord(**v) for k, v in data.get("generation_records", {}).items()}
                self.global_tags = data.get("global_tags", {})

    def save(self):
        os.mkdirs(os.path.dirname(self.pool_file), exist_ok=True)                                                  
        data = {
            'fusion_records': {k: asdict(v) for k, v in self.fusion_records.items()},
            'generation_records': {k: asdict(v) for k, v in self.generation_records.items()},
            'global_tags': self.global_tags,
            'last_updated': datetime.now().isoformat()
        }
    
    def register_source(self, source_id, source_type, tags: List[str] = None):
        if source_id not in self.fusion_records:
            self.fusion_records[source_id] = FusionRecord(source_id=source_id, source_type=source_type, tags_extracted=tags or [])

    def get_available_sources(self, source_type: str, count: int, exclude_used: bool = True, max_reuse: int = 3) -> List[str]:
        candidates = []
        
        for sid, rec in self.fusion_records.items():
            if rec.source_type != source_type:
                    continue
            if rec.fusion_count < max_reuse:
               score = rec.fusion_count * 100
               candidates.append((sid, score))

        candidates.sort(key=lambda x: x[1])
        return [sid for sid, _ in candidates[:count]]
    
    def check_reuse_rate(self, source_ids: List[str]) -> float:

        if not source_ids:
            return 0.0
        total = sum(self.fusion_records.get(sid, FusionRecord(sid, "")).fusion_count for sid in source_ids)
        
        return total / len(source_ids)

    def record_fusion(self, source_ids: List[str], generated_id: str, generated_type: str, tags: List[str]):

        now = datetime.now().isoformat()
        for sid in source_ids:
            if sid not in self.fusion_records:
                self.fusion_records[sid] = FusionRecord(sid, "unknown")
            rec = self.fusion_records[sid]
            rec.fusion_count += 1
            rec.last_used = now
            rec.used_in.append(generated_id)

        self.generation_records[generated_id] = GenerationRecord(
            generated_id=generated_id,
            generated_type=generated_type,
            source_elements=source_ids,
            tags=tags,
            created_at=now
        )

        for tag in tags:
            self.global_tags[tag] = self.global_tags.get(tag, 0) + 1

    def get_tag_diversity_report(self) -> Dict:

        total_generations = len(self.generation_records)
        return {
            'total_generations': total_generations,
            'unique_tags': len(self.global_tags),
            'tag_distribution': dict(sorted(
                self.global_tags.items(), key=lambda x: x[1], reverse=True
            )[:20]),
        'reuse_stats': {
            'source_never_used': sum(1 for r in self.fusion_records.values() if r.fusion_count == 0),
            'source_reused': sum(1 for r in self.fusion_records.values() if r.fusion_count > 0),
            }
        }

    def is_generated(self, generated_id: str) -> bool:
        return generated_id in self.generation_records
    
    def get_generation_ids(self, generated_type: str)-> List[str]:
        return [gid for gid, rec in self.generation_records.items() if rec.generated_type == generated_type]

_resource_pool_instance: Optional[ResourcePool] = None

def get_resource_pool() -> Optional[ResourcePool]:
    global _resource_pool_instance
    if _resource_pool_instance is None:
        _resource_pool_instance = ResourcePool()
    return _resource_pool_instance

