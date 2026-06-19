# go2rtc Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new Hugo guide for installing go2rtc on a Klipper printer host, configuring a USB camera stream, running go2rtc through systemd, and adding the stream to Mainsail and Fluidd.

**Architecture:** This is a documentation-only change. Create one new Markdown page under `content/docs/guides/` that follows the existing Doks/Hugo guide style, uses Hugo callouts/details, and requires no layout or configuration changes. Validate the guide through Hugo build output and a focused Markdown review.

**Tech Stack:** Hugo, Hyas/Doks theme, Markdown, Hugo shortcodes, shell/systemd examples, go2rtc, FFmpeg, Mainsail, Fluidd.

---

## File Structure

- Create: `content/docs/guides/go2rtc-camera-streaming.md`
  - Owns the full published guide.
  - Uses the existing front matter shape from `content/docs/guides/energy-usage-monitoring.md`.
  - Contains no screenshots.
- No changes: `content/docs/guides/_index.md`
  - Existing guide pages are discovered from content files; do not edit the section index.
- No changes: `config/_default/menus/menus.en.toml`
  - The main nav already points to `/docs/guides/`.

## Task 1: Create Guide Skeleton, Introduction, Prerequisites, and Install Sections

**Files:**
- Create: `content/docs/guides/go2rtc-camera-streaming.md`

- [ ] **Step 1: Create the guide file with front matter and the opening sections**

Use `apply_patch` to add `content/docs/guides/go2rtc-camera-streaming.md` with this content:

```markdown
---
title: "Low-Latency Camera Streaming with go2rtc"
description: "How to install go2rtc for a Klipper printer camera and configure the stream in Mainsail and Fluidd"
summary: ""
date: 2026-06-19T00:00:00Z
lastmod: 2026-06-19T00:00:00Z
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

[go2rtc](https://github.com/AlexxIT/go2rtc) is a lightweight camera streaming application that can expose a printer camera through WebRTC. For printer monitoring, this can provide a lower-latency stream than a traditional MJPEG setup while still integrating cleanly with browser-based printer UIs.

This guide installs go2rtc on a Raspberry Pi OS based printer host, configures a USB camera stream named `chamber`, starts go2rtc automatically with systemd, and adds the stream to Mainsail and Fluidd.

By the end, you will have:

- A `go2rtc` binary installed at `/home/pi/go2rtc/go2rtc`
- A `go2rtc.yaml` configuration file defining a `chamber` camera stream
- A `go2rtc` systemd service that starts on boot
- A camera entry in Mainsail or Fluidd

## Prerequisites

- A printer host running Raspberry Pi OS Bookworm or Trixie
- SSH access to the printer host
- A USB camera available as a Linux video device, usually `/dev/video0`
- A recent Mainsail or Fluidd installation
- Browser access to the printer host on the same local network

{{< callout context="note" title="Camera Device Access" icon="outline/info-circle" >}}
Crowsnest, camera-streamer, ustreamer, mjpg-streamer, or another webcam service may already be using the camera device. A V4L2 USB camera can usually be opened by only one process at a time. If another service is already using `/dev/video0`, stop or reconfigure that service before testing go2rtc with the same device.
{{< /callout >}}

{{< callout context="caution" title="Supported OS Baseline" icon="outline/alert-triangle" >}}
This guide targets Raspberry Pi OS Bookworm and Trixie. Older Raspberry Pi OS releases such as Bullseye, Buster, Stretch, and Jessie are legacy baselines for this guide. If your printer host is running an older release, upgrade or re-image to Bookworm or Trixie before following these steps.
{{< /callout >}}

## Install FFmpeg

The example stream uses go2rtc's FFmpeg source to read the USB camera and produce an H.264 WebRTC-compatible stream. Install FFmpeg before configuring go2rtc.

1. Update the APT package index:

   ```bash {title="Updating package indexes"}
   sudo apt update
   ```

1. Install FFmpeg:

   ```bash {title="Installing FFmpeg"}
   sudo apt install -y ffmpeg
   ```

1. Verify that FFmpeg is available:

   ```bash {title="Checking FFmpeg"}
   ffmpeg -version
   ```

   The command should print the installed FFmpeg version and build configuration.

## Install go2rtc

Install the go2rtc binary in `/home/pi/go2rtc`. The commands below use the `go2rtc_linux_arm64` release asset, which is the correct binary for 64-bit Raspberry Pi OS.

{{< callout context="note" title="Choosing the Correct Binary" icon="outline/info-circle" >}}
Use `go2rtc_linux_arm64` for 64-bit Raspberry Pi OS and `go2rtc_linux_arm` for 32-bit Raspberry Pi OS. Other builds are available on the [go2rtc releases page](https://github.com/AlexxIT/go2rtc/releases).
{{< /callout >}}

1. Create the installation directory:

   ```bash {title="Creating the go2rtc directory"}
   mkdir -p ~/go2rtc
   cd ~/go2rtc
   ```

1. Download the latest go2rtc binary and save it as `go2rtc`:

   ```bash {title="Downloading go2rtc"}
   wget -O go2rtc https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_arm64
   ```

1. Make the binary executable:

   ```bash {title="Making go2rtc executable"}
   chmod a+x go2rtc
   ```

1. Verify the binary exists and is executable:

   ```bash {title="Checking the go2rtc binary"}
   ls -l /home/pi/go2rtc/go2rtc
   ```

   The permissions should include executable bits, such as `-rwxr-xr-x`.
```

