from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2.extras import RealDictCursor
from flask import flash

from db import get_db
from services.action.move import land_on_planet

BEGINNERS_PLANET_ID = 1


def handle_login(username: str, password: str, session):
    if not username or not password:
        flash("未入力です", "login_error")

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            "SELECT id, password_hash FROM users WHERE username = %s",
            (username,)
        )
        user = cur.fetchone()

        if user is None:
            # 新規作成
            password_hash = generate_password_hash(password)

            cur.execute(
                """
                INSERT INTO users (username, password_hash, planet_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (username, password_hash, BEGINNERS_PLANET_ID)
            )
            self_id = cur.fetchone()["id"]

            land_on_planet(cur, self_id, BEGINNERS_PLANET_ID)
            conn.commit()

        else:
            self_id = user["id"]
            stored_hash = user["password_hash"]

            if not check_password_hash(stored_hash, password):
                flash("パスワードが違います", "login_error")
                return

        session["self_id"] = self_id
        session["state"] = "landing"
        return 

    finally:
        cur.close()
        conn.close()


def handle_logout(session):
    session.clear()
