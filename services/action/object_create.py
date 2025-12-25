from services.data import fetch_user_data
from errors import DomainDataError


def create_to_new_tile(cur,*,user_id,kind,content):
    user_data=fetch_user_data(cur,user_id,None)

    object_id = create_object(
        cur,
        kind=kind,
        content=content,
        created_name=user_data.username,
    )
    attach_object_to_new_tile(
        cur,
        object_id=object_id,
        planet_id=user_data.planet_id,
        x=user_data.x,
        y=user_data.y,
    )    
    
def create_to_parent(cur,*,user_id,kind: str,content: str,parent_id: int):

    user_data=fetch_user_data(cur,user_id,None)

    object_id = create_object(
        cur,
        kind=kind,
        content=content,
        created_name=user_data.username,
    )
    attach_object_to_parent(
        cur,
        parent_id=parent_id,
        child_id=object_id,
    )

def create_to_tile_with_children(cur,*,user_id,kind,content):

    user = fetch_user_data(cur, user_id,None)

    object_id = create_object(
        cur,
        kind=kind,
        content=content,
        created_name=user.username,
    )

    attach_object_to_tile_with_children(
        cur,
        object_id=object_id,
        planet_id=user.planet_id,
        x=user.x,
        y=user.y,
    )



def create_object(cur, *, kind: str, content: str, created_name: str) -> int:
    cur.execute("""
        INSERT INTO objects (kind, content, created_name, created_at)
        VALUES (%s, %s, %s, NOW())
        RETURNING id
    """, (kind, content, created_name))
    return cur.fetchone()["id"]

def attach_object_to_new_tile(cur, *, object_id: int, planet_id: int, x: int, y: int):
    cur.execute("""
        INSERT INTO object_tiles (object_id, planet_id, x, y)
        VALUES (%s, %s, %s, %s)
    """, (object_id, planet_id, x, y))


def attach_object_to_parent(cur, *, parent_id: int, child_id: int):
    if parent_id == child_id:
        raise DomainDataError("object cannot be parent of itself")

    cur.execute("""
        SELECT 1 FROM object_relations
        WHERE child_id = %s
    """, (child_id,))

    if cur.fetchone():
        raise DomainDataError("object already has a parent")

    # 新しい親に接続
    cur.execute("""
        INSERT INTO object_relations (parent_id, child_id)
        VALUES (%s, %s)
    """, (parent_id, child_id))


def attach_object_to_tile_with_children(
    cur,
    *,
    object_id: int,      # 新しく作った container（page/book/shelf）
    planet_id: int,
    x: int,
    y: int,
):
    # 1) 既存の tile 直下 object を取得
    cur.execute("""
        SELECT object_id
        FROM object_tiles
        WHERE planet_id = %s AND x = %s AND y = %s
    """, (planet_id, x, y))
    row = cur.fetchone()

    if row is None:
        # ここは設計次第：無いならエラー or そのまま置く
        raise DomainDataError("no object on tile to attach as child")

    child_object_id = row["object_id"]

    if child_object_id == object_id:
        raise DomainDataError("object cannot be parent of itself")

    # 2) tile の直下を新しい container に差し替え（UPDATE方式）
    cur.execute("""
        UPDATE object_tiles
        SET object_id = %s
        WHERE planet_id = %s AND x = %s AND y = %s
    """, (object_id, planet_id, x, y))

    # 3) container の子にする
    cur.execute("""
        INSERT INTO object_relations (parent_id, child_id)
        VALUES (%s, %s)
    """, (object_id, child_object_id))
