#!/usr/bin/env python3
"""Read/write check for the accompanying Mo BLE Demo peripheral, via BlueZ."""
import argparse, time
import dbus
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--name', default='Mo BLE Demo', help='Advertised peripheral name')
args = parser.parse_args()
BUS = 'org.bluez'
PROPS = 'org.freedesktop.DBus.Properties'
DEVICE = 'org.bluez.Device1'
CHAR = 'org.bluez.GattCharacteristic1'
UUID = '12345678-1234-5678-1234-56789abcdef1'
bus = dbus.SystemBus()
manager = dbus.Interface(bus.get_object(BUS, '/'), 'org.freedesktop.DBus.ObjectManager')

def objects():
    return manager.GetManagedObjects()

def find():
    return [p for p, i in objects().items() if i.get(DEVICE, {}).get('Name') == args.name]
paths = find()
adapter = None
if not paths:
    adapters = [p for p, i in objects().items() if 'org.bluez.Adapter1' in i]
    if not adapters:
        raise SystemExit('No Bluetooth adapter found.')
    adapter_path = adapters[0]
    adapter = dbus.Interface(bus.get_object(BUS, adapter_path), 'org.bluez.Adapter1')
    adapter.SetDiscoveryFilter({'Transport': dbus.String('le'), 'Pattern': dbus.String(args.name)})
    adapter.StartDiscovery()
    try:
        for _ in range(30):
            time.sleep(0.5)
            paths = find()
            if paths:
                break
    finally:
        adapter.StopDiscovery()
if not paths:
    raise SystemExit('Demo peripheral not found. Start it and try again.')
if len(paths) != 1:
    raise SystemExit('Multiple peripherals have this name. Give the intended peripheral a unique name first.')
path = paths[0]
device = dbus.Interface(bus.get_object(BUS, path), DEVICE)
props = dbus.Interface(bus.get_object(BUS, path), PROPS)
was_connected = bool(props.Get(DEVICE, 'Connected'))
try:
    if not was_connected:
        device.Connect()
    for _ in range(40):
        if props.Get(DEVICE, 'ServicesResolved'):
            break
        time.sleep(0.25)
    else:
        raise SystemExit('GATT services did not resolve.')
    print('Peripheral:', args.name)
    print('LE connection: connected')
    print('GATT services: resolved')
    chars = [p for p, i in objects().items() if p.startswith(path + '/') and i.get(CHAR, {}).get('UUID') == UUID]
    if not chars:
        raise SystemExit('Demo characteristic is unavailable.')
    characteristic = dbus.Interface(bus.get_object(BUS, chars[0]), CHAR)
    print('Read:', bytes(characteristic.ReadValue({})).decode('utf-8', 'replace'))
    value = b'Mo62A BLE OK'
    characteristic.WriteValue(dbus.Array(value, signature='y'), {})
    print('Write:', value.decode())
    result = bytes(characteristic.ReadValue({}))
    print('Read back:', result.decode('utf-8', 'replace'))
    if result != value:
        raise SystemExit('FAIL: read-back mismatch')
    print('PASS: read-back matches the written value')
finally:
    if not was_connected:
        try:
            device.Disconnect()
        except dbus.DBusException:
            pass
