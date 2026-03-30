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
| `PERIODS` | 10 | Number of full sine wave cycles |
| `LINE_HEIGHT` | 0.6 | Layer height of the purge line (mm) |
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

## Adaptive Mode

When `ADAPTIVE_MODE=1`, the macro positions the purge line near the print area using either:

1. The `SIZE` parameter (passed by the slicer as `xMin_yMin_xMax_yMax`)
2. Klipper's `[exclude_object]` polygon data

The line is mirrored across the bed center when the print area is on the opposite side, and clamped to stay within bed boundaries.
