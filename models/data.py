from dataclasses import dataclass, field
from datetime import datetime
from errors import MissingNowError
from utils.formatters import format_stardust

@dataclass
class CreatedAtMixin:
    created_at: datetime

    @property
    def f_created_at(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M")



@dataclass
class NowMixin(CreatedAtMixin):
    now: datetime | None

    @property
    def survive_days(self) -> int:
        if self.now is None:
            raise MissingNowError(
                "survive_days requires now, but now is None"
            )
        return (self.now.date() - self.created_at.date()).days
    
@dataclass
class User(NowMixin):
    id: int
    username: str
    planet_id: int
    x: int
    y: int
    direction: int
    stardust: int

    @property
    def f_stardust(self) -> str:
        return format_stardust(self.stardust)

@dataclass
class UserCount:
    user_id: int
    walk: int
    turn: int
    rocket: int
    kill: int
    post: int
    page: int
    book: int
    shelf: int
    planet: int
    special: int
    planet_draw: int
    user_draw: int



@dataclass
class Planet(NowMixin):
    id: int
    name: str
    width: int
    height: int
    created_name: str

@dataclass(frozen=True)
class Tile:
    kind: str
    content: str = ""
    
@dataclass(frozen=True)
class NoneTile(Tile):
    kind: str = "none"
    content: str = "none"
    
@dataclass
class Object(CreatedAtMixin):
    id: int
    kind: str
    content: str
    good:int
    bad:int
    created_name:str
    children: list["Object"] = field(default_factory=list)

@dataclass
class Surround:
    s4: Tile
    s5: Object | None
    s6: Tile
    s7: Tile
    s8: Tile
    s9: Tile