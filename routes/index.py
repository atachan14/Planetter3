from flask import Blueprint, render_template, request, redirect, session, flash
from psycopg2.extras import RealDictCursor
from services.errors import AppError,InvalidStateError
import logging

logger = logging.getLogger(__name__)

from db import get_db
from services.data import (
    fetch_now,
    fetch_user_data,
    fetch_planet_data,
    fetch_surround_data,
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
        surround_data = None
        galaxyData = None

        if state == "landing":
            content_template = "main_content/landing.jinja"

        elif state == "planet":
            surround_data = fetch_surround_data(cur, self_data, planet_data)
            content_template = "main_content/planet.jinja"

        elif state == "galaxy":
            galaxyData = fetch_galaxy_data(cur, self_id)
            content_template = "main_content/galaxy.jinja"

        else:
            # 保険
            logger.warning(f"invalid state: {state}")
            raise InvalidStateError(f"invalid state: {state}")

    except AppError as e:
        return render_template("error.jinja", error_code=e.code)

    finally:
        cur.close()
        conn.close()

    return render_template(
        "main.jinja",
        content_template=content_template,
        self_data=self_data,
        planet_data=planet_data,

        surround_data=surround_data,
        galaxyData=galaxyData,
    )


@index_bp.route("/", methods=["POST"])
def index_post():
    action = request.form.get("action")

    auth_action(action)
    move_action(action)
    object_create(action)

    # その他 action

    return redirect("/")


def auth_action(action):
    if action == "login":
        handle_login(
            request.form.get("username"),
            request.form.get("password"),
            session,
        )

    if action == "logout":
        handle_logout(session)

def move_action(action):
    if action == "enter_planet":
        session["state"] = "planet"

    if action == "front_action":
        #あとで実装
        pass
    
    if action == "left_turn":
        #あとで実装
        pass
    
    if action == "right_turn":
        #あとで実装
        pass

def object_create(action):
    if action == "post_to_tile":
        #あとで実装
        pass
    
    if action == "post_to_page":
        #あとで実装
        pass
    if action == "page_to_tile":
        #あとで実装
        pass

    if action == "page_to_book":
        #あとで実装
        pass

    if action == "book_to_tile":
        #あとで実装
        pass
    
    if action == "book_to_shelf":
        #あとで実装
        pass
    
    if action == "shelf_to_tile":
        #あとで実装
        pass