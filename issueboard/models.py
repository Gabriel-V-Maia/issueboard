from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Issue:
    id:         int
    title:      str
    url:        str
    state:      str
    labels:     list
    repo:       str
    number:     int
    assignee:   Optional[str] = None
    created_at: str = ""
    body:       str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Issue":
        return Issue(**d)