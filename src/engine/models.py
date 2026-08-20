from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any

class Severity(str, Enum):
    OK="OK"; INFO="INFO"; UNKNOWN="UNKNOWN"; WARN="WARN"; FAIL="FAIL"; CRITICAL="CRITICAL"

@dataclass
class Check:
    name: str
    severity: Severity
    message: str
    value: Any = None
    details: str = ""
    recommendation: str = ""
    elapsed: float = 0.0
    def to_dict(self):
        d=asdict(self); d["severity"]=self.severity.value; return d

@dataclass
class Finding:
    title: str
    confidence: str
    evidence: str
    recommendation: str
    severity: Severity = Severity.WARN
    def to_dict(self):
        d=asdict(self); d["severity"]=self.severity.value; return d

@dataclass
class ActionResult:
    name: str
    success: bool
    message: str
    details: str = ""
    requires_admin: bool = False
    def to_dict(self): return asdict(self)
