"""Layout helpers for non-overlapping cut number markers."""

from __future__ import annotations

from dataclasses import dataclass

from zuschnitt.core.cuts import CutLine


@dataclass(frozen=True)
class CutMarkerPlacement:
    cut: CutLine
    anchor_x: float
    anchor_y: float
    label_x: float
    label_y: float


def _spread_positions(desired: list[float], min_sep: float) -> list[float]:
    if not desired:
        return []

    clusters: list[list[float]] = [[desired[0]]]
    for pos in desired[1:]:
        if pos - clusters[-1][-1] < min_sep:
            clusters[-1].append(pos)
        else:
            clusters.append([pos])

    placed: list[float] = []
    prev_end = float("-inf")
    for cluster in clusters:
        count = len(cluster)
        center = sum(cluster) / count
        start = center - (count - 1) * min_sep / 2
        start = max(start, prev_end + min_sep)
        cluster_positions = [start + i * min_sep for i in range(count)]
        placed.extend(cluster_positions)
        prev_end = cluster_positions[-1]
    return placed


def place_horizontal_cut_markers(
    cuts: list[CutLine],
    *,
    anchor_x: float,
    label_x: float,
    min_sep: float,
) -> list[CutMarkerPlacement]:
    horizontal = sorted((cut for cut in cuts if cut.orientation == "H"), key=lambda cut: cut.position)
    y_positions = _spread_positions([cut.position for cut in horizontal], min_sep)
    return [
        CutMarkerPlacement(
            cut=cut,
            anchor_x=anchor_x,
            anchor_y=cut.position,
            label_x=label_x,
            label_y=label_y,
        )
        for cut, label_y in zip(horizontal, y_positions)
    ]


def place_vertical_cut_markers(
    cuts: list[CutLine],
    *,
    anchor_y: float,
    label_y: float,
    min_sep: float,
) -> list[CutMarkerPlacement]:
    vertical = sorted((cut for cut in cuts if cut.orientation == "V"), key=lambda cut: cut.position)
    x_positions = _spread_positions([cut.position for cut in vertical], min_sep)
    return [
        CutMarkerPlacement(
            cut=cut,
            anchor_x=cut.position,
            anchor_y=anchor_y,
            label_x=label_x,
            label_y=label_y,
        )
        for cut, label_x in zip(vertical, x_positions)
    ]
