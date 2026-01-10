from services.action.move import handle_to_front, handle_turn, handle_kill
from services.action.object_create import (
    create_to_new_tile,
    create_to_parent,
    create_to_tile_with_children,
)
from services.action.auth import handle_login, handle_logout
from services.data import (
    fetch_db_now,
    fetch_latest_user_data,
    fetch_user_count,
    fetch_planet_data,
    fetch_surround_data,
    fetch_galaxy_data,
)
from models.data import ActionContext
from db import get_db
from flask import Blueprint, render_template, request, redirect, session, flash
from psycopg2.extras import RealDictCursor
from errors import AppError, InvalidStateError, OperationAborted,StardustNotEnough
import logging

logger = logging.getLogger(__name__)


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
        db_now = fetch_db_now(cur)
        self_data = fetch_latest_user_data(cur, self_id, db_now)
        planet_data = fetch_planet_data(cur, self_data.planet_id, db_now)

    # デフォルト
        datas = {}
        pops = session.pop("pops", {})
        here_state = session.get("here_state",{})
        print(pops)
        print(here_state)

        if state == "landing":
            content_template = "main_content/landing.jinja"

        elif state == "planet":
            datas["surround"] = fetch_surround_data(
                cur, self_data, planet_data)
            content_template = "main_content/planet.jinja"

        elif state == "galaxy":
            datas["galaxy"] = fetch_galaxy_data(cur, self_id)
            content_template = "main_content/galaxy.jinja"

        elif state in ("contact", "killed"):
            contact_target_id = session.get("contact_target_id")
            if not contact_target_id:
                logger.warning("contact state without contact_target_id")
                raise InvalidStateError("contact without target")

            datas["target"] = fetch_latest_user_data(
                cur, contact_target_id, db_now)
            datas["count"] = fetch_user_count(cur, contact_target_id)

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
        
        state=state,
        datas=datas,
        pops=pops,
        here_state=here_state,
    )


@index_bp.route("/", methods=["POST"])
def index_post():
    action = request.form.get("action")

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    db_now = fetch_db_now(cur)
    self_id = session.get("self_id")

    ctx = ActionContext(
        cur=cur,
        session=session,
        db_now=db_now,
        self_id=self_id,
    )

    try:
        if action in TOP_ACTIONS:
            TOP_ACTIONS[action](ctx)

        elif action in MAIN_ACTIONS:
            if self_id is None:
                raise OperationAborted()
            MAIN_ACTIONS[action](ctx)

        else:
            raise OperationAborted()

        conn.commit()

    except OperationAborted:
        conn.rollback()
        return redirect("/")

    except AppError as e:
        conn.rollback()
        return render_template("error.jinja", error_code=e.code)

    except StardustNotEnough as e:
        conn.rollback()
        pops = session.get("pops", {})
        session["pops"] = pops
        pops["dialog"] = {
            "text": "星屑が足りない。",
            "options": [
                {"label": "戻る", "action": "redirect"},
            ],
        }
        return redirect("/")

    finally:
        cur.close()
        conn.close()

    return redirect("/")


# top_action
def action_login(ctx: ActionContext):
    handle_login(
        ctx.cur,
        request.form.get("username"),
        request.form.get("password"),
        ctx.session,
    )


def action_logout(ctx: ActionContext):
    handle_logout(ctx.session)


def action_redirect(ctx: ActionContext):
    raise OperationAborted()


def action_enter_planet(ctx: ActionContext):
    ctx.session["state"] = "planet"


# main_action
def action_to_front(ctx: ActionContext):
    handle_to_front(ctx)


def action_turn_left(ctx: ActionContext):
    handle_turn(ctx, -1)


def action_turn_right(ctx: ActionContext):
    handle_turn(ctx, 1)


def action_kill(ctx: ActionContext):
    pops = ctx.session.get("pops", {})
    pops["dialog"] = {
        "text": "殺されたアカウントは生き返りません。本当に殺しますか？",
        "options": [
            {"label": "やめる", "action": "redirect"},
            {"label": "殺す", "action": "killed"},
        ],
    }
    session["pops"] = pops


def action_killed(ctx: ActionContext):
    handle_kill(ctx)


def action_post_to_tile(ctx: ActionContext):
    create_to_new_tile(
        ctx,
        kind="post",
        content=request.form.get("post_content"),
    )


def action_post_to_page(ctx: ActionContext):
    create_to_parent(
        ctx,
        kind="post",
        content=request.form.get("post_content"),
        parent_id=int(request.form.get("parent_id")),
    )


def action_page_to_tile(ctx: ActionContext):
    create_to_tile_with_children(
        ctx,
        kind="page",
        content=request.form.get("page_content"),
    )


def action_page_to_book(ctx: ActionContext):
    create_to_parent(
        ctx,
        kind="page",
        content=request.form.get("page_content"),
        parent_id=int(request.form.get("parent_id")),
    )


def action_book_to_tile(ctx: ActionContext):
    create_to_tile_with_children(
        ctx,
        kind="book",
        content=request.form.get("book_content"),
    )


def action_book_to_shelf(ctx: ActionContext):
    create_to_tile_with_children(
        ctx,
        kind="book",
        content=request.form.get("book_content"),
        parent_id=int(request.form.get("parent_id")),
    )


def action_shelf_to_tile(ctx: ActionContext):
    create_to_tile_with_children(
        ctx,
        kind="shelf",
        content=request.form.get("shelf_content"),
    )

def action_page_select(ctx):
    here_state = ctx.session.setdefault("here_state", {})
    here_state["current_page"] = int(request.form["current_page"])
    ctx.session.modified = True


TOP_ACTIONS = {
    "login": action_login,
    "logout": action_logout,
    "redirect": action_redirect,
    "enter_planet": action_enter_planet,
}

MAIN_ACTIONS = {

    # move
    "to_front": action_to_front,
    "turn_left": action_turn_left,
    "turn_right": action_turn_right,

    # contact
    "kill": action_kill,
    "killed": action_killed,

    # object create
    "post_to_tile": action_post_to_tile,
    "post_to_page": action_post_to_page,
    "page_to_tile": action_page_to_tile,
    "page_to_book": action_page_to_book,
    "book_to_tile": action_book_to_tile,
    "book_to_shelf": action_book_to_shelf,
    "shelf_to_tile": action_shelf_to_tile,

    # object_index_select
    "page_select": action_page_select,
}

