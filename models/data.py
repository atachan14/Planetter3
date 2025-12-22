from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    username: str
    planet_id: int
    x: int
    y: int
    direction: int
    stardust: int
    created_at: datetime

    now: datetime

    @property
    def survive_days(self):
        return (self.now.date() - self.created_at.date()).days


@dataclass
class Planet:
    id: int
    name: str
    width: int
    height: int
    created_at: datetime
    created_name: str
    
    now: datetime

    @property
    def survive_days(self):
        return (self.now.date() - self.created_at.date()).days


@dataclass(frozen=True)
class Tile:
    kind: str
    content: str = ""
    
@dataclass(frozen=True)
class NoneTile(Tile):
    kind: str = "none"
    content: str = ""
    
@dataclass
class Object:
    id: int
    kind: str
    content: str
    children: list["Object"] = field(default_factory=list)

@dataclass
class Surround:
    s4: Tile
    s5: Object | None
    s6: Tile
    s7: Tile
    s8: Tile
    s9: Tile