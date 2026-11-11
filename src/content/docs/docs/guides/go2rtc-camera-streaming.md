---
title: "Camera Streaming with go2rtc"
description: "How to install go2rtc for a Klipper printer camera and configure the stream in Mainsail and Fluidd"
---

## Introduction

[go2rtc](https://github.com/AlexxIT/go2rtc) is a lightweight camera streaming application that can serve a printer camera over WebRTC. It usually has lower latency than a traditional MJPEG setup and works with browser-based printer UIs.

This guide installs go2rtc on a Raspberry Pi OS based printer host, configures a USB camera stream named `chamber`, starts go2rtc automatically with systemd, and adds the stream to Mainsail and Fluidd.

By the end, you will have:

- A `go2rtc` binary installed at `/home/pi/go2rtc/go2rtc`
- A `go2rtc.yaml` configuration file defining a `chamber` camera stream
- A `go2rtc` systemd service that starts on boot
- A camera entry in Mainsail or Fluidd

:::note[Camera device access]
Crowsnest, camera-streamer, ustreamer, mjpg-streamer or another webcam service may already be using the camera. Usually only one process at a time can open a V4L2 USB camera. If another service is using `/dev/video0`, stop or reconfigure it before testing go2rtc with the same device.
:::

:::caution[Supported OS]
This guide targets Raspberry Pi OS Bookworm and Trixie. Older releases such as Bullseye, Buster, Stretch and Jessie are not supported. If your printer host runs one of them, upgrade or re-image to Bookworm or Trixie before following these steps.
:::

## Prerequisites

- A printer host running Raspberry Pi OS Bookworm or Trixie
- SSH access to the printer host
- A USB camera available as a Linux video device, usually `/dev/video0`
- A recent Mainsail or Fluidd installation
- A browser on the same local network as the printer host

## Install FFmpeg

The example stream uses go2rtc's FFmpeg source to read the USB camera and produce an H.264 stream that WebRTC can carry. Install FFmpeg before configuring go2rtc.

1. Update the APT package index:

   ```bash title="Updating package indexes"
   sudo apt update
   ```

1. Install FFmpeg:

   ```bash title="Installing FFmpeg"
   sudo apt install -y ffmpeg
   ```

1. Verify that FFmpeg is available:

   ```bash title="Checking FFmpeg"
   ffmpeg -version
   ```

   The command should print the installed FFmpeg version and build configuration.

## Install go2rtc

Install the go2rtc binary in `/home/pi/go2rtc`. The commands below use the `go2rtc_linux_arm64` release asset, which is the right binary for 64-bit Raspberry Pi OS.

:::note[Choosing the binary]
Use `go2rtc_linux_arm64` for 64-bit Raspberry Pi OS and `go2rtc_linux_arm` for 32-bit Raspberry Pi OS. Other builds are available on the [go2rtc releases page](https://github.com/AlexxIT/go2rtc/releases).
:::

1. Create the installation directory:

   ```bash title="Creating the go2rtc directory"
   mkdir -p ~/go2rtc
   cd ~/go2rtc
   ```

1. Download the latest go2rtc binary and save it as `go2rtc`:

   ```bash title="Downloading go2rtc"
   wget -O go2rtc https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_arm64
   ```

1. Make the binary executable:

   ```bash title="Making go2rtc executable"
   chmod a+x go2rtc
   ```

1. Verify the binary exists and is executable:

   ```bash title="Checking the go2rtc binary"
   ls -l /home/pi/go2rtc/go2rtc
   ```

   The permissions should include executable bits, such as `-rwxr-xr-x`.

## Find your camera device

Before writing the stream configuration, find the Linux video device for your camera and pick one capture mode it supports.

1. List video devices:

   ```bash title="Listing video devices"
   ls -l /dev/video*
   ```

   A single USB camera is often `/dev/video0`, but the number can vary.

1. Install the V4L2 utilities:

   ```bash title="Installing V4L2 utilities"
   sudo apt install -y v4l-utils
   ```

1. Map video devices to physical cameras:

   ```bash title="Listing V4L2 devices"
   v4l2-ctl --list-devices
   ```

   Use this output to choose the `video=` path for `go2rtc.yaml`. If several cameras are connected, `/dev/video0` can change after a reboot or after reconnecting USB devices. Persistent device paths and udev rules are outside the scope of this guide.

1. List the selected camera's supported formats and resolutions:

   ```bash title="Listing camera modes"
   ffmpeg -f v4l2 -list_formats all -i /dev/video0
   ```

   If your camera is not `/dev/video0`, replace `/dev/video0` with the device path from the previous step. Use one reported format and resolution for `input_format` and `video_size` in `go2rtc.yaml`.

## Configure a camera stream

Create `/home/pi/go2rtc/go2rtc.yaml` with a stream named `chamber`.

1. Open the configuration file:

   ```bash title="Creating go2rtc.yaml"
   nano /home/pi/go2rtc/go2rtc.yaml
   ```

1. Add the following configuration:

   ```yaml title="go2rtc.yaml"
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

The `chamber` stream reads `/dev/video0` as a V4L2 camera, requests `yuyv422` input at `1280x720`, and asks FFmpeg/go2rtc to produce H.264 video. Later steps use the stream name `chamber` in go2rtc, Mainsail and Fluidd.

:::caution[Hardware H.264 encoding]
The `#hardware` option depends on hardware and FFmpeg/go2rtc support. The Raspberry Pi 4 product brief lists H.264 encode support. The Raspberry Pi 5 product brief lists HEVC decode support but not H.264 encode. If `#hardware` causes startup errors or unusable CPU or video behavior, remove it and retest. If your camera can already provide H.264, consider a source you can pass through with `#video=copy` instead of transcoding.
:::

:::note[Additional cameras]
To add another camera, duplicate the `chamber:` entry under `streams:` with a new stream name and device path, such as `nozzle: ...video=/dev/video1...`. Each camera needs a supported format and resolution, and no other process may be using its device.
:::

## Test go2rtc

Before creating the systemd service, run go2rtc in the foreground so configuration errors show up immediately.

1. Start go2rtc manually:

   ```bash title="Starting go2rtc manually"
   /home/pi/go2rtc/go2rtc -config /home/pi/go2rtc/go2rtc.yaml
   ```

1. Open the go2rtc WebUI in a browser:

   ```text title="go2rtc WebUI"
   http://<printer-ip>:1984
   ```

1. Select the `chamber` stream link.

The video should start after a short delay. Stop the foreground process with **CTRL-C** before continuing.

Common errors at this stage:

- `permission denied`: the binary is not executable, or the camera device permissions are wrong.
- `no such file or directory`: the binary path, config path, or camera path is wrong.
- FFmpeg format errors: `input_format` or `video_size` is not supported by the camera.
- For hardware encoder errors, remove `#hardware` from the stream line and test again.

## Start go2rtc on boot

Create a systemd service so go2rtc starts automatically when the printer host boots.

1. Create the service file:

   ```bash title="Creating the go2rtc service"
   nano /home/pi/go2rtc/go2rtc.service
   ```

1. Add this unit:

   ```ini title="go2rtc.service"
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

:::note[Service user]
This service runs as `root` to avoid inconsistent USB camera permissions on printer hosts. You can run go2rtc as a less-privileged user if you also set up the required video device permissions.
:::

1. Enable the service using the absolute service-file path:

   ```bash title="Enabling go2rtc"
   sudo systemctl enable /home/pi/go2rtc/go2rtc.service
   ```

1. Reload systemd and start go2rtc:

   ```bash title="Starting go2rtc"
   sudo systemctl daemon-reload
   sudo systemctl start go2rtc
   ```

1. Check the service state:

   ```bash title="Checking go2rtc service state"
   sudo systemctl status go2rtc
   ```

To follow service logs while troubleshooting, run:

```bash title="Following go2rtc logs"
sudo journalctl -u go2rtc -f
```

## Configure Mainsail

Mainsail includes a `WebRTC (go2rtc)` webcam service for go2rtc streams.

1. Open Mainsail in your browser.
1. Go to **Settings > Webcams**.
1. Add a new webcam entry.
1. Configure the webcam with these values:

   - **Name**: `Chamber`
   - **Service**: `WebRTC (go2rtc)`
   - **Stream URL**: `http://<printer-ip>:1984/stream.html?src=chamber&mode=webrtc`
   - **Aspect ratio**: `16:9` for the sample `1280x720` stream
   - **Rotation/flip**: Set these to match your camera orientation

The `src=chamber` parameter must match the stream name in `go2rtc.yaml`.

:::caution[HTTPS and mixed content]
If you access Mainsail over HTTPS, the browser may block an HTTP camera stream as mixed content. This usually shows as a blank camera panel. HTTPS, reverse proxy and remote access setup are outside the scope of this guide.
:::

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

### Check go2rtc service state

Use systemd to confirm whether go2rtc is running:

```bash title="Checking go2rtc service state"
sudo systemctl status go2rtc
```

If the service is not active, inspect the logs:

```bash title="Following go2rtc logs"
sudo journalctl -u go2rtc -f
```

### Confirm the camera device path

List available video devices:

```bash title="Listing video devices"
ls -l /dev/video*
```

If your camera is not `/dev/video0`, update the `video=` parameter in `go2rtc.yaml`.

### Confirm the camera format and resolution

List supported camera modes:

```bash title="Listing camera modes"
ffmpeg -f v4l2 -list_formats all -i /dev/video0
```

If the configured `input_format` or `video_size` is not listed, update the stream line to use a supported mode.

### Check for another process using the camera

Check whether another service already has the camera open:

```bash title="Checking camera users"
sudo fuser /dev/video0
```

If another process is listed, stop or reconfigure that service before starting go2rtc with the same device.

### Remove hardware encoding

If go2rtc starts but the stream fails, or FFmpeg reports hardware encoder errors, remove `#hardware` from the stream line and restart go2rtc:

```yaml title="go2rtc.yaml"
streams:
  chamber: ffmpeg:device?video=/dev/video0&input_format=yuyv422&video_size=1280x720#video=h264
```

Then restart the service:

```bash title="Restarting go2rtc"
sudo systemctl restart go2rtc
```

### Check browser and network access

Open the go2rtc WebUI directly:

```text title="go2rtc WebUI"
http://<printer-ip>:1984
```

If the WebUI does not load, check the printer host IP address and that your browser is on the same local network.

## Further reading

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
