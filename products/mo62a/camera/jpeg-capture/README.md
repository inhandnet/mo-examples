# IMX219 JPEG capture through TI ISP

Capture IMX219 frames through the TI ISP using V4L2 mmap, then software JPEG encoding. This is not a hardware JPEG encoder test. Use the camera tutorial to configure the boot entry, sensor and DCC files. The script needs root and a new output directory: `sudo bash capture-jpeg-mmap.sh OUTPUT_DIRECTORY`.

Tutorial: https://developer.inhand.online/docs/mo-62a/application-development/camera-and-video/

See `MIGRATION.md` and the local `LICENSE` for source and licensing.
