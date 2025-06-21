from pydantic import BaseModel
from typing import Optional, Dict

class ActionRequest(BaseModel):
    org: str
    repo: str
    action: str
    parameters: Optional[Dict[str, str]]

class AuditRecord(BaseModel):
    user: str
    ip: str
    timestamp: str
    org: str
    repo: str
    action: str
    result: str
