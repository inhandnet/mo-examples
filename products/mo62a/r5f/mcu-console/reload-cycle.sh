#!/usr/bin/env bash
# Usage: sudo reload-cycle.sh <firmware basename in /lib/firmware> <1..1000 cycles>
# The root overrides allow an isolated test fixture; defaults target the board.
set -euo pipefail
[[ $# == 2 ]] || { echo 'Usage: reload-cycle.sh <firmware basename> <1..1000 cycles>' >&2; exit 2; }
fw=$1
cycles=$2
# Both validation conditions must pass; either failure takes the error branch.
# shellcheck disable=SC2015
[[ $fw =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]*$ && $cycles =~ ^[1-9][0-9]{0,3}$ ]] && ((cycles <= 1000)) || {
  echo 'Invalid firmware name or cycle count (use 1..1000).' >&2; exit 2;
}
rproc_root=${MO_RPROC_ROOT:-/sys/class/remoteproc}
firmware_root=${MO_FIRMWARE_ROOT:-/lib/firmware}
trace_root=${MO_TRACE_ROOT:-/sys/kernel/debug/remoteproc}
script_dir=$(dirname "$(readlink -f "$0")")
echo_tool=${MO_ECHO_TOOL:-$script_dir/rpmsg_echo_latency}
[[ -r $firmware_root/$fw && -s $firmware_root/$fw ]] || { echo 'Firmware is missing or empty.' >&2; exit 1; }
[[ -x $echo_tool ]] || { echo 'rpmsg_echo_latency is missing or not executable.' >&2; exit 1; }
cores=()
for name in "$rproc_root"/remoteproc*/name; do
  [[ -r $name ]] || continue
  if [[ $(cat "$name") == 79000000.r5f ]]; then cores+=("${name%/name}"); fi
done
[[ ${#cores[@]} == 1 ]] || { echo 'Expected exactly one MCU R5F (79000000.r5f).' >&2; exit 1; }
mcu=${cores[0]}
[[ $(cat "$mcu/state") == running ]] || { echo 'MCU R5F must initially be running.' >&2; exit 1; }
for ((i=1; i<=cycles; i++)); do
  printf 'stop\n' > "$mcu/state" || { echo "cycle $i: STOP FAILED" >&2; exit 1; }
  printf '%s' "$fw" > "$mcu/firmware" || { echo "cycle $i: FIRMWARE WRITE FAILED; MCU left stopped" >&2; exit 1; }
  printf 'start\n' > "$mcu/state" || { echo "cycle $i: START FAILED" >&2; exit 1; }
  ready=0
  for ((attempt=0; attempt<20; attempt++)); do
    if grep -q 'end point 14' "$trace_root/${mcu##*/}/trace0" 2>/dev/null; then ready=1; break; fi
    sleep 0.1
  done
  ((ready)) || { echo "cycle $i: firmware did not reach its receive loop" >&2; exit 1; }
  timeout 5 "$echo_tool" 0 20 >/dev/null || { echo "cycle $i: echo FAILED" >&2; exit 1; }
done
printf 'PASS %s/%s cycles with %s\n' "$cycles" "$cycles" "$fw"
