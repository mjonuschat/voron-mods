# go2rtc Guide Design

## Goal

Add a new GitHub Pages guide that walks a Klipper printer user through installing go2rtc, publishing a USB/V4L2 camera stream, running go2rtc at boot, and configuring the resulting stream in Mainsail and Fluidd.

The finished guide should be usable without consulting the rough notes. It should explain what each command changes, call out the common printer-host pitfalls, and leave the reader with a working low-latency camera feed inside their preferred printer UI.

## Audience

The guide is for Voron/Klipper users who can SSH into their printer host and edit configuration files, but who may not know go2rtc's binary names, WebUI, WebRTC URLs, or frontend camera settings.

Assumptions:

- The printer host is a Debian/Raspberry Pi OS style Linux system.
- The default printer host user is `pi`; the text will tell readers to replace `/home/pi` if they use a different user.
- The first example camera is a USB camera exposed as `/dev/video0`.
- The guide focuses on LAN access. Public internet exposure is intentionally out of scope.

## Sources Checked

- go2rtc README for release binary names, default ports, and supported streaming modes.
- go2rtc app configuration docs for default `api`, `rtsp`, `srtp`, `webrtc`, `ffmpeg`, and log settings.
- go2rtc V4L2 docs for USB camera constraints and device format/resolution caveats.
- go2rtc Web viewer docs for `stream.html?src=...&mode=...` URLs.
- Fluidd camera docs for the native `WebRTC (go2rtc)` camera type.
- Mainsail webcam docs for supported camera service types and HTTP iframe behavior.

## Content Structure

The guide will be added as a new page under `content/docs/guides/` and will follow the existing guide style: front matter, `##` sections, numbered setup steps, Hugo callouts, fenced command/config blocks, verification steps, troubleshooting, and further reading.

Target file:

```text
content/docs/guides/go2rtc-camera-streaming.md
```

Proposed front matter:

```yaml
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
  title: ""
  description: ""
  canonical: ""
  noindex: false
---
```

Planned sections:

1. Introduction
2. Prerequisites
3. Install FFmpeg
4. Install go2rtc
5. Configure a Camera Stream
6. Test go2rtc
7. Start go2rtc on Boot
8. Configure Mainsail
9. Configure Fluidd
10. Troubleshooting
11. Further Reading

## Section Design

### Introduction

Explain that go2rtc is a lightweight camera streaming application that can serve a USB camera as WebRTC for lower latency and bandwidth use than traditional MJPEG streams. Keep the focus on printer monitoring, not on go2rtc's wider smart-home features.

The introduction should also state what the reader will end up with:

- A `go2rtc` binary installed in `/home/pi/go2rtc`.
- A `go2rtc.yaml` file defining a `chamber` camera stream.
- A `go2rtc` systemd service that starts at boot.
- A camera entry in Mainsail and/or Fluidd.

### Prerequisites

List required context before commands:

- SSH access to the printer host.
- A supported Linux camera device, usually `/dev/video0`.
- A recent Mainsail or Fluidd installation.
- Network access from the browser to the printer host.
- A camera that is not already exclusively held by another streamer.

Include a note that Crowsnest, camera-streamer, ustreamer, or mjpg-streamer may already be using the camera device. The guide should not instruct readers to remove those tools globally, but should explain that only one process can normally open a V4L2 camera at a time.

### Install FFmpeg

Explain that the sample stream uses go2rtc's FFmpeg source to read the USB camera and transcode it to H.264 for WebRTC. FFmpeg must be available on the printer host before go2rtc can start that stream.

Use a dedicated install step:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

Do not require a full `sudo apt upgrade` as part of the guide. If the package install fails because the package index is stale or the OS is very old, the troubleshooting text can recommend updating the system separately.

Ask the reader to verify the install:

```bash
ffmpeg -version
```

### Install go2rtc

Use the rough notes as the base, but make the commands consistent and less architecture-fragile:

```bash
mkdir -p ~/go2rtc
cd ~/go2rtc
wget -O go2rtc https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_arm64
chmod a+x go2rtc
```

Add a callout explaining that `go2rtc_linux_arm64` is correct for a 64-bit Raspberry Pi OS install, while 32-bit Raspberry Pi OS should use `go2rtc_linux_arm`. Link to the go2rtc release assets for other platforms.

