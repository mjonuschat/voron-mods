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


def test_max_cs_correction_reduces_purge():
    # Same invocation as before: correction clamps purge to
    # 0.98 * 0.64 * 146.165 / 2.40528 = 38.11 mm of filament, and with the
    # relaxed 0.75 threshold the corrected line (h/w = 0.574) now prints.
    printer = default_printer(max_cross_section="0.64")
    gcode, msgs = render(
        {"PURGE_LENGTH": 50, "LINE_HEIGHT": 0.6, "PERIOD_LENGTH": 10, "PERIODS": 10},
        printer,
    )
    assert math.isclose(total_e(gcode), 38.11, abs_tol=0.01)
    assert any("Corrected the prime_line_purge_distance" in m for m in msgs)


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


def test_ratio_up_to_0_75_allowed():
    # 30 mm purge at h=0.4 over 20x5 periods: width 0.784 mm, h/w = 0.510.
    # Aborted under the old 0.5 rule; a perfectly good thin line under 0.75.
    gcode, _ = render(
        {"PURGE_LENGTH": 30, "LINE_HEIGHT": 0.4, "PERIOD_LENGTH": 5, "PERIODS": 20}
    )
    assert math.isclose(total_e(gcode), 30.0, abs_tol=1e-6)


def test_ratio_above_0_75_aborts_with_actionable_message():
    # width = 36.08 / (0.6 * 230.14) = 0.261 mm -> h/w = 2.3
    with pytest.raises(RaiseError, match="Decrease LINE_HEIGHT"):
        render({"PURGE_LENGTH": 15, "LINE_HEIGHT": 0.6, "PERIOD_LENGTH": 5, "PERIODS": 20})


def test_max_cs_clamped_abort_names_the_real_culprit():
    # h=0.7 at max_cs=0.64: correction clamps width to 0.98*0.64/0.7 = 0.896,
    # h/w = 0.781 >= 0.75. The old message said "increase purge distance" —
    # the opposite of helpful, since the correction just reduced it.
    printer = default_printer(max_cross_section="0.64")
    with pytest.raises(RaiseError, match="max_extrude_cross_section"):
        render(
            {"PURGE_LENGTH": 50, "LINE_HEIGHT": 0.7, "PERIOD_LENGTH": 10, "PERIODS": 10},
            printer,
        )


def test_squish_factor_default_leaves_gcode_unchanged():
    assert render()[0] == render({"SQUISH_FACTOR": 0.8})[0]


def test_squish_factor_changes_only_the_z_gap():
    base, _ = render()
    flat, _ = render({"SQUISH_FACTOR": 1.0})
    assert extrusion_moves(base) == extrusion_moves(flat)  # legacy math untouched
    assert z_gap(base) == pytest.approx(0.48)
    assert z_gap(flat) == pytest.approx(0.6)


def test_squish_factor_out_of_range_aborts():
    for bad in (0, -0.5, 1.2):
        with pytest.raises(RaiseError, match="SQUISH_FACTOR"):
            render({"SQUISH_FACTOR": bad})
