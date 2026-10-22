# Camera examples

| Directory | What it is | Origin |
| --- | --- | --- |
| `imx219-preview/` | Shell script that runs a live IMX219 CSI preview through the VPAC ISP to the HDMI output with GStreamer, plus the `Makefile` the Mo62A flash tool uses to install it. | Mo62A repository, `board-support/extra-applications/imx219-preview` |

See each subdirectory README for prerequisites. Camera pipelines with inference are in `../ai/edgeai-cpp/` (`app_edgeai` with the CSI configuration).
