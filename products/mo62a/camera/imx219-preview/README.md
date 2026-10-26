# IMX219 CSI live preview

`imx219-preview.sh` configures the IMX219 camera through the media controller and runs a GStreamer pipeline `v4l2src → tiovxisp (VPAC ISP) → NV12 → kmssink` to show a live preview on the HDMI output.

```bash
sudo imx219-preview.sh [fps]      # fps: 5 | 8 | 10 | 15 (default) | 30
```

Prerequisites on the Mo62A board:

- The camera boot entry must be active: the IMX219 overlay is selected with `bootcfg switch` (the `-cam` entry) followed by a reboot; see the camera page in mo-docs.
- DCC tuning files for `tiovxisp` under `/opt/imaging/imx219/linear/` (installed by `init-imx219` on the image).
- `gstreamer1.0-tools` and `v4l-utils` (`media-ctl`, `v4l2-ctl`).
- Root privileges: `kmssink` needs DRM master. The script stops a running display manager (lightdm, gdm3, sddm, weston) while the preview runs and restarts it on exit.

Exposure and gain can be overridden with the `EXPOSURE`, `GAIN` and `DGAIN` environment variables; the script maps each frame rate to the matching vertical blanking and maximum exposure.

`Makefile` has no build step; the Mo62A flash tool calls `make install APP_INSTALL_DIR=...` to place the script in `/usr/local/bin` of the target root filesystem.

Origin: Mo62A repository, `board-support/extra-applications/imx219-preview` (Apache-2.0). The script was imported unchanged; `shellcheck` reports no findings.
