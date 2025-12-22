from models.data import User, Planet, Tile, NoneTile, Object, Surround


def fetch_now(cur):
    cur.execute("SELECT now()")
    return cur.fetchone()["now"]


def fetch_user_data(cur, user_id, now) -> User | None:
    cur.execute("""
        SELECT
            id,
            username,
            planet_id,
            x,
            y,
            direction,
            stardust,
            created_at
        FROM users
        WHERE id = %s
    """, (user_id,))

    row = cur.fetchone()
    if row is None:
        return None

    return User(
        id=row["id"],
        username=row["username"],
        planet_id=row["planet_id"],
        x=row["x"],
        y=row["y"],
        direction=row["direction"],
        stardust=row["stardust"],
        created_at=row["created_at"],
        now=now,
    )

def fetch_user_at(cur, planet_id: int, x: int, y: int) -> User | None:
    cur.execute("""
        SELECT id, username, planet_id, x, y, direction, stardust, created_at
        FROM users
        WHERE planet_id = %s AND x = %s AND y = %s
        LIMIT 1
    """, (planet_id, x, y))
    row = cur.fetchone()
    if row is None:
        return None
    return User(
        id=row["id"],
        username=row["username"],
        planet_id=row["planet_id"],
        x=row["x"],
        y=row["y"],
        direction=row["direction"],
        stardust=row["stardust"],
        created_at=row["created_at"],
        now=None,  # surround表示では不要なら None でOK
    )

def fetch_planet_data(cur, planet_id, now) -> Planet:
    cur.execute("""
        SELECT id, name, width, height, created_at, created_name
        FROM planets
        WHERE id = %s
    """, (planet_id,))

    row = cur.fetchone()
    if row is None:
        raise Exception("planet not found")

    return Planet(
        id=row["id"],
        name=row["name"],
        width=row["width"],
        height=row["height"],
        created_at=row["created_at"],
        created_name=row["created_name"],
        now=now,
    )


def rotate(dx: int, dy: int, direction: int) -> tuple[int, int]:
    if direction == 0:      # 上
        return dx, dy
    elif direction == 1:    # 右
        return -dy, dx
    elif direction == 2:    # 下
        return -dx, -dy
    elif direction == 3:    # 左
        return dy, -dx
    return dx, dy


SURROUND_BASE = {
    7: (-1, -1),
    8: (0, -1),
    9: (1, -1),
    4: (-1,  0),
    5: (0, 0),
    6: (1,  0),
}
def wrap_coord(x: int, y: int, planet: Planet) -> tuple[int, int]:
    return x % planet.width, y % planet.height

def fetch_tile_at(cur, planet_id,tx,ty):
    
    return

def fetch_object_at(cur,planet_id,tx,ty):
    return

def fetch_surround_data(cur, self_data: User, planet_data: Planet) -> Surround:
    # here (center)
    obj = fetch_object_at(
        cur,
        planet_data.id,
        self_data.x,
        self_data.y,
    )

    tiles: dict[int, Tile] = {}

    for pos, (dx, dy) in SURROUND_BASE.items():
        # 向き補正
        rdx, rdy = rotate(dx, dy, self_data.direction)

        # 生座標
        tx = self_data.x + rdx
        ty = self_data.y + rdy

        # トーラス補正
        tx, ty = wrap_coord(tx, ty, planet_data)

        # 他ユーザー優先
        other_user = fetch_user_at(cur, planet_data.id, tx, ty)
        if other_user:
            tiles[pos] = Tile(
                kind="user",
                content=other_user.username,
            )
            continue

        # 通常タイル
        tiles[pos] = fetch_tile_at(cur, planet_data.id, tx, ty)

    return Surround(
        s4=tiles[4],
        s5=obj,
        s6=tiles[6],
        s7=tiles[7],
        s8=tiles[8],
        s9=tiles[9],
    )

def fetch_galaxy_data():
    return
