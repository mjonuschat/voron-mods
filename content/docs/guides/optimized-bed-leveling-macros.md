---
title: "Optimized Bed Leveling Macros"
description: "How to use a dual pass leveling approach for Z_TILT_ADJUST or QUAD_GANTRY_LEVEL"
summary: ""
date: 2024-07-19T04:29:12Z
lastmod: 2024-07-19T04:29:12
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

These optimized macros strike a balance between safety and time efficiency by combining the benefits of large and small Z-Hop values. The leveling procedure is divided into two passes:

Pass 1: Initial Coarse Leveling

- Utilizes a large Z-Hop value to prevent scratching the print surface
- Minimizes probing samples to quickly determine bed position
- Relaxes tolerance requirements to ensure bed levelness within 1mm

Pass 2: Fine Leveling and Accuracy

- Employs normal settings for accuracy and retries
- Reduces Z-Hop distance, leveraging the knowledge that the bed is already approximately level

This two-pass approach ensures a efficient and safe leveling process, optimizing time savings while maintaining accuracy.

{{< callout context="danger" title="Important Compatibility Notice" icon="outline/alert-triangle" >}}
These macros are not compatible with dockable probes, as they override the default bed leveling functionality. Using these macros with dockable probes may result in unexpected behavior or errors.
{{< /callout >}}

## QUAD_GANTRY_LEVEL (Voron 2.4)

This macro renames and extends the existing QUAD_GANTRY_LEVEL command, implementing the two-pass leveling process. By replacing the default functionality, no additional modifications to the configuration are required. The macro executes the following steps:

Pass 1: Initial Coarse Leveling - Lifts the head to 10mm  
Pass 2: Fine Leveling - Lifts the head to 2mm  

```ini {title="printer.cfg"}
[gcode_macro QUAD_GANTRY_LEVEL]
rename_existing: BASE_QUAD_GANTRY_LEVEL
gcode:
    # Pass 1: Initial Coarse Leveling
    BASE_QUAD_GANTRY_LEVEL HORIZONTAL_MOVE_Z=10 RETRY_TOLERANCE=1
    # Pass 2: Fine Leveling and Accuracy
    BASE_QUAD_GANTRY_LEVEL HORIZONTAL_MOVE_Z=2
```

## Z_TILT_ADJUST (Voron Trident)

This macro renames and extends the existing Z_TILT_ADJUST command, implementing the two-pass leveling process. By replacing the default functionality, no additional modifications to the configuration are required. The macro executes the following steps:

Pass 1: Initial Coarse Leveling - Moves bed down by 10mm  
Pass 2: Fine Leveling - Moves bed down by 2mm  

```ini {title="printer.cfg"}
[gcode_macro Z_TILT_ADJUST]
rename_existing: BASE_Z_TILT_ADJUST
gcode:
    # Pass 1: Initial Coarse Leveling
    BASE_Z_TILT_ADJUST HORIZONTAL_MOVE_Z=10 RETRY_TOLERANCE=1
    # Pass 2: Fine Leveling and Accuracy
    BASE_Z_TILT_ADJUST HORIZONTAL_MOVE_Z=2
```

{{< callout context="note" title="Note" icon="outline/info-circle" >}}
Printers equipped with lead screws tend to exhibit reduced bed and gantry sagging, minimizing the impact of these issues. As a result, the advantages of the two-pass leveling approach is less significant.
{{< /callout >}}

## Optional Tuning Parameters

The following parameters in the macros can be adjusted to futher optimize the leveling process:

- **HORIZONTAL_MOVE_Z**: Specifies the intermediate move height (in mm) between probes
- **RETRY_TOLERANCE**: Defines the maximum allowable deviation between the largest and smallest probed points, triggering retry leveling if exceeded
- **SAMPLES**: Specifies the number of probe samples to use per leveling point