- [ ] **Step 2: Review the new file for the intended opening structure**

Run:

```bash
sed -n '1,150p' content/docs/guides/go2rtc-camera-streaming.md
```

Expected:
- Front matter is present.
- Sections are `Introduction`, `Prerequisites`, `Install FFmpeg`, and `Install go2rtc`.
- No `ice_servers` setting appears in this section.

- [ ] **Step 3: Commit Task 1**

Run:

```bash
git add content/docs/guides/go2rtc-camera-streaming.md
git commit -m "[TASK] Add go2rtc guide install sections"
```

Expected: commit succeeds with one new guide file.

## Task 2: Add go2rtc Camera Configuration, Foreground Test, and systemd Service

**Files:**
- Modify: `content/docs/guides/go2rtc-camera-streaming.md`

- [ ] **Step 1: Append the camera configuration, test, and service sections**

Use `apply_patch` to append this content after the `Install go2rtc` section:

```markdown

## Configure a Camera Stream

Create `/home/pi/go2rtc/go2rtc.yaml` with a stream named `chamber`.

1. Open the configuration file:

   ```bash {title="Creating go2rtc.yaml"}
   nano /home/pi/go2rtc/go2rtc.yaml
   ```

1. Add the following configuration:

   ```yaml {title="go2rtc.yaml"}
   api:
     listen: ":1984"
     origin: "*"

   ffmpeg:
     bin: "ffmpeg"

   log:
     format: "color"
     level: "info"
     output: "stdout"
     time: "UNIXMS"

   rtsp:
     listen: ":8554"
     default_query: "video&audio"

   srtp:
     listen: ":8443"

   webrtc:
     listen: ":8555/tcp"

   streams:
     chamber: ffmpeg:device?video=/dev/video0&input_format=yuyv422&video_size=1280x720#video=h264#hardware
   ```

The `chamber` stream reads `/dev/video0` as a V4L2 camera, requests `yuyv422` input at `1280x720`, and asks FFmpeg/go2rtc to produce H.264 video. The `chamber` stream name is used later in go2rtc, Mainsail, and Fluidd.

The sample does not set `ice_servers`. go2rtc provides defaults for WebRTC ICE servers, and overriding them is only needed for advanced STUN, TURN, or remote-access setups.

{{< callout context="caution" title="Hardware H.264 Encoding" icon="outline/alert-triangle" >}}
The `#hardware` option depends on hardware and FFmpeg/go2rtc support. Raspberry Pi 4 lists H.264 encode support in its product brief. Raspberry Pi 5 lists HEVC decode support, but not H.264 encode. If `#hardware` causes startup errors or unusable CPU/video behavior, remove `#hardware` and retest. If your camera can already provide H.264 directly, consider using a source that can be copied with `#video=copy` instead of transcoding.
{{< /callout >}}

