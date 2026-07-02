---
title: "Custom Boot Splash Screen"
description: "How to replace the Raspberry Pi boot splash with a custom Voron logo using Plymouth"
---

## Introduction

Raspberry Pi OS ships a Plymouth-based boot splash, the `pix` theme. You can clone it and swap in a custom image without touching the underlying splash mechanism. This guide clones `pix` into a new `voron` theme, drops in one of the Voron splash images from [samwiseg0's misc_3dprinting repository](https://github.com/samwiseg0/misc_3dprinting/tree/main/guides/voron_rpi_bootscreen/Images), and enables it at boot.

This guide targets Raspberry Pi OS Bookworm and Trixie.

By the end, you will have:

- The `rpd-plym-splash` package installed, providing the stock `pix` Plymouth theme
- A `voron` Plymouth theme cloned from `pix` at `/usr/share/plymouth/themes/voron`
- A Voron splash image installed as that theme's `splash.png`
- The `voron` theme set as default, with the initrd rebuilt to match
- The splash screen enabled at boot, and the firmware rainbow/color-test screen disabled

## Prerequisites

- SSH access to the printer host
- A user with `sudo` access
- Raspberry Pi OS Bookworm or Trixie
- Network access from the printer host to GitHub, to download the splash image

## Install the Plymouth splash package

1. Update the APT package index:

   ```bash title="Updating package indexes"
   sudo apt update
   ```

1. Install the Plymouth splash package:

   ```bash title="Installing rpd-plym-splash"
   sudo apt install -y rpd-plym-splash
   ```

   This pulls in Plymouth itself plus the `pix` theme at `/usr/share/plymouth/themes/pix`. That includes `pix.script`. `raspi-config` checks for this file before it lets you enable the splash screen.

## Create the Voron theme

Clone the `pix` theme into a new `voron` theme rather than editing `pix` in place, so the original theme stays intact as a fallback.

1. Copy the theme directory:

   ```bash title="Cloning the pix theme"
   cd /usr/share/plymouth/themes/
   sudo cp -a pix voron
   cd voron
   ```

1. Rename the script and theme definition files to match:

   ```bash title="Renaming theme files"
   sudo mv pix.script voron.script
   sudo mv pix.plymouth voron.plymouth
   ```

## Download the splash image

Download the image as your regular user into `/tmp` first, rather than running `wget` under `sudo` directly against a system directory. A failed or partial download then never touches `/usr/share`. `sudo` only shows up for the final copy.

The example below uses the gunmetal splash. Other colors are available from the same repository; see the table below.

1. Download the image to a staging location:

   ```bash title="Downloading the splash image"
   wget -O /tmp/voron-splash.png \
     https://raw.githubusercontent.com/samwiseg0/misc_3dprinting/main/guides/voron_rpi_bootscreen/Images/voron_splash_gunmetal.png
   ```

1. Confirm the download is a valid PNG:

   ```bash title="Checking the downloaded file"
   file /tmp/voron-splash.png
   ```

   The output should report a PNG image, not `HTML document` or `empty`.

1. Copy the image into the theme directory as `splash.png`, replacing the original:

   ```bash title="Installing the splash image"
   sudo cp /tmp/voron-splash.png /usr/share/plymouth/themes/voron/splash.png
   ```

:::note[Other colors and serial variants]
The source repository has 8 colors, each with a plain version and a `_serial` version. Substitute the filename in the `wget` command above to use a different one:

| Color | Plain | With serial number area |
|---|---|---|
| Aqua | `voron_splash_aqua.png` | `voron_splash_aqua_serial.png` |
| Blue | `voron_splash_blue.png` | `voron_splash_blue_serial.png` |
| Green | `voron_splash_green.png` | `voron_splash_green_serial.png` |
| Grey | `voron_splash_grey.png` | `voron_splash_grey_serial.png` |
| Gunmetal | `voron_splash_gunmetal.png` | `voron_splash_gunmetal_serial.png` |
| Orange | `voron_splash_orange.png` | `voron_splash_orange_serial.png` |
| Purple | `voron_splash_purple.png` | `voron_splash_purple_serial.png` |
| Red | `voron_splash_red.png` | `voron_splash_red_serial.png` |

All filenames live under the same [`Images` directory](https://github.com/samwiseg0/misc_3dprinting/tree/main/guides/voron_rpi_bootscreen/Images). Browse it to preview a color before downloading.
:::

## Fix the theme definition file

`voron.plymouth` still refers to the old `pix` paths and name after the rename. Fix it with `sed` instead of opening an editor:

```bash title="Updating voron.plymouth"
sudo sed -i 's/pix/voron/g' /usr/share/plymouth/themes/voron/voron.plymouth
```

This replaces every `pix` reference (theme name, image directory, script file path) with `voron`. It only touches lines that still say `pix`, so running it again after it succeeds once is a no-op.

Verify the result:

```bash title="Checking voron.plymouth"
cat /usr/share/plymouth/themes/voron/voron.plymouth
```

It should read:

```ini title="voron.plymouth"
[Plymouth Theme]
Name=voron
Description=Raspberry Pi Desktop Splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/voron
ScriptFile=/usr/share/plymouth/themes/voron/voron.script
```

## Set the Voron theme as default

Set `voron` as the default Plymouth theme and rebuild the initrd so the new theme is baked into the boot image:

```bash title="Setting the default theme"
sudo plymouth-set-default-theme --rebuild-initrd voron
```

:::caution[Command produces no output]
This command is normally silent on success. If it reports an error about the initrd, re-run it and confirm `voron.plymouth` looks correct as shown above before continuing.
:::

## Enable the splash screen at boot

Enable the boot splash without going through the `raspi-config` menu:

```bash title="Enabling the splash screen"
sudo raspi-config nonint do_boot_splash 0
```

This appends `quiet splash plymouth.ignore-serial-consoles` to `cmdline.txt` (`/boot/firmware/cmdline.txt` on Bookworm and Trixie) if those options aren't already present, so it's safe to run more than once.

## Disable the firmware rainbow splash

The Raspberry Pi firmware shows its own rainbow/color-test screen before Plymouth starts. Disable it by adding `disable_splash=1` to `config.txt`, guarding against adding the line twice:

```bash title="Disabling the firmware splash"
grep -qxF 'disable_splash=1' /boot/firmware/config.txt || \
  echo 'disable_splash=1' | sudo tee -a /boot/firmware/config.txt
```

## Reboot and verify

```bash title="Rebooting"
sudo reboot
```

After the printer host comes back up, the Voron splash should appear during boot in place of the Raspberry Pi rainbow screen and the default `pix` splash.

## Revert to the default theme

To go back to the stock Raspberry Pi splash:

```bash title="Reverting to the pix theme"
sudo plymouth-set-default-theme --rebuild-initrd pix
```

To also turn the splash screen off entirely:

```bash title="Disabling the splash screen"
sudo raspi-config nonint do_boot_splash 1
```

The `voron` theme directory and the downloaded image are left in place; delete `/usr/share/plymouth/themes/voron` manually if you no longer want them.

## Troubleshooting

### Splash screen never appears

- Confirm `splash` was added to `cmdline.txt`:

  ```bash title="Checking cmdline.txt"
  cat /boot/firmware/cmdline.txt
  ```

  If `splash` is missing, re-run `sudo raspi-config nonint do_boot_splash 0`.

- Confirm the `voron` theme is set as default:

  ```bash title="Checking the default theme"
  plymouth-set-default-theme
  ```

  This should print `voron`. If it doesn't, re-run the `plymouth-set-default-theme --rebuild-initrd voron` command.

### Rainbow screen still appears before the splash

Confirm `disable_splash=1` is present in `config.txt`:

```bash title="Checking config.txt"
grep disable_splash /boot/firmware/config.txt
```

### Image looks stretched, cropped, or has black bars

The source images aren't guaranteed to match your display's exact resolution or aspect ratio. Plymouth scales the image to fit, which can distort or crop it on some displays. No universal fix for this: edit the PNG to match your screen's aspect ratio before copying it into the theme directory, or try a different attached display.

### Initrd rebuild finishes but the splash doesn't change

Some Bookworm updates changed how the initrd gets rebuilt. If the splash doesn't change after a reboot despite no errors, force an initramfs rebuild directly:

```bash title="Forcing an initramfs rebuild"
sudo update-initramfs -u
```

Then reboot again.

## Further reading

- [samwiseg0/misc_3dprinting: voron_rpi_bootscreen Images](https://github.com/samwiseg0/misc_3dprinting/tree/main/guides/voron_rpi_bootscreen/Images)
- [Raspberry Pi config.txt reference](https://www.raspberrypi.com/documentation/computers/config_txt.html)
- [Raspberry Pi Configuration documentation](https://www.raspberrypi.com/documentation/computers/configuration.html)
- [RPi-Distro/raspi-config source](https://github.com/RPi-Distro/raspi-config/blob/bookworm/raspi-config)
- [Plymouth project (GitLab)](https://gitlab.freedesktop.org/plymouth/plymouth)
