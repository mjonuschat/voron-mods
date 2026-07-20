"""Render squiggly_purge.cfg offline the way Klipper would.

Klipper compiles gcode_macro templates with
jinja2.Environment("{%", "%}", "{", "}") — block tags are normal but output
expressions use single braces. The printer object supports both attribute
and item access; config values arrive as strings.
"""
import pathlib
import re

import jinja2

MACRO_PATH = pathlib.Path(__file__).resolve().parent.parent / "Macro" / "squiggly_purge.cfg"


class RaiseError(Exception):
    """Raised when the macro calls action_raise_error."""


class NS(dict):
    """Dict with attribute access, mirroring Klipper's printer object views."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


def default_printer(max_cross_section="5.0", bed=(300.0, 300.0), z=10.0):
    extruder = {"filament_diameter": "1.75", "nozzle_diameter": "0.4"}
    if max_cross_section is not None:
        extruder["max_extrude_cross_section"] = max_cross_section
    return NS({
        "toolhead": NS({
            "axis_maximum": NS({"x": bed[0], "y": bed[1]}),
            "position": NS({"z": z}),
        }),
        "configfile": NS({"config": {"extruder": extruder}}),
    })


def render(params=None, printer=None):
    body = MACRO_PATH.read_text().split("gcode:\n", 1)[1]
    env = jinja2.Environment("{%", "%}", "{", "}")
    messages = []

    def action_respond_info(msg):
        messages.append(msg)
        return ""

    def action_raise_error(msg):
        raise RaiseError(msg)

    gcode = env.from_string(body).render(
        params={k.upper(): str(v) for k, v in (params or {}).items()},
        printer=printer if printer is not None else default_printer(),
        action_respond_info=action_respond_info,
        action_raise_error=action_raise_error,
        action_respond_error=action_raise_error,
    )
    return gcode, messages


_MOVE_RE = re.compile(
    r"^\s*G1 X(?P<x>[-\d.e+]+) Y(?P<y>[-\d.e+]+) E(?P<e>[-\d.e+]+) F(?P<f>[-\d.e+]+)",
    re.M,
)


def extrusion_moves(gcode):
    return [
        (float(m["x"]), float(m["y"]), float(m["e"]), float(m["f"]))
        for m in _MOVE_RE.finditer(gcode)
    ]


def total_e(gcode):
    return sum(e for _, _, e, _ in extrusion_moves(gcode))


def path_length(gcode):
    return sum((x * x + y * y) ** 0.5 for x, y, _, _ in extrusion_moves(gcode))


def z_gap(gcode):
    """The squish Z move. Of all `G1 Z<v> F600` moves (initial raise to 5,
    squish, final 3 mm hop) the squish gap is always the smallest value."""
    return min(float(z) for z in re.findall(r"G1 Z([-\d.e+]+) F600", gcode))
