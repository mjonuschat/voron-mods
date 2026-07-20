# Squiggly Purge

A Klipper macro that draws a sinusoidal purge/prime line before prints to prepare the nozzle. Includes a printable bucket to catch purge material.

## Installation

1. Copy `Macro/squiggly_purge.cfg` to your Klipper config directory
2. Add `[include squiggly_purge.cfg]` to your `printer.cfg`
3. Call `SQUIGGLY_PURGE` in your slicer's start G-code

## Parameters

### Commonly adjusted

| Parameter | Default | Description |
|---|---|---|
| `PURGE_LENGTH` | 100.0 | Total filament length to extrude (mm) |
| `PERIODS` | 10 | Number of full sine wave cycles (an upper bound when `LINE_WIDTH` is set) |
| `LINE_HEIGHT` | 0.6 | Layer height of the purge line (mm) |
| `LINE_WIDTH` | - | Target line width (mm). When set, the macro computes the number of periods itself |
| `LINE_DIRECTION` | X | Primary travel axis: `X` or `Y` |
| `START_X` | 5.0 | Starting X position (mm) |
| `START_Y` | 3.5 | Starting Y position (mm) |

### Occasionally adjusted

| Parameter | Default | Description |
|---|---|---|
| `FLOWRATE` | 10.0 | Volumetric flow rate (mm³/s) |
| `AMPLITUDE` | 5.0 | Peak-to-peak width of the sine wave (mm) |
| `PERIOD_LENGTH` | 5.0 | Length of one sine cycle along the travel direction (mm) |
| `LINE_MARGIN` | 10.0 | Clearance from print area in adaptive mode (mm) |
| `SQUISH_FACTOR` | 0.8 | Fraction of `LINE_HEIGHT` used as the actual nozzle gap, pressing the line into the bed |

### Rarely changed

| Parameter | Default | Description |
|---|---|---|
| `STEPS` | 16 | Samples per sine period. Higher = smoother curve |
| `UNRETRACT_LENGTH` | 5.0 | Filament to push before starting the line (mm) |
| `ADAPTIVE_MODE` | 1 | Position purge line relative to the print area |
| `SIZE` | - | Print area bounding box (`xMin_yMin_xMax_yMax`), typically passed by the slicer |
| `VERBOSE` | 1 | Enable status messages |

### Example

```
SQUIGGLY_PURGE PURGE_LENGTH=80 PERIODS=8
```

This draws a shorter purge line with 8 sine wave cycles instead of the default 10, extruding 80mm of filament over a 40mm path (8 periods x 5mm period length). Useful when less priming is needed or when bed space is limited.

## Line Sizing

The line width follows from `width = purge volume / (line height x path length)`, purging more filament over the same path makes a wider line.

Without `LINE_WIDTH`, the path is fixed (`PERIODS` x `PERIOD_LENGTH`) and the width is whatever the purge volume dictates. The macro aborts if height/width reaches 0.75 (the line would be too tall and narrow to stick).

With `LINE_WIDTH`, the macro solves the same equation the other way: it computes how many periods are needed to lay the requested purge volume down at the requested width and uses that. `PERIODS` then acts as an upper bound, and the line never grows past the edge of the bed. When either cap limits the path, the width is honored and the purge volume is reduced instead (a console warning reports the reduction).

```
SQUIGGLY_PURGE LINE_WIDTH=0.8 LINE_HEIGHT=0.3 PURGE_LENGTH=15
```

This draws a 0.8 mm wide, 0.3 mm high line and picks the period count itself (17 periods with the default 5 mm period length). In this mode the volume math uses the actual nozzle gap (`LINE_HEIGHT` x `SQUISH_FACTOR`), so the printed bead matches the requested width.

## Adaptive Mode

When `ADAPTIVE_MODE=1`, the macro positions the purge line near the print area using either:

1. The `SIZE` parameter (passed by the slicer as `xMin_yMin_xMax_yMax`)
2. Klipper's `[exclude_object]` polygon data

The line is mirrored across the bed center when the print area is on the opposite side, and clamped to stay within bed boundaries.
