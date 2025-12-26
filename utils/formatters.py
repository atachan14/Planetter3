def format_stardust(value: int) -> str:
    units = [
        (10**12, "t"),
        (10**9,  "b"),
        (10**6,  "m"),
        (10**3,  "k"),
    ]

    for base, suffix in units:
        if value >= base:
            return f"{value / base:.1f}{suffix}"

    return str(value)