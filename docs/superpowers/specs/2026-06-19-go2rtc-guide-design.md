# go2rtc Guide Design

## Goal

Add a new GitHub Pages guide that walks a Klipper printer user through installing go2rtc, publishing a USB/V4L2 camera stream, running go2rtc at boot, and configuring the resulting stream in Mainsail and Fluidd.

## Audience

The guide is for Voron/Klipper users who can SSH into their printer host and edit configuration files, but who may not know go2rtc's binary names, WebUI, WebRTC URLs, or frontend camera settings.

## Sources Checked

- go2rtc README for release binary names, default ports, and supported streaming modes.
- go2rtc app configuration docs for default `api`, `rtsp`, `srtp`, `webrtc`, `ffmpeg`, and log settings.
- go2rtc V4L2 docs for USB camera constraints and device format/resolution caveats.
- go2rtc Web viewer docs for `stream.html?src=...&mode=...` URLs.
- Fluidd camera docs for the native `WebRTC (go2rtc)` camera type.
- Mainsail webcam docs for supported camera service types and HTTP iframe behavior.

## Content Structure

The guide will be added as a new page under `content/docs/guides/` and will follow the existing guide style: front matter, `##` sections, numbered setup steps, Hugo callouts, fenced command/config blocks, verification steps, troubleshooting, and further reading.

Planned sections:

1. Introduction
2. Prerequisites
3. Install go2rtc
4. Configure a Camera Stream
5. Test go2rtc
6. Start go2rtc on Boot
7. Configure Mainsail
8. Configure Fluidd
9. Troubleshooting
10. Further Reading

## Implementation Details

The installation should normalize the downloaded binary to `/home/pi/go2rtc/go2rtc` so later commands and the systemd unit do not depend on the release asset name. The guide will mention choosing the correct release asset for the host architecture, with `go2rtc_linux_arm64` as the Raspberry Pi 64-bit example.

The sample `go2rtc.yaml` will keep the user's intended stream name, `chamber`, and use a V4L2/FFmpeg source for `/dev/video0` at `1280x720`. It will include a note that only one service can usually open a USB camera device at a time, so Crowsnest or another streamer may need to be stopped or reconfigured.

The systemd unit will use the normalized binary path and config path. It should include `WorkingDirectory=/home/pi/go2rtc`, restart automatically, and run as root only because common printer-host USB camera permissions are inconsistent. The text will call this out rather than presenting it as an ideal security posture.

The Mainsail section will use an HTTP iframe style configuration pointed at:

```text
http://<printer-ip>:1984/stream.html?src=chamber&mode=webrtc
```

The Fluidd section will use Fluidd's `WebRTC (go2rtc)` camera type and configure the go2rtc stream source for `chamber`.

## Verification

The guide should ask the reader to verify each stage:

- `ffmpeg` and the go2rtc binary are installed.
- `go2rtc` starts in the foreground without config errors.
- `http://<printer-ip>:1984` loads and the `chamber` stream plays.
- `systemctl status go2rtc` reports the service as active.
- The camera appears in Mainsail and Fluidd.

## Troubleshooting

Troubleshooting should cover:

- Wrong binary for the host architecture.
- Camera device path mismatch, such as `/dev/video1` instead of `/dev/video0`.
- Unsupported camera format, resolution, or frame rate.
- Camera already in use by Crowsnest or another process.
- WebUI or WebRTC ports blocked or unreachable.
- Service failures visible through `journalctl -u go2rtc`.

## Out Of Scope

- Docker, Home Assistant, and go2rtc add-on installation paths.
- Multiple camera examples beyond explaining how to duplicate the stream entry.
- Public internet exposure, reverse proxies, TURN servers, or authenticated go2rtc access.
- Screenshots, unless added later from a real configured printer UI.
