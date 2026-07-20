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
# discrete path length: 115.068 mm total over 10 default periods (per-period arc
# drifts 11.4787-11.5725 mm; see the solver-mode reference notes further down)


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
    with pytest.raises(RaiseError, match="Decrease LINE_HEIGHT") as excinfo:
        render({"PURGE_LENGTH": 15, "LINE_HEIGHT": 0.6, "PERIOD_LENGTH": 5, "PERIODS": 20})
    assert "max_extrude_cross_section" not in str(excinfo.value)


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


# Solver-mode reference values:
# one-period arc length = 11.478695 mm (single fresh period; the macro's
# truncated TAU + float modulo make later periods drift slightly longer,
# so the solver's estimate errs thin — width never exceeds the request)
# filament area = 2.405280 mm^2


def test_line_width_solver_picks_periods():
    # gap = 0.3*0.8 = 0.24; cs = 0.8*0.24 = 0.192 mm^2
    # required length = 15*2.40528/0.192 = 187.9 mm -> ceil(187.9/11.478695) = 17 periods
    gcode, _ = render({"LINE_WIDTH": 0.8, "LINE_HEIGHT": 0.3, "PURGE_LENGTH": 15})
    moves = extrusion_moves(gcode)
    assert len(moves) == 17 * 16
    assert math.isclose(total_e(gcode), 15.0, abs_tol=1e-6)  # full purge kept
    # ceil rounding means slightly MORE path, so actual width is <= request
    width = 15 * 2.40528 / (0.24 * path_length(gcode))
    assert 0.75 < width <= 0.8 + 1e-6


def test_line_width_periods_cap_honors_width_and_reduces_purge():
    gcode, msgs = render(
        {"LINE_WIDTH": 0.8, "LINE_HEIGHT": 0.3, "PURGE_LENGTH": 15, "PERIODS": 10}
    )
    assert len(extrusion_moves(gcode)) == 10 * 16
    # purge = 0.192 * 10 * 11.478695 / 2.40528 = 9.163 mm of filament
    assert math.isclose(total_e(gcode), 9.163, abs_tol=0.01)
    assert any("reducing purge" in m and "PERIODS" in m for m in msgs)


def test_line_width_bed_space_caps_periods():
    # 120 mm bed, start X=5 -> 115 mm of travel space -> 23 periods max;
    # the solver wants ceil(50*2.40528/0.12/11.478695) = 88.
    printer = default_printer(bed=(120.0, 120.0))
    gcode, msgs = render(
        {"LINE_WIDTH": 0.5, "LINE_HEIGHT": 0.3, "PURGE_LENGTH": 50}, printer
    )
    assert len(extrusion_moves(gcode)) == 23 * 16
    assert math.isclose(total_e(gcode), 13.172, abs_tol=0.01)
    assert any("reducing purge" in m and "bed space" in m for m in msgs)


def test_line_width_solver_reports_geometry():
    _, msgs = render({"LINE_WIDTH": 0.8, "LINE_HEIGHT": 0.3, "PURGE_LENGTH": 15})
    assert any("periods" in m and "wide bead" in m for m in msgs)


def test_line_width_validation():
    with pytest.raises(RaiseError, match="LINE_WIDTH"):
        render({"LINE_WIDTH": 0})


def test_line_width_absent_keeps_legacy_output():
    # The whole legacy suite is the real guarantee; this is a direct sentinel.
    gcode, _ = render()
    assert len(extrusion_moves(gcode)) == 160
    assert math.isclose(total_e(gcode), 100.0, abs_tol=1e-6)


def test_solver_rejects_too_narrow_width_request():
    # gap 0.24 / width 0.325 = 0.738: nominally below 0.75, but ceil rounding and
    # period drift would push the actual ratio over - rejected up front with
    # advice naming the solver knobs.
    with pytest.raises(RaiseError, match="Increase LINE_WIDTH"):
        render({"LINE_WIDTH": 0.325, "LINE_HEIGHT": 0.3})


def test_solver_clamps_width_to_max_cross_section():
    # 0.98*0.64/0.48 = 1.3067 mm max width; cs = 0.62726 mm^2
    # required length = 50*2.40528/0.62726 = 191.75 -> ceil(191.75/11.478695) = 17
    printer = default_printer(max_cross_section="0.64")
    gcode, msgs = render(
        {"LINE_WIDTH": 3.5, "LINE_HEIGHT": 0.6, "PURGE_LENGTH": 50}, printer
    )
    assert len(extrusion_moves(gcode)) == 17 * 16
    assert math.isclose(total_e(gcode), 50.0, abs_tol=1e-6)  # full purge preserved
    assert any("clamping the width" in m for m in msgs)
    width = 50 * 2.40528 / (0.48 * path_length(gcode))
    assert width <= 1.3067 + 1e-6
