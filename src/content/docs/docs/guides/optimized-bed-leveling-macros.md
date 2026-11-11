---
title: "Optimized Bed Leveling Macros"
description: "How to use a dual pass leveling approach for Z_TILT_ADJUST or QUAD_GANTRY_LEVEL"
---

## Introduction

These macros level the bed in two passes, one with a large Z-Hop and one with a small Z-Hop. The large hop keeps the nozzle from scratching the print surface, and the small hop saves time.

**Pass 1, initial coarse leveling**

- Uses a large Z-Hop value so the nozzle does not scratch the print surface
- Takes as few probe samples as possible to find the bed position quickly
- Relaxes the tolerance, which still levels the bed to within 1mm

**Pass 2, fine leveling and accuracy**

- Uses the normal settings for accuracy and retries
- Uses a smaller Z-Hop, because the bed is already approximately level

Together the two passes level the bed safely and quickly without losing accuracy.

:::danger[Compatibility]
These macros do not work with dockable probes, because they override the default bed leveling command. Using them with a dockable probe may cause errors or unexpected behavior.
:::

## QUAD_GANTRY_LEVEL (Voron 2.4)

This macro renames the existing QUAD_GANTRY_LEVEL command and wraps it in the two-pass process. Because it replaces the default command, you do not need to change anything else in your configuration. It runs two steps:

1. Level coarsely, lifting the head to 10mm
1. Level finely, lifting the head to 2mm

```ini title="printer.cfg"
[gcode_macro QUAD_GANTRY_LEVEL]
rename_existing: BASE_QUAD_GANTRY_LEVEL
gcode:
    # Pass 1: Initial Coarse Leveling
    BASE_QUAD_GANTRY_LEVEL HORIZONTAL_MOVE_Z=10 RETRY_TOLERANCE=1
    # Pass 2: Fine Leveling and Accuracy
    BASE_QUAD_GANTRY_LEVEL HORIZONTAL_MOVE_Z=2
```

## Z_TILT_ADJUST (Voron Trident)

This macro renames the existing Z_TILT_ADJUST command and wraps it in the two-pass process. Because it replaces the default command, you do not need to change anything else in your configuration. It runs two steps:

1. Level coarsely, moving the bed down by 10mm
1. Level finely, moving the bed down by 2mm

```ini title="printer.cfg"
[gcode_macro Z_TILT_ADJUST]
rename_existing: BASE_Z_TILT_ADJUST
gcode:
    # Pass 1: Initial Coarse Leveling
    BASE_Z_TILT_ADJUST HORIZONTAL_MOVE_Z=10 RETRY_TOLERANCE=1
    # Pass 2: Fine Leveling and Accuracy
    BASE_Z_TILT_ADJUST HORIZONTAL_MOVE_Z=2
```

:::note
Printers with lead screws tend to have less bed and gantry sagging, so the two-pass approach helps less on them.
:::

## Optional tuning parameters

You can adjust these parameters in the macros to tune the leveling process further:

- **HORIZONTAL_MOVE_Z**: The height (in mm) the toolhead or bed moves between probe points
- **RETRY_TOLERANCE**: The largest allowed difference between the highest and lowest probed points. Leveling retries if the difference is larger
- **SAMPLES**: The number of probe samples taken per leveling point
