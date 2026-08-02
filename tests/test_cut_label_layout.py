"""Tests for cut label marker layout."""

from zuschnitt.core.cuts import CutLine
from zuschnitt.visualization.cut_label_layout import (
    place_horizontal_cut_markers,
    place_vertical_cut_markers,
)


def test_horizontal_markers_spread_close_cut_numbers():
    cuts = [
        CutLine(number=1, orientation="H", position=511.0),
        CutLine(number=2, orientation="H", position=514.4),
        CutLine(number=3, orientation="H", position=746.4),
    ]

    placements = place_horizontal_cut_markers(
        cuts,
        anchor_x=1000.0,
        label_x=1020.0,
        min_sep=20.0,
    )

    assert placements[1].label_y - placements[0].label_y >= 20.0
    assert placements[2].label_y == cuts[2].position


def test_vertical_markers_spread_close_cut_numbers():
    cuts = [
        CutLine(number=1, orientation="V", position=150.0),
        CutLine(number=2, orientation="V", position=153.4),
        CutLine(number=3, orientation="V", position=548.0),
    ]

    placements = place_vertical_cut_markers(
        cuts,
        anchor_y=1250.0,
        label_y=1270.0,
        min_sep=22.0,
    )

    assert placements[1].label_x - placements[0].label_x >= 22.0
    assert placements[2].label_x == cuts[2].position
    assert placements[0].anchor_x == cuts[0].position
    assert placements[1].anchor_x == cuts[1].position
