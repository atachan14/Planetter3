from models.data import Planet
import random


def land_on_planet(cur, self_id, planet_id):
    cur.execute(
        "SELECT width, height FROM planets WHERE id = %s",
        (planet_id,)
    )
    row = cur.fetchone()
    width = int(row["width"])
    height = int(row["height"])

    x = random.randrange(width)
    y = random.randrange(height)
    direction = random.randrange(4)

    cur.execute(
        """
        UPDATE users
        SET planet_id = %s,
            x = %s,
            y = %s,
            direction = %s
        WHERE id = %s
        """,
        (planet_id, x, y, direction, self_id)
    )


SURROUND_BASE = {
    7: (-1, -1),
    8: (0, -1),
    9: (1, -1),
    4: (-1,  0),
    5: (0, 0),
    6: (1,  0),
}
DIRECTION_TO_DELTA = {
    0: (0, -1),   # 上
    1: (1, 0),    # 右
    2: (0, 1),    # 下
    3: (-1, 0),   # 左
}


def rotate_direction(direction: int, turn: int) -> int:
    return (direction + turn) % 4


def rotate_delta(dx: int, dy: int, direction: int) -> tuple[int, int]:
    if direction == 0:      # 上
        return dx, dy
    elif direction == 1:    # 右
        return -dy, dx
    elif direction == 2:    # 下
        return -dx, -dy
    elif direction == 3:    # 左
        return dy, -dx
    return dx, dy


def wrap_coord(x: int, y: int, planet: Planet) -> tuple[int, int]:
    return x % planet.width, y % planet.height