{{< callout context="note" title="Additional Cameras" icon="outline/info-circle" >}}
To add another camera, duplicate the `chamber:` entry under `streams:` with a new stream name and device path, such as `nozzle: ...video=/dev/video1...`. Each camera needs a supported format and resolution, and each device must not already be held by another process.
{{< /callout >}}

### Check Camera Modes

If the sample stream does not match your camera, list the camera's supported formats and resolutions:

```bash {title="Listing camera modes"}
ffmpeg -f v4l2 -list_formats all -i /dev/video0
```

Adjust `input_format` and `video_size` in `go2rtc.yaml` to match a mode reported by the camera.

## Test go2rtc

Before creating the systemd service, run go2rtc in the foreground so configuration errors are visible immediately.

1. Start go2rtc manually:

   ```bash {title="Starting go2rtc manually"}
   /home/pi/go2rtc/go2rtc -config /home/pi/go2rtc/go2rtc.yaml
   ```

1. Open the go2rtc WebUI in a browser:

   ```text {title="go2rtc WebUI"}
   http://<printer-ip>:1984
   ```

1. Select the `chamber` stream link.

The video should start after a short delay. Stop the foreground process with **CTRL-C** before continuing.

Common errors at this stage:

- `permission denied`: the binary is not executable, or the camera device permissions are wrong.
- `no such file or directory`: the binary path, config path, or camera path is wrong.
- FFmpeg format errors: `input_format` or `video_size` is not supported by the camera.
- Hardware encoder errors: remove `#hardware` from the stream line and test again.

## Start go2rtc on Boot

Create a systemd service so go2rtc starts automatically when the printer host boots.

1. Create the service file:

   ```bash {title="Creating the go2rtc service"}
   nano /home/pi/go2rtc/go2rtc.service
   ```

1. Add this unit:

   ```ini {title="go2rtc.service"}
   [Unit]
   Description=go2rtc
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/home/pi/go2rtc
   ExecStart=/home/pi/go2rtc/go2rtc -config /home/pi/go2rtc/go2rtc.yaml
   ExecReload=/bin/kill -HUP $MAINPID
   Restart=always
   RestartSec=5
   User=root
   Group=root
   Environment=PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin

   [Install]
   WantedBy=multi-user.target
   ```

   {{< callout context="note" title="Service User" icon="outline/info-circle" >}}
   This service runs as `root` to avoid inconsistent USB camera permissions on printer hosts. Advanced users can run go2rtc as a less-privileged service user if they also configure the required video-device permissions.
   {{< /callout >}}

1. Enable the service using the absolute service-file path:

   ```bash {title="Enabling go2rtc"}
   sudo systemctl enable /home/pi/go2rtc/go2rtc.service
   ```

1. Reload systemd and start go2rtc:

   ```bash {title="Starting go2rtc"}
   sudo systemctl daemon-reload
   sudo systemctl start go2rtc
   ```

1. Check the service state:

   ```bash {title="Checking go2rtc service state"}
   sudo systemctl status go2rtc
   ```

To follow service logs while troubleshooting, run:

```bash {title="Following go2rtc logs"}
journalctl -u go2rtc -f
```
```

- [ ] **Step 2: Verify the configuration sections contain required decisions**

Run:

```bash
rg -n "ice_servers|#hardware|systemctl enable|Additional Cameras|Raspberry Pi 5|journalctl" content/docs/guides/go2rtc-camera-streaming.md
```

Expected:
- The `ice_servers` result is explanatory text only, not a YAML configuration line.
- `#hardware` appears in the sample and in caveat/troubleshooting text.
- `sudo systemctl enable /home/pi/go2rtc/go2rtc.service` appears.
- `Additional Cameras` appears.

Run:

```bash
rg -n "^\\s+ice_servers:" content/docs/guides/go2rtc-camera-streaming.md
```

Expected: no output and exit code 1.

- [ ] **Step 3: Commit Task 2**

Run:

```bash
git add content/docs/guides/go2rtc-camera-streaming.md
git commit -m "[TASK] Add go2rtc stream and service setup"
```

Expected: commit succeeds with one modified guide file.

