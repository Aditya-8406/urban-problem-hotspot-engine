from pydantic import BaseModel

class HotspotSchema(BaseModel):
    cluster_id: int
    category: str
    priority_score: float
    priority_level: str
