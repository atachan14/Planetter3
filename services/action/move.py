
from services.data import (
    fetch_db_now,
    fetch_latest_user_data,
    fetch_planet_data,
    fetch_user_at,
)
from errors import InvalidStateError
from services.spatial import rotate_delta,wrap_coord


def handle_to_front(cur,session):
    self_id = session.get("self_id")
    if not self_id:
        raise InvalidStateError("to_front without login")

    now = fetch_db_now(cur)
    self_data = fetch_latest_user_data(cur, self_id, now)
    planet_data = fetch_planet_data(cur, self_data.planet_id, now)

    # ここから前方判定
    dx, dy = 0, -1
    rdx, rdy = rotate_delta(dx, dy, self_data.direction)

    tx = self_data.x + rdx
    ty = self_data.y + rdy
    wtx, wty = wrap_coord(tx, ty, planet_data)

    target_user = fetch_user_at(cur, planet_data.id, wtx, wty)

    if target_user:
        handle_contact(session, target_user)
    else:
        handle_walk(cur, self_data, wtx, wty)

def handle_contact(session,target_user):
    session["state"]="contact"
    session["contact_target_id"]=target_user.id


def handle_walk(cur, self_data, wtx, wty):
    cur.execute(
        """
        UPDATE users
        SET x = %s, y = %s
        WHERE id = %s
        """,
        (wtx, wty, self_data.id)
    )
    cur.execute(
        """
        UPDATE user_counts
        SET walk = walk + 1
        WHERE user_id = %s
        """,
        (self_data.id,),
    )
    
def handle_turn(cur, self_id, turn: int):
    if not self_id:
        raise InvalidStateError("turn without login")

    cur.execute(
        """
        UPDATE users
        SET direction = (direction + %s + 4) %% 4
        WHERE id = %s
        """,
        (turn, self_id)
    )
    cur.execute(
        """
        UPDATE user_counts
        SET turn = turn + 1
        WHERE user_id = %s
        """,
        (self_id,),
    )

def handle_kill(cur, session, target_id):

    self_id = session["self_id"]
    # ① まず target の stardust を取得
    cur.execute(
        """
        SELECT stardust
        FROM users
        WHERE id = %s
        FOR UPDATE;
        """,
        (target_id,)
    )
    row = cur.fetchone()
    if row is None:
        # すでに存在しないなら何もしない or abort
        return

    gained = row["stardust"]

    # ② session に結果を積む（表示用）
    session["result"] = gained

    # ③ 自分の stardust を加算
    cur.execute(
        """
        UPDATE users
        SET stardust = stardust + %s
        WHERE id = %s
        """,
        (gained, self_id)
    )

    # ④ target を DELETE（ここで CASCADE 発動）
    cur.execute(
        """
        DELETE FROM users
        WHERE id = %s
        """,
        (target_id,)
    )