## Task 3: Add Mainsail, Fluidd, Troubleshooting, and Further Reading Sections

**Files:**
- Modify: `content/docs/guides/go2rtc-camera-streaming.md`

- [ ] **Step 1: Append frontend configuration and closing sections**

Use `apply_patch` to append this content after the `Start go2rtc on Boot` section:

```markdown

## Configure Mainsail

Mainsail can embed go2rtc's WebRTC viewer page as an HTML iframe.

1. Open Mainsail in your browser.
1. Go to **Settings > Webcams**.
1. Add a new webcam entry.
1. Configure the webcam with these values:

   - **Name**: `Chamber`
   - **Service**: `HTML Iframe`
   - **Stream URL**: `http://<printer-ip>:1984/stream.html?src=chamber&mode=webrtc`
   - **Aspect ratio**: `16:9` for the sample `1280x720` stream
   - **Rotation/flip**: Set these to match your camera orientation

The `src=chamber` parameter must match the stream name in `go2rtc.yaml`.

{{< callout context="caution" title="HTTPS and Mixed Content" icon="outline/alert-triangle" >}}
If you access Mainsail over HTTPS, the browser may block an HTTP iframe camera page as mixed content. This usually appears as a blank camera panel. HTTPS, reverse proxy, and remote-access setup are outside the scope of this guide.
{{< /callout >}}

## Configure Fluidd

Fluidd includes a native `WebRTC (go2rtc)` camera type.

1. Open Fluidd in your browser.
1. Go to **Settings > Cameras**.
1. Add a new camera.
1. Configure the camera with these values:

   - **Name**: `Chamber`
   - **Type**: `WebRTC (go2rtc)`
   - **go2rtc URL**: `http://<printer-ip>:1984`
   - **Stream name/source**: `chamber`
   - **Aspect ratio**: `16:9` for the sample `1280x720` stream
   - **Rotation/flip**: Set these to match your camera orientation

Fluidd field labels may vary by version. The required values are the go2rtc WebUI URL and the `chamber` stream name.

## Troubleshooting

### Check go2rtc Service State

Use systemd to confirm whether go2rtc is running:

```bash {title="Checking go2rtc service state"}
sudo systemctl status go2rtc
```

If the service is not active, inspect the logs:

```bash {title="Following go2rtc logs"}
journalctl -u go2rtc -f
```

### Confirm the Camera Device Path

List available video devices:

```bash {title="Listing video devices"}
ls -l /dev/video*
```

If your camera is not `/dev/video0`, update the `video=` parameter in `go2rtc.yaml`.

### Confirm the Camera Format and Resolution

List supported camera modes:

```bash {title="Listing camera modes"}
ffmpeg -f v4l2 -list_formats all -i /dev/video0
```

If the configured `input_format` or `video_size` is not listed, update the stream line to use a supported mode.

### Check for Another Process Using the Camera

Check whether another service already has the camera open:

```bash {title="Checking camera users"}
sudo fuser /dev/video0
```

If another process is listed, stop or reconfigure that service before starting go2rtc with the same device.

### Remove Hardware Encoding

If go2rtc starts but the stream fails, or FFmpeg reports hardware encoder errors, remove `#hardware` from the stream line and restart go2rtc:

```yaml {title="go2rtc.yaml"}
streams:
  chamber: ffmpeg:device?video=/dev/video0&input_format=yuyv422&video_size=1280x720#video=h264
```

Then restart the service:

```bash {title="Restarting go2rtc"}
sudo systemctl restart go2rtc
```

### Check Browser and Network Access

Open the go2rtc WebUI directly:

```text {title="go2rtc WebUI"}
http://<printer-ip>:1984
```

If the WebUI does not load, confirm the printer host IP address and check that your browser is on the same local network.

## Further Reading