Avoid `cd ~` followed by `mkdir go2rtc` because rerunning the guide should not fail if the directory already exists.

### Configure a Camera Stream

Create `~/go2rtc/go2rtc.yaml` with a complete but concise configuration. The config should preserve the rough-note defaults where they are useful, but it should not imply every default must be manually specified.

Proposed config:

```yaml
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
  ice_servers:
    - urls: [ "stun:stun.l.google.com:19302" ]

streams:
  chamber: ffmpeg:device?video=/dev/video0&input_format=yuyv422&video_size=1280x720#video=h264#hardware
```

Explain the stream line directly:

- `chamber` is the stream name used later in go2rtc, Mainsail, and Fluidd.
- `/dev/video0` is the camera device path.
- `input_format=yuyv422` and `video_size=1280x720` must match a mode supported by the camera.
- `#video=h264#hardware` asks FFmpeg/go2rtc to produce H.264 using hardware acceleration when available.

Include a short optional diagnostic command:

```bash
ffmpeg -f v4l2 -list_formats all -i /dev/video0
```

This helps readers find supported formats and resolutions without turning the guide into a camera tuning reference.

### Test go2rtc

Run go2rtc in the foreground before adding systemd:

```bash
/home/pi/go2rtc/go2rtc -config /home/pi/go2rtc/go2rtc.yaml
```

Then open:

```text
http://<printer-ip>:1984
```

Tell the reader to select the stream link for `chamber` and wait briefly for the first keyframe/frame sync. The guide should describe a successful test as visible live video in the browser.

Include common foreground-test failures:

- `permission denied`: binary is not executable or camera permissions are wrong.
- `no such file or directory`: binary path, config path, or camera path is wrong.
- FFmpeg format errors: `input_format` or `video_size` is unsupported.

### Start go2rtc on Boot

Create a systemd service at `~/go2rtc/go2rtc.service`, then enable it through systemd.

Use this unit:

```ini
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

Install and start it:

```bash
sudo systemctl enable "$PWD/go2rtc.service"
sudo systemctl daemon-reload
sudo systemctl start go2rtc
sudo systemctl status go2rtc
```

The guide should explain that `User=root` is chosen for predictable camera-device access on printer hosts. It should add that advanced users may create a less-privileged service user if they also configure the needed video-device permissions.

Mention that logs can be inspected with:

```bash
journalctl -u go2rtc -f
```

### Configure Mainsail

Use a Mainsail camera entry that embeds go2rtc's viewer page.

Expected settings:

- **Name**: `Chamber`
- **Service**: `HTML Iframe`
- **Stream URL**: `http://<printer-ip>:1984/stream.html?src=chamber&mode=webrtc`
- **Aspect ratio**: match the configured stream, usually `16:9` for `1280x720`
- Rotation/flip: configure to match the physical camera orientation

Explain why iframe mode is used: go2rtc provides its own WebRTC viewer at `stream.html`, and Mainsail can embed that page even though Mainsail's native WebRTC presets are aimed at other streamers.

If the user accesses Mainsail over HTTPS, call out that embedding an HTTP camera page may be blocked by the browser as mixed content. The guide should keep HTTPS/reverse-proxy setup out of scope, but it should name the symptom so users know why a blank iframe can happen.

### Configure Fluidd

Use Fluidd's native go2rtc camera type.

Expected settings:

- **Name**: `Chamber`
- **Type**: `WebRTC (go2rtc)`
- **Stream URL / go2rtc URL**: the printer host go2rtc endpoint, using `http://<printer-ip>:1984`
- **Stream name / source**: `chamber` if Fluidd exposes a separate source field
- **Aspect ratio**: `16:9` for the sample config
- Rotation/flip: configure to match the physical camera orientation

If the exact Fluidd field labels differ by version, the guide should describe the values rather than overfitting to one UI screenshot. It should link to Fluidd's camera docs for the current UI wording.

### Troubleshooting

Troubleshooting should be concrete and command-oriented:

- Check service state:

  ```bash
  sudo systemctl status go2rtc
  ```

- Follow service logs:

  ```bash
  journalctl -u go2rtc -f
  ```

- Check whether the camera exists:

  ```bash
  ls -l /dev/video*
  ```

- Check supported camera modes:

  ```bash
  ffmpeg -f v4l2 -list_formats all -i /dev/video0
  ```

