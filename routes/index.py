from flask import Blueprint, render_template, request, redirect, session, flash
from psycopg2.extras import RealDictCursor

from db import get_db
from services.data import (
    fetch_now,
    fetch_user_data,
    fetch_planet_data,
    fetch_surround_data,
    fetch_here_data,
    fetch_galaxy_data,
)

from services.auth import handle_login, handle_logout


index_bp = Blueprint("index", __name__)


@index_bp.route("/", methods=["GET"])
def index_get():
    if "self_id" not in session:
        return render_template("top.jinja")

    self_id = session["self_id"]
    state = session.get("state", "landing")

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 共通データ
        db_now = fetch_now(cur)
        self_data = fetch_user_data(cur, self_id, db_now)
        planet_data = fetch_planet_data(cur, self_data.planet_id,db_now)

    # デフォルト
        surroundData = None
        galaxyData = None

        if state == "landing":
            content_template = "landing.jinja"

        elif state == "planet":
            surroundData = fetch_surround_data(cur, self_id)
            content_template = "planet.jinja"

        elif state == "galaxy":
            galaxyData = fetch_galaxy_data(cur, self_id)
            content_template = "galaxy.jinja"

        else:
            # 保険
            content_template = "error.jinja"

    finally:
        cur.close()
        conn.close()

    return render_template(
        "main.jinja",
        content_template=content_template,
        self_data=self_data,
        planet_data=planet_data,

        surroundData=surroundData,
        galaxyData=galaxyData,
    )


@index_bp.route("/", methods=["POST"])
def index_post():
    action = request.form.get("action")

    if action == "login":
        handle_login(
            request.form.get("username"),
            request.form.get("password"),
            session,
        )

    if action == "logout":
        handle_logout(session)

    if action == "go_planet":
        #　ここを通ったか確認するためのデバッグログ出したいんだけど何て書けばいい？
        session["state"] = "planet"

    # その他 action
    return redirect("/")
