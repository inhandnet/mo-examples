#!/bin/bash
# Capture 30 IMX219 frames through the TI ISP, retaining the final two JPEGs.
# Uses V4L2 mmap for repeatable capture on the tested Mo62A image.
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo: sudo bash capture-jpeg-mmap.sh OUTPUT_DIRECTORY" >&2
    exit 1
fi
out=${1:?Specify a new output directory}
if [ -e "$out" ]; then
    echo "Output directory already exists: $out" >&2
    exit 1
fi
mkdir -p "$out"
init-imx219
gst-launch-1.0 \
    v4l2src device=/dev/video-imx219-cam0 io-mode=2 num-buffers=30 ! \
    'video/x-bayer,format=rggb,width=1920,height=1080,framerate=30/1' ! \
    tiovxisp sensor-name=SENSOR_SONY_IMX219_RPI \
      dcc-isp-file=/opt/imaging/imx219/linear/dcc_viss.bin \
      sink_0::dcc-2a-file=/opt/imaging/imx219/linear/dcc_2a.bin \
      format-msb=7 ! \
    'video/x-raw,format=NV12,width=1920,height=1080' ! \
    videoconvert ! jpegenc quality=90 ! \
    multifilesink location="$out/frame-%02d.jpg" max-files=2
file "$out"/frame-*.jpg
