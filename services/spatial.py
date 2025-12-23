from models.data import Planet
def rotate(dx: int, dy: int, direction: int) -> tuple[int, int]:
    if direction == 0:      # 上
        return dx, dy
    elif direction == 1:    # 右
        return -dy, dx
    elif direction == 2:    # 下
        return -dx, -dy
    elif direction == 3:    # 左
        return dy, -dx
    return dx, dy


SURROUND_BASE = {
    7: (-1, -1),
    8: (0, -1),
    9: (1, -1),
    4: (-1,  0),
    5: (0, 0),
    6: (1,  0),
}
def wrap_coord(x: int, y: int, planet: Planet) -> tuple[int, int]:
    return x % planet.width, y % planet.height