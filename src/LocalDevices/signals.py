import django.dispatch

import LocalDevices.signal_handlers

Devices_datagram_reception= django.dispatch.Signal(providing_args=["Device","values"])
Devices_datagram_reception.connect(LocalDevices.signal_handlers.datagram_reception_handler)

Devices_datagram_exception= django.dispatch.Signal(providing_args=["DeviceName","Error"])
Devices_datagram_exception.connect(LocalDevices.signal_handlers.datagram_exception_handler)

Toggle_DeviceStatus= django.dispatch.Signal(providing_args=["DeviceName"])
Toggle_DeviceStatus.connect(LocalDevices.signal_handlers.Toggle_DeviceStatus_handler)

DeviceName_changed= django.dispatch.Signal(providing_args=["OldDeviceName","NewDeviceName"])
DeviceName_changed.connect(LocalDevices.signal_handlers.DeviceName_changed_handler)