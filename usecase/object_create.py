from DAO.fetchs import fetch_latest_user_data,fetch_db_now
from DAO.create_object import create_object,attach_object_to_new_tile,attach_object_to_parent,attach_object_to_tile_with_children



def create_to_new_tile(ctx,*,kind,content):
    user_id = ctx.self_id
    db_now = ctx.db_now
    cur = ctx.cur
    user_data=fetch_latest_user_data(cur,user_id,db_now)

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
    
def create_to_parent(ctx,*,kind: str,content: str,parent_id: int):

    user_id = ctx.self_id
    db_now = ctx.db_now
    cur = ctx.cur
    
    user_data=fetch_latest_user_data(cur,user_id,db_now)

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

def create_to_tile_with_children(ctx,*,kind,content):
    user_id = ctx.self_id
    db_now = ctx.db_now
    cur = ctx.cur
    
    user = fetch_latest_user_data(cur, user_id, db_now)

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



