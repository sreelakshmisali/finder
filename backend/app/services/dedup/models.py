from pydantic import BaseModel
from typing import Dict, Optional
import uuid

class DuplicateResult(BaseModel):
    is_duplicate: bool
    score: float
    matched_fields: Dict[str, float]
    duplicate_of_id: Optional[uuid.UUID] = None
