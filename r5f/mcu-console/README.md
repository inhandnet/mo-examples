# MCU R5F console and RPMsg helpers

Firmware, Linux clients, the SDK patch, reload helper and the published firmware checksum stay together. Follow the MCU console tutorial for the exact SDK project and loading steps; the Device Manager R5F remains reserved. SDK installers and compiler versions are owned by mo-tools. The firmware and existing tutorial evidence are retained; this migration does not claim a new firmware build or board run.

Verify the retained binary with `sha256sum -c mo62a-mcu-console.out.sha256`. The command-line client is `python3 mcu-console.py help` on the configured board. Reload testing changes the MCU firmware state; follow the tutorial prerequisites and recovery procedure.

Tutorial: https://developer.inhand.online/docs/mo-62a/real-time-cores/mcu-console/

See `MIGRATION.md` and the local `LICENSE` for source and licensing.
