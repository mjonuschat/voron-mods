import math

import pytest

from harness import (
    RaiseError,
    default_printer,
    extrusion_moves,
    path_length,
    render,
    total_e,
    z_gap,
)

# Reference values, derived from the macro's own math with default params:
# filament area = 3.14159 * 0.875^2 = 2.405280 mm^2
# discrete path length: 11.50685 mm per period (AMPLITUDE=5, PERIOD_LENGTH=5, STEPS=16)


def test_default_invocation_geometry():
    gcode, _ = render()
    moves = extrusion_moves(gcode)
    assert len(moves) == 160  # PERIODS=10 x STEPS=16
    assert math.isclose(total_e(gcode), 100.0, abs_tol=1e-6)
    assert math.isclose(path_length(gcode), 115.068, abs_tol=0.01)
    # width = 240.528 / (0.6 * 115.068) = 3.4839 -> F = 10/(0.6*3.4839)*60
    assert math.isclose(moves[0][3], 286.99, abs_tol=0.5)


def test_default_invocation_squish_z():
    gcode, _ = render()
    assert z_gap(gcode) == pytest.approx(0.48)  # LINE_HEIGHT 0.6 * 0.8 squish


def test_start_position_and_direction():
    gcode, _ = render()
    assert "G0 X5.0 Y3.5 F18000" in gcode
    moves = extrusion_moves(gcode)
    assert all(x > 0 for x, _, _, _ in moves)  # +X travel from the default corner


def test_max_cs_correction_then_ratio_abort():
    # 50 mm purge at h=0.6 over 10x10 mm periods: cross-section 0.823 mm^2
    # exceeds Klipper's default 0.64, the correction clamps width to
    # 0.98*0.64/0.6 = 1.045 mm, then h/w = 0.574 >= 0.5 aborts.
    printer = default_printer(max_cross_section="0.64")
    with pytest.raises(RaiseError, match="too thin"):
        render(
            {"PURGE_LENGTH": 50, "LINE_HEIGHT": 0.6, "PERIOD_LENGTH": 10, "PERIODS": 10},
            printer,
        )


def test_wide_flat_line_passes_ratio_check():
    gcode, _ = render(
        {"PURGE_LENGTH": 50, "LINE_HEIGHT": 0.6, "PERIOD_LENGTH": 10, "PERIODS": 10}
    )
    assert math.isclose(total_e(gcode), 50.0, abs_tol=1e-6)
    assert math.isclose(path_length(gcode), 146.165, abs_tol=0.01)


def test_missing_max_cs_falls_back_to_klipper_default():
    printer = default_printer(max_cross_section=None)
    gcode, msgs = render({"PURGE_LENGTH": 20, "LINE_HEIGHT": 0.3}, printer)
    assert any("falling back to the Klipper default" in m for m in msgs)


def test_steps_periods_validation():
    with pytest.raises(RaiseError, match="STEPS and PERIODS"):
        render({"STEPS": 0})