- Check whether another process is using the camera:

  ```bash
  sudo fuser /dev/video0
  ```

The text should map each diagnostic to the likely fix: change device path, change `input_format`, change `video_size`, stop/reconfigure the competing streamer, or correct the frontend URL.

### Further Reading

Link to:

- go2rtc releases
- go2rtc README/config docs
- go2rtc V4L2 docs
- go2rtc Web viewer docs
- Mainsail webcam settings docs
- Fluidd camera docs

## Implementation Details

The installation should normalize the downloaded binary to `/home/pi/go2rtc/go2rtc` so later commands and the systemd unit do not depend on the release asset name. The guide will mention choosing the correct release asset for the host architecture, with `go2rtc_linux_arm64` as the Raspberry Pi 64-bit example.

The sample `go2rtc.yaml` will keep the user's intended stream name, `chamber`, and use a V4L2/FFmpeg source for `/dev/video0` at `1280x720`. It will include a note that only one service can usually open a USB camera device at a time, so Crowsnest or another streamer may need to be stopped or reconfigured.

The systemd unit will use the normalized binary path and config path. It should include `WorkingDirectory=/home/pi/go2rtc`, restart automatically, and run as root only because common printer-host USB camera permissions are inconsistent. The text will call this out rather than presenting it as an ideal security posture.

The Mainsail section will use an HTTP iframe style configuration pointed at:

```text
http://<printer-ip>:1984/stream.html?src=chamber&mode=webrtc
```

The Fluidd section will use Fluidd's `WebRTC (go2rtc)` camera type and configure the go2rtc stream source for `chamber`.

## Editorial Guidelines

The guide should use direct imperative wording, matching the existing guides:

- "Install the required package..." rather than long background prose.
- "Append the following configuration..." only when the reader is truly appending to an existing file.
- "Create the file..." for new files such as `go2rtc.yaml` and `go2rtc.service`.

Avoid overpromising latency or CPU savings. State that WebRTC is generally lower latency and more bandwidth efficient than MJPEG, but performance still depends on camera format, resolution, network quality, and hardware acceleration.

Keep security wording practical:

- go2rtc exposes the WebUI/API on port `1984` and streams on ports such as `8555`.
- The guide assumes a trusted local network.
- Do not expose these ports directly to the public internet as part of this guide.

## Verification

The guide should ask the reader to verify each stage:

- `ffmpeg` and the go2rtc binary are installed.
- `go2rtc` starts in the foreground without config errors.
- `http://<printer-ip>:1984` loads and the `chamber` stream plays.
- `systemctl status go2rtc` reports the service as active.
- The camera appears in Mainsail and Fluidd.

Implementation verification for the repository:

- Run a Hugo build with the existing package script if dependencies are available:

  ```bash
  npm run build
  ```

- Check Markdown/code-block formatting by visually reviewing the rendered guide or, if a full render is not available, reviewing the generated Markdown around Hugo shortcodes and fenced blocks.

## Troubleshooting

Troubleshooting should cover:

- Wrong binary for the host architecture.
- Camera device path mismatch, such as `/dev/video1` instead of `/dev/video0`.
- Unsupported camera format, resolution, or frame rate.
- Camera already in use by Crowsnest or another process.
- WebUI or WebRTC ports blocked or unreachable.
- Service failures visible through `journalctl -u go2rtc`.

## Acceptance Criteria

- A new guide exists at `content/docs/guides/go2rtc-camera-streaming.md`.
- The guide explicitly installs and verifies FFmpeg before configuring the FFmpeg-backed go2rtc stream.
- The guide includes a corrected install flow that downloads the selected release asset as `~/go2rtc/go2rtc`.
- The guide includes a complete `go2rtc.yaml` example for the `chamber` stream.
- The guide includes a complete systemd unit using the normalized binary path.
- The guide includes both Mainsail and Fluidd configuration sections.
- The guide includes verification steps before and after installing the systemd service.
- The guide includes troubleshooting steps with concrete commands.
- The guide builds successfully with Hugo, or any build failure is documented with the exact blocker.

## Out Of Scope

- Docker, Home Assistant, and go2rtc add-on installation paths.
- Multiple camera examples beyond explaining how to duplicate the stream entry.
- Public internet exposure, reverse proxies, TURN servers, or authenticated go2rtc access.
- Screenshots, unless added later from a real configured printer UI.
