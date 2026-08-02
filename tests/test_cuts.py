"""Tests for guillotine cut sequencing."""

from pathlib import Path

from zuschnitt.core.cuts import compute_cuts
from zuschnitt.core.optimizer_2d import optimize_2d
from zuschnitt.core.project import load
from zuschnitt.core.models import Piece2D, PlacedPiece2D, SheetLayout, StockSheet


def _placed(width: float, height: float, x: float, y: float) -> PlacedPiece2D:
    return PlacedPiece2D(piece=Piece2D(width=width, height=height), x=x, y=y)


def test_cut_sequence_detaches_smallest_piece_first():
    layout = SheetLayout(
        stock=StockSheet(width=600, height=1000),
        placements=[
            _placed(300, 400, 0, 0),
            _placed(300, 400, 300, 0),
            _placed(600, 400, 0, 400),
            _placed(300, 200, 0, 800),
            _placed(300, 200, 300, 800),
        ],
    )

    cuts = compute_cuts(layout)

    assert [(cut.orientation, cut.position) for cut in cuts[:3]] == [
        ("H", 800),
        ("V", 300),
        ("H", 400),
    ]


def test_kerf_pair_counts_reference_side_only():
    layout = SheetLayout(
        stock=StockSheet(width=1000, height=500),
        placements=[
            _placed(490, 500, 0, 0),
            _placed(500, 500, 500, 0),
        ],
    )

    cuts = compute_cuts(layout, kerf=10)

    assert [(cut.orientation, cut.position) for cut in cuts] == [("V", 490)]


def test_example_project_cut_count_is_not_duplicated():
    project = load(Path("example.zusc"))
    layouts, unplaced = optimize_2d(
        project.sheets,
        project.pieces_2d,
        kerf=project.settings.kerf,
        allow_rotation=project.settings.allow_rotation,
    )

    assert unplaced == []
    cuts = compute_cuts(layouts[0], kerf=project.settings.kerf)

    assert (cuts[0].orientation, cuts[0].position) == ("V", 713.4)
    assert len(cuts) >= 5
