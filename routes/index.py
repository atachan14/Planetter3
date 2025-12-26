from flask import Blueprint, render_template, request, redirect, session, flash
from psycopg2.extras import RealDictCursor
from errors import AppError,InvalidStateError,OperationAborted
import logging

logger = logging.getLogger(__name__)

from db import get_db
from services.data import (
    fetch_now,
    fetch_latest_user_data,
    fetch_user_count,
    fetch_planet_data,
    fetch_surround_data,
    fetch_galaxy_data,
)

from services.action.auth import handle_login, handle_logout
from services.action.move import handle_to_front, handle_turn,handle_kill
from services.action.object_create import (
    create_to_new_tile,
    create_to_parent,
    create_to_tile_with_children,
)


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
        self_data = fetch_latest_user_data(cur, self_id, db_now)
        planet_data = fetch_planet_data(cur, self_data.planet_id,db_now)

    # デフォルト
        datas = {}
        dialog = session.pop("dialog", None)
        result = session.pop("result", None)

        if state == "landing":
            content_template = "main_content/landing.jinja"

        elif state == "planet":
            datas["surround"] = fetch_surround_data(cur, self_data, planet_data)
            content_template = "main_content/planet.jinja"

        elif state == "galaxy":
            datas["galaxy"] = fetch_galaxy_data(cur, self_id)
            content_template = "main_content/galaxy.jinja"

        elif state in ("contact", "killed"):
            contact_target_id = session.get("contact_target_id")
            if not contact_target_id:
                logger.warning("contact state without contact_target_id")
                raise InvalidStateError("contact without target")

            datas["target"] = fetch_latest_user_data(cur, contact_target_id, db_now)
            datas["count"] = fetch_user_count(cur,contact_target_id)

            content_template = "main_content/contact.jinja"
        
        
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

        datas=datas,
        state=state,
        dialog=dialog,
        result = result,
    )


@index_bp.route("/", methods=["POST"])
def index_post():

    
    action = request.form.get("action")
    print(action)

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        auth(cur, action)
        
        # ここから先は「ログイン必須アクション」
        self_id = session.get("self_id")
        if self_id is None:
            raise OperationAborted()
        
        dialog(action)        
        landing(action)
        move(cur, action,self_id)
        contact(cur,action)
        object_create(cur, action,self_id)

        conn.commit()   # ← 成功時のみ
    
    except OperationAborted:
        conn.rollback()
        return redirect("/")
    
    except AppError as e:
        conn.rollback() # ← 失敗時
        return render_template("error.jinja", error_code=e.code)

    finally:
        cur.close()
        conn.close()

    return redirect("/")


def auth(cur,action):
    if action == "login":
        handle_login(
            cur,
            request.form.get("username"),
            request.form.get("password"),
            session,
        )

    if action == "logout":
        handle_logout(session)

def dialog(action):
    if action == "redirect":
        raise OperationAborted()

def landing(action):
    if action == "enter_planet":
        session["state"] = "planet"

def move(cur,action,self_id):
    if action == "to_front":
        handle_to_front(cur,session)
    
    if action == "turn_left":
        handle_turn(cur,self_id,-1)
    
    if action == "turn_right":
        handle_turn(cur,self_id,1)

def contact(cur,action):
    if action =="kill":
        session["dialog"] = {
        "text": "殺されたアカウントは生き返りません。本当に殺しますか？",
        "options": [
            {"label": "やめる", "action": "redirect"},
            {"label": "殺す", "action": "killed"},
            ]
        }
        
    elif action =="killed":
        session["state"]="killed"
        handle_kill(cur,session["contact_target_id"])

        
def object_create(cur,action,self_id):
    if action == "post_to_tile":
        print("post_to_tile",request.form.get("post_content"))
        create_to_new_tile(
            cur,
            user_id=self_id,
            kind="post",
            content=request.form.get("post_content"),
            )    
    elif  action == "post_to_page":

        create_to_parent(
            cur,
            user_id=self_id,
            kind="post",
            content=request.form.get("post_content"),
            parent_id = int(request.form.get("parent_id"))
            )        
    elif  action == "page_to_tile":
        create_to_tile_with_children(
            cur,
            user_id=self_id,
            kind="page",
            content=request.form.get("page_content"),
            )
    elif  action == "page_to_book":
        create_to_parent(
            cur,
            user_id=self_id,
            kind="page",
            content=request.form.get("page_content"),
            parent_id = int(request.form.get("parent_id"))
            )
    elif  action == "book_to_tile":
        create_to_tile_with_children(
            cur,
            user_id=self_id,
            kind="book",
            content=request.form.get("book_content"),
            )
    elif  action == "book_to_shelf":
        create_to_tile_with_children(
            cur,
            user_id=self_id,
            kind="book",
            content=request.form.get("book_content"),
            parent_id = int(request.form.get("parent_id"))
            )
    elif  action == "shelf_to_tile":
        create_to_tile_with_children(
            cur,
            user_id=self_id,
            kind="shelf",
            content=request.form.get("shelf_content"),
            )