- [go2rtc releases](https://github.com/AlexxIT/go2rtc/releases)
- [go2rtc README](https://github.com/AlexxIT/go2rtc)
- [go2rtc FFmpeg source documentation](https://github.com/AlexxIT/go2rtc/blob/master/internal/ffmpeg/README.md)
- [go2rtc FFmpeg hardware acceleration documentation](https://github.com/AlexxIT/go2rtc/blob/master/internal/ffmpeg/hardware/README.md)
- [go2rtc V4L2 documentation](https://github.com/AlexxIT/go2rtc/blob/master/internal/v4l2/README.md)
- [go2rtc Web viewer documentation](https://github.com/AlexxIT/go2rtc/blob/master/www/README.md)
- [Raspberry Pi 4 product brief](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-product-brief.pdf)
- [Raspberry Pi 5 product brief](https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-product-brief.pdf)
- [Mainsail webcam settings](https://docs.mainsail.xyz/overview/settings/webcams)
- [Fluidd camera settings](https://docs.fluidd.xyz/features/cameras/)
```

- [ ] **Step 2: Verify the guide has all planned sections and only one troubleshooting section**

Run:

```bash
rg -n "^## |^### Troubleshooting|^### Check|^### Confirm|^### Remove" content/docs/guides/go2rtc-camera-streaming.md
```

Expected:
- `## Introduction`
- `## Prerequisites`
- `## Install FFmpeg`
- `## Install go2rtc`
- `## Configure a Camera Stream`
- `## Test go2rtc`
- `## Start go2rtc on Boot`
- `## Configure Mainsail`
- `## Configure Fluidd`
- `## Troubleshooting`
- `## Further Reading`
- Exactly one `## Troubleshooting`

- [ ] **Step 3: Commit Task 3**

Run:

```bash
git add content/docs/guides/go2rtc-camera-streaming.md
git commit -m "[TASK] Add go2rtc frontend and troubleshooting docs"
```

Expected: commit succeeds with one modified guide file.

## Task 4: Verify Hugo Build and Final Guide Quality

**Files:**
- Verify: `content/docs/guides/go2rtc-camera-streaming.md`

- [ ] **Step 1: Check Markdown for unresolved markers and required choices**

Run:

```bash
rg -n "T[B]D|T[O]DO|\\$PWD" content/docs/guides/go2rtc-camera-streaming.md
```

Expected: no output and exit code 1.

Run:

```bash
rg -n "go2rtc_linux_arm64|ice_servers|Bullseye|Buster|Stretch|Jessie|Bookworm|Trixie|Raspberry Pi 5|#hardware|HTML Iframe|WebRTC \\(go2rtc\\)" content/docs/guides/go2rtc-camera-streaming.md
```

Expected:
- `go2rtc_linux_arm64` appears in the binary download section.
- `ice_servers` appears only in explanatory text saying the sample omits it.
- `Bookworm` and `Trixie` appear in supported OS wording.
- `Bullseye`, `Buster`, `Stretch`, and `Jessie` appear only in the legacy/out-of-scope callout.
- `Raspberry Pi 5` and `#hardware` appear in the hardware caveat/troubleshooting text.
- `HTML Iframe` appears in the Mainsail section.
- `WebRTC (go2rtc)` appears in the Fluidd section.

Run:

```bash
rg -n "^\\s+ice_servers:" content/docs/guides/go2rtc-camera-streaming.md
```

Expected: no output and exit code 1.

- [ ] **Step 2: Check whitespace errors**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 3: Build the site**

Run:

```bash
npm run build
```

Expected:
- Hugo build exits with code 0.
- No shortcode errors.
- No Markdown render errors.

- [ ] **Step 4: Inspect the generated guide page if the build succeeds**

Run:

```bash
rg -n "Low-Latency Camera Streaming with go2rtc|Install FFmpeg|Configure Mainsail|Configure Fluidd|Further Reading" public/docs/guides/go2rtc-camera-streaming/index.html
```

Expected:
- Each searched heading appears in the generated HTML.

- [ ] **Step 5: Commit verification fixes if any were needed**

If Task 4 required edits, commit them:

```bash
git add content/docs/guides/go2rtc-camera-streaming.md
git commit -m "[TASK] Polish go2rtc guide"
```

If Task 4 required no edits, do not create an empty commit.

- [ ] **Step 6: Report final status**

Run:

```bash
git status --short
```

Expected: clean worktree except for generated files already ignored by the repository.

Report:
- Final commits created for the guide.
- `npm run build` result.
- Any build or render blocker with exact command output if one occurs.
