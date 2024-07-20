---
title: "Automating Z Offset Adjustments"
description: "Perfect First Layers: Automating Z Offset Adjustments"
summary: ""
date: 2024-07-20T02:10:01Z
lastmod: 2024-07-20T02:10:01Z
draft: false
weight: 810
toc: true
seo:
  title: "" # custom title (optional)
  description: "" # custom description (recommended)
  canonical: "" # custom canonical URL (optional)
  noindex: false # false (default) or true
---

## Introduction

Printing with diverse filament materials often necessitates Z offset adjustments for optimal bed adhesion and first layer squish. Manually executing these adjustments for each print job be inefficient and errors prone. This guide provides a comprehensive solution, detailing how to configure your Slicer to automatically incorporate necessary Z offset adjustments for each print job. Additionally, we will cover the modification of the `PRINT_END` macro to ensure the Z offset is reset to its default value upon print job completion, streamlining your printing process.

## Prerequisites

To utilize this guide, ensure you have the following:

- A 3D printer configured with Klipper firmware
- A compatible Slicer software that supports filament-specific start G-code, such as:
  - PrusaSlicer
  - SuperSlicer
  - OrcaSlicer
- Enable "Advanced" settings in your Slicer software to access the necessary configuration options.

## Modifying the PRINT_END Macro

The printer.cfg file should already contain a `PRINT_END` macro definition, as this is a standard configuration in Voron setups. If you require a template, refer to the callout section below. To modify the `PRINT_END` macro, append the following command to its end. If your macro utilizes the `SAVE_GCODE_STATE` and `RESTORE_GCODE_STATE` commands, ensure that the added command follows the `RESTORE_GCODE_STATE` command. This is crucial because `RESTORE_GCODE_STATE` also restores the saved G-code offset, which could result in incremental changes to the offset between print jobs, rather than resetting to the baseline offset.

```ini {title="printer.cfg"}
    SET_GCODE_OFFSET Z=0
```

The `SET_GCODE_OFFSET` command effectively resets the positional offset on the Z-axis to zero, thereby ensuring that all subsequent G-Code commands will execute without any Z-axis offsets. This resets the baseline for Z-axis positioning, allowing subsequent print jobs to adjust from known starting point.

{{< callout context="tip" title="No PRINT_END macro?" icon="outline/rocket" >}}
The `PRINT_END` macro should be part of your `printer.cfg` as it is an integral part of the stock Voron Klipper configuration. Check the code snippet below in case you don't have one defined yet.

{{< details "Macro: PRINT_END" >}}

```ini {title="printer.cfg"}
[gcode_macro PRINT_END]
gcode:
    # safe anti-stringing move coords
    {% set th = printer.toolhead %}
    {% set x_safe = th.position.x + 20 * (1 if th.axis_maximum.x - th.position.x > 20 else -1) %}
    {% set y_safe = th.position.y + 20 * (1 if th.axis_maximum.y - th.position.y > 20 else -1) %}
    {% set z_safe = [th.position.z + 2, th.axis_maximum.z]|min %}

    SAVE_GCODE_STATE NAME=STATE_PRINT_END

    M400                           ; wait for buffer to clear
    G92 E0                         ; zero the extruder
    G1 E-5.0 F1800                 ; retract filament

    TURN_OFF_HEATERS

    G90                                      ; absolute positioning
    G0 X{x_safe} Y{y_safe} Z{z_safe} F20000  ; move nozzle to remove stringing
    G0 X{th.axis_maximum.x//2} Y{th.axis_maximum.y - 2} F3600  ; park nozzle at rear
    M107                                     ; turn off fan

    BED_MESH_CLEAR

    # The purpose of the SAVE_GCODE_STATE/RESTORE_GCODE_STATE
    # command pair is to restore the printer's coordinate system
    # and speed settings since the commands above change them.
    # However, to prevent any accidental, unintentional toolhead
    # moves when restoring the state, explicitly set MOVE=0.
    RESTORE_GCODE_STATE NAME=STATE_PRINT_END MOVE=0
```

{{< /details >}}
{{< /callout >}}

## Configuring Filament Settings in Your Slicer

This section uses PrusaSlicer as an example, but the process applies to other slicers as well.

### Step 1: Access Custom G-Code

In your Slicer, navigate to Filament Settings and select the Custom G-code entry (highlighted in blue in the screenshot below).

### Step 2: Add Start G-Code

```gcode {title="Start G-Code"}
SET_GCODE_OFFSET Z_ADJUST=0.3
```

![PrusSlicer Filament Settings](images/guides/automatic-z-offset-ajustments/prusaslicer-filament-settings.png)

Note that the `SET_GCODE_OFFSET` command is utilized again, this time with the `Z_ADJUST` parameter, differing from the `Z` parameter used in the `PRINT_END` macro. The key distinction between these parameters is that `Z` sets the positional offset to the specified value, whereas `Z_ADJUST` modifies the existing offset by adding or subtracting the given value. For instance, executing `SET_GCODE_OFFSET Z=-0.2` followed by `SET_GCODE_OFFSET Z_ADJUST=0.3` results in a cumulative positional offset of **0.1** for the Z axis. This highlights the importance of resetting the offset post-print to maintain the correct Z offset.

## Verification Process

To confirm that the adjustments are being applied correctly, perform the following steps:

1. Slice and initiate a new print job.
2. Observe the Z offset adjustment during the print job preparation phase. If the configuration is correct, the WebUI displays the desired Z offset in the Toolhead card, as shown in the screenshot below:

   ![Mainsail Toolhead Z-Offset](images/guides/automatic-z-offset-ajustments/mainsail-toolhead-z-offset.png)

## Further Reading

- Klipper [SET_GCODE_OFFSET](https://www.klipper3d.org/G-Codes.html#set_gcode_offset) documentation
