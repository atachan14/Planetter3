import random

#helper
DIRECTION_TO_DELTA = {
    0: (0, -1),
    1: (1, 0),
    2: (0, 1),
    3: (-1, 0),
}
def rotate(direction, turn):
    return (direction + turn) % 4

#landing
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