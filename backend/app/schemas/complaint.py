from pydantic import BaseModel
from typing import Optional

class ComplaintSchema(BaseModel):
    complaint_id: str
    category: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ward_number: Optional[int] = None
