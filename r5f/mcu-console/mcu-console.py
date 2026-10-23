#!/usr/bin/env python3
"""Talk to the Mo62A MCU R5F console firmware over RPMsg.

  sudo mcu-console            interactive prompt (exit with Ctrl-D or 'exit')
  sudo mcu-console tasks      run one command and exit
"""
import glob
import os
import select
import sys

CORE = "79000000.r5f"   # MCU R5F
ENDPOINT = 15           # console end point announced by the firmware
TIMEOUT_S = 1.0
MAX_PAYLOAD = 496       # 512-byte transport buffer minus the RPMsg header


def find_device():
    for channel in glob.glob(f"/sys/bus/rpmsg/devices/*.rpmsg_chrdev.-1.{ENDPOINT}"):
        if CORE in os.path.realpath(channel):
            for node in glob.glob(f"{channel}/rpmsg/rpmsg[0-9]*"):
                return "/dev/" + os.path.basename(node)
    sys.exit(f"MCU console not found: is the console firmware running on {CORE}?")


def run(fd, command):
    payload = command.encode('utf-8')
    if not payload or len(payload) > MAX_PAYLOAD:
        raise ValueError(f"command must contain 1..{MAX_PAYLOAD} UTF-8 bytes")
    if os.write(fd, payload) != len(payload):
        raise OSError("incomplete RPMsg write")
    if not select.select([fd], [], [], TIMEOUT_S)[0]:
        raise TimeoutError(f"no reply within {TIMEOUT_S:g} s")
    reply = os.read(fd, MAX_PAYLOAD)
    if not reply:
        raise OSError("RPMsg endpoint closed without a reply")
    return reply.decode(errors="replace").rstrip("\n")


def main():
    device = find_device()
    try:
        fd = os.open(device, os.O_RDWR)
    except PermissionError:
        sys.exit(f"{device}: permission denied, run with sudo")
    try:
        if len(sys.argv) > 1:
            print(run(fd, " ".join(sys.argv[1:])))
            return
        print(f"Connected to {CORE} console on {device}. Type 'help', or 'exit' to quit.")
        while True:
            try:
                line = input("mcu> ").strip()
            except EOFError:
                print()
                break
            if line in ("exit", "quit"):
                break
            if line:
                try:
                    print(run(fd, line))
                except ValueError as error:
                    print(f"mcu-console: {error}", file=sys.stderr)
                # Exit after transport failures: a late reply could otherwise
                # be misattributed to the next interactive command.
    finally:
        os.close(fd)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        sys.exit(f"mcu-console: {error}")
