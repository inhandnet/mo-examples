# Mo62A zone-occupancy example

The two input clips come from Wikimedia Commons under CC BY 4.0. Preserve
`SOURCE.txt` with copied footage and result media. The example zone is fictional;
the site, author and depicted workers do not endorse this tutorial.

Follow the **Set up the toolchain**, **Compile your own model**, and **YOLO:
deployment and quantization** pages of Mo documentation in that order.

This example uses the unchanged TI YOLOX-tiny-lite 8210 COCO model and its matching
detection metadata. It detects the existing `person` class; it does not train a
new defect detector. The application uses bottom-center box points inside a
configured convex polygon, a dwell threshold and a clear delay. Events describe
aggregate zone occupancy, not the identity or track of individual people.

Host: x86_64, Python 3.10, TI ONNX Runtime 1.23.0, AM62A tools 11_02_17_00.
Target: the documented Mo62A V1.1.0 development stack. Do not run host setup or
install host requirements on the board. No GPU or Ultralytics installation is
required. The supplied scripts refuse to overwrite result/artifact directories.

`setup_host.sh` downloads the official TI source and binaries into a new directory
and installs Python dependencies only into its virtual environment. It requires
Python 3.10 with venv support, Git, curl, tar and the host system libraries listed
in the toolchain page. It does not call TI's broad setup/update scripts.
If the Python installation omits `ensurepip`, the script needs an existing pip
launcher supporting `--python` to bootstrap only the new virtual environment.

`fetch_model.py`, `prepare_inputs.py`, `compile_model.py` and `run_images.py`
implement download, frame preparation, calibration/compilation and raw-output
comparison. `run_video.py` produces `events.jsonl`, `events.csv`, `frames.jsonl`,
`summary.json`, screenshots of its actual output and `annotated.avi`.

Run business-rule tests without AI packages:

```bash
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

The example is an offline video replay, not a certified safety function or a
command to control equipment. End-of-file does not imply the zone became clear.
It has no face recognition, identity tracking, webhook, or actuator output.
Validate your own data, camera geometry, failure handling and privacy/retention
policy before any deployment. Do not expose raw footage or the development
viewer to an untrusted network.

Source and license records are in `sources.json`. Example code/documentation
follow this repository's CC BY-SA 4.0 license; official models, tool binaries and
footage have separate terms. The archive includes two prepared CC BY 4.0 video
inputs, but no TI binaries or pretrained weights. These are separate clips of
the same site, not a representative labeled accuracy dataset. An illustrative
ROI must not imply misconduct or endorsement by any depicted person.

## Repository checkout and assembled download

The application, licensed inputs and recorded results live in mo-examples.
`model.py` is a generated, hash-checked copy of the model contract owned by
mo-models; `dependencies/model-contract.json` pins its source commit. Do not
edit this generated copy. Host setup belongs to mo-tools/toolchain/host-setup,
and compilation belongs to mo-models/compile/zone-demo. The developer website
assembles those fixed sources into the complete tutorial download and includes
`WEBSITE-SOURCES.json` with per-file origins and hashes.

For inference with an existing verified bundle, run the application scripts
directly from this checkout. For host setup and compilation, follow the linked
tutorial and use the complete download; those steps are not included in this
application directory. The original evidence is retained under `evidence/`;
moving the files does not add new board validation. The code in this directory
retains its local CC BY-SA 4.0 LICENSE, rather than the repository default.
