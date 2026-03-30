from dataclasses import dataclass
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