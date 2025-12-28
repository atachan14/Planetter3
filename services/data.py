from datetime import timedelta
from models.data import Object
from models.data import User, Planet, UserCount,Tile, NoneTile, Object, Surround
from services.spatial import SURROUND_BASE, rotate_delta, wrap_coord
from errors import DomainDataError
import logging


logger = logging.getLogger(__name__)

STARDUST_UNIT_SEC = 1 

def fetch_db_now(cur):
    cur.execute("SELECT now()")
    return cur.fetchone()["now"]


def fetch_latest_user_data(cur, user_id, db_now) -> User | None:

    update_stardust(cur, user_id, db_now)

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
        now=db_now,
    )

def fetch_user_pos(cur, user_id):
    cur.execute("""
        SELECT x, y, direction, planet_id
        FROM users
        WHERE id = %s
    """, (user_id,))
    return cur.fetchone()

def update_stardust(cur, user_id, db_now):
    cur.execute("""
        SELECT stardust, last_updated
        FROM users
        WHERE id = %s
        FOR UPDATE
    """, (user_id,))

    row = cur.fetchone()
    if not row:
        return

    last_stardust = row["stardust"]
    last_date = row["last_updated"] or db_now

    delta_sec = (db_now - last_date).total_seconds()
    gain = int(delta_sec // STARDUST_UNIT_SEC)
    if gain <= 0:
        return
 
    new_stardust = last_stardust + gain
    new_updated_at = last_date + timedelta(
        seconds=gain * STARDUST_UNIT_SEC
    )

    cur.execute("""
        UPDATE users
        SET stardust = %s,
            last_updated = %s
        WHERE id = %s
    """, (new_stardust, new_updated_at, user_id))



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
def fetch_user_count(cur, user_id: int) -> UserCount | None:
    cur.execute(
        """
        SELECT
            user_id,
            walk,
            turn,
            kill,
            post,
            page,
            book,
            shelf,
            planet,
            special,
            rocket,
            planet_draw,
            user_draw
        FROM user_counts
        WHERE user_id = %s
        """,
        (user_id,),
    )

    row = cur.fetchone()
    if row is None:
        return None

    return UserCount(**row)


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


def fetch_tile_at(cur, planet_id: int, wtx: int, wty: int) -> Tile:
    """
    周囲表示用のタイルを取得する。
    - wtx, wty はすでに wrap 済み想定（spatial 側で処理）
    - 他ユーザーがいれば user を優先表示
    - object がなければ NoneTile
    """

    # ① 他ユーザー優先
    cur.execute("""
        SELECT username
        FROM users
        WHERE planet_id = %s
          AND x = %s
          AND y = %s
        LIMIT 1
    """, (planet_id, wtx, wty))

    user_row = cur.fetchone()
    if user_row:
        return Tile(
            kind="user",
            content=user_row["username"],
        )

    # ② オブジェクト（表示用情報だけ）
    cur.execute("""
        SELECT
            o.kind,
            o.content
        FROM object_tiles ot
        JOIN objects o ON o.id = ot.object_id
        WHERE
            ot.planet_id = %s
            AND ot.x = %s
            AND ot.y = %s
        LIMIT 1
    """, (planet_id, wtx, wty))

    obj_row = cur.fetchone()
    if obj_row:
        return Tile(
            kind=obj_row["kind"],
            content=obj_row["content"] or "",
        )

    # ③ 何もない
    return NoneTile()


def fetch_object_at(cur, planet_id: int, x: int, y: int) -> Object | None:
    """
    行動対象となる Object を取得する。
    - x, y は wrap 済み想定
    - user は扱わない
    - children（relations）を含めて返す
    """

    # ① 中心オブジェクト取得
    cur.execute("""
        SELECT
            o.id,
            o.kind,
            o.content,
            o.good,
            o.bad,
            o.created_at,
            o.created_name
        FROM object_tiles ot
        JOIN objects o ON o.id = ot.object_id
        WHERE
            ot.planet_id = %s
            AND ot.x = %s
            AND ot.y = %s
        LIMIT 1
    """, (planet_id, x, y))

    row = cur.fetchone()
    if row is None:
        return None

    obj = Object(
        id=row["id"],
        kind=row["kind"],
        content=row["content"],
        good=row["good"],
        bad=row["bad"],
        created_at=row["created_at"],
        created_name=row["created_name"],
        children=[],
    )

    # ② 子オブジェクト（relations / edges）
    fetch_object_children(cur, obj)

    return obj


def fetch_object_children(cur, parent, visited=None):
    if visited is None:
        visited = set()
    if parent.id in visited:
        logger.error("Detected circular object relation: %s", parent.id)
        raise DomainDataError("circular object relation")
    visited.add(parent.id)

    cur.execute("""
        SELECT
            o.id,
            o.kind,
            o.content,
            o.good,
            o.bad,
            o.created_at,
            o.created_name
        FROM object_relations r
        JOIN objects o ON o.id = r.child_id
        WHERE r.parent_id = %s
        ORDER BY r.child_id ASC
    """, (parent.id,))

    rows = cur.fetchall()
    for row in rows:
        child = Object(
            id=row["id"],
            kind=row["kind"],
            content=row["content"],
            good=row["good"],
            bad=row["bad"],
            created_at=row["created_at"],
            created_name=row["created_name"],
            children=[],
        )
        parent.children.append(child)

        # 再帰：この child の子も取る
        fetch_object_children(cur, child)


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
        rdx, rdy = rotate_delta(dx, dy, self_data.direction)

        # 生座標
        tx = self_data.x + rdx
        ty = self_data.y + rdy

        # トーラス補正
        wtx, wty = wrap_coord(tx, ty, planet_data)

        tiles[pos] = fetch_tile_at(cur, planet_data.id, wtx, wty)

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
