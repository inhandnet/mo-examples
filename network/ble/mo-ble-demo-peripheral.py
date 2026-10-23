#!/usr/bin/env python3
"""Temporary BlueZ BLE echo peripheral; stop with Ctrl+C to unregister it.
Run on a second Linux computer: sudo python3 mo-ble-demo-peripheral.py BOARD_BLUETOOTH_ADDRESS
Only the selected board is authorized to pair. No Internet access is required.
"""
import sys, signal, re, time
import dbus, dbus.service, dbus.mainloop.glib
from gi.repository import GLib
BLUEZ = 'org.bluez'
PROP = 'org.freedesktop.DBus.Properties'
OM = 'org.freedesktop.DBus.ObjectManager'
SERVICE = 'org.bluez.GattService1'
CHAR = 'org.bluez.GattCharacteristic1'
ADV = 'org.bluez.LEAdvertisement1'
AGENT = 'org.bluez.Agent1'
SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'
if len(sys.argv) != 2:
    raise SystemExit('Usage: mo-ble-demo-peripheral.py BOARD_BLUETOOTH_ADDRESS')
if not re.fullmatch('(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', sys.argv[1]):
    raise SystemExit('Expected a Bluetooth address such as AA:BB:CC:DD:EE:FF')
peer = sys.argv[1].upper().replace(':', '_')
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
loop = GLib.MainLoop()

class Object(dbus.service.Object):

    def __init__(self, path, iface, props):
        self.path = path
        self.iface = iface
        self.props = props
        super().__init__(bus, path)

    @dbus.service.method(PROP, in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface):
        return self.props if iface == self.iface else {}

class Service(Object):

    def __init__(self):
        super().__init__('/org/mo/demo/service0', SERVICE, {'UUID': SERVICE_UUID, 'Primary': dbus.Boolean(True)})

class Characteristic(Object):

    def __init__(self):
        super().__init__('/org/mo/demo/service0/char0', CHAR, {'UUID': CHAR_UUID, 'Service': dbus.ObjectPath('/org/mo/demo/service0'), 'Flags': dbus.Array(['read', 'write'], signature='s')})
        self.value = b'Mo BLE ready'

    @dbus.service.method(CHAR, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        print('GATT read:', self.value.decode('utf-8', 'replace'), flush=True)
        return dbus.Array(self.value, signature='y')

    @dbus.service.method(CHAR, in_signature='aya{sv}', out_signature='')
    def WriteValue(self, value, options):
        self.value = bytes(value)
        print('GATT write:', self.value.decode('utf-8', 'replace'), flush=True)

class App(dbus.service.Object):

    def __init__(self):
        super().__init__(bus, '/org/mo/demo')
        self.objects = [Service(), Characteristic()]

    @dbus.service.method(OM, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        return {o.path: {o.iface: o.props} for o in self.objects}

class Advertisement(Object):

    def __init__(self):
        super().__init__('/org/mo/advert', ADV, {'Type': 'peripheral', 'ServiceUUIDs': dbus.Array([SERVICE_UUID], signature='s'), 'LocalName': 'Mo BLE Demo', 'Includes': dbus.Array(['tx-power'], signature='s')})

    @dbus.service.method(ADV, in_signature='', out_signature='')
    def Release(self):
        pass

class Rejected(dbus.DBusException):
    _dbus_error_name = 'org.bluez.Error.Rejected'

class Agent(dbus.service.Object):

    def __init__(self):
        super().__init__(bus, '/org/mo/agent')

    def allow(self, device):
        if not str(device).endswith('/dev_' + peer):
            raise Rejected('Not the selected test board')

    @dbus.service.method(AGENT, in_signature='', out_signature='')
    def Release(self):
        pass

    @dbus.service.method(AGENT, in_signature='o', out_signature='')
    def RequestAuthorization(self, device):
        self.allow(device)

    @dbus.service.method(AGENT, in_signature='ou', out_signature='')
    def RequestConfirmation(self, device, passkey):
        self.allow(device)

    @dbus.service.method(AGENT, in_signature='os', out_signature='')
    def AuthorizeService(self, device, uuid):
        self.allow(device)

    @dbus.service.method(AGENT, in_signature='', out_signature='')
    def Cancel(self):
        pass
objects = dbus.Interface(bus.get_object(BLUEZ, '/'), OM).GetManagedObjects()
adapters = [p for p, ifs in objects.items() if 'org.bluez.GattManager1' in ifs and 'org.bluez.LEAdvertisingManager1' in ifs]
if not adapters:
    raise SystemExit('No adapter supports both GATT and LE advertising. Enable Bluetooth and try again.')
adapter = adapters[0]
obj = bus.get_object(BLUEZ, adapter)
props = dbus.Interface(obj, PROP)
old = {k: props.Get('org.bluez.Adapter1', k) for k in ('Alias', 'Pairable', 'Powered')}
app = App()
adv = Advertisement()
agent = Agent()
mgr = dbus.Interface(obj, 'org.bluez.GattManager1')
am = dbus.Interface(obj, 'org.bluez.LEAdvertisingManager1')
agm = dbus.Interface(bus.get_object(BLUEZ, '/org/bluez'), 'org.bluez.AgentManager1')
error_state = []

def failed(e):
    error_state.append(str(e))
    print('BLE demo error:', e, flush=True)
    loop.quit()

def registered():
    print('GATT application ready', flush=True)
    am.RegisterAdvertisement('/org/mo/advert', {}, reply_handler=lambda: print('Advertising Mo BLE Demo', flush=True), error_handler=failed)
signal.signal(signal.SIGINT, lambda *_: loop.quit())
signal.signal(signal.SIGTERM, lambda *_: loop.quit())
try:
    props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(True))
    props.Set('org.bluez.Adapter1', 'Alias', 'Mo BLE Demo')
    props.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(True))
    agm.RegisterAgent('/org/mo/agent', 'NoInputNoOutput')
    agm.RequestDefaultAgent('/org/mo/agent')
    mgr.RegisterApplication('/org/mo/demo', {}, reply_handler=registered, error_handler=failed)
    loop.run()
finally:
    for manager, method, path in [(am, 'UnregisterAdvertisement', '/org/mo/advert'), (mgr, 'UnregisterApplication', '/org/mo/demo'), (agm, 'UnregisterAgent', '/org/mo/agent')]:
        try:
            getattr(manager, method)(path)
        except dbus.DBusException:
            pass
    for k, v in old.items():
        for attempt in range(5):
            try:
                if props.Get('org.bluez.Adapter1', k) != v:
                    props.Set('org.bluez.Adapter1', k, v)
                break
            except dbus.DBusException as e:
                if attempt == 4:
                    error_state.append('Could not restore ' + k)
                    print('Could not restore', k, str(e), file=sys.stderr)
                time.sleep(0.2)
    print('Demo stopped.' if error_state else 'Demo stopped; adapter settings restored.', flush=True)
if error_state:
    raise SystemExit(1)
