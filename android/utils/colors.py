"""Color palette for auto-assigning piece colors."""

_PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#d37295", "#fabfd2", "#8cd17d", "#b6992d", "#499894",
    "#86bcb6", "#e49444", "#d4a6c8", "#9d7660", "#bcbd22",
]


def get_color(index: int) -> str:
    return _PALETTE[index % len(_PALETTE)]
