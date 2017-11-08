import django.dispatch

import RemoteDevices.signal_handlers

Device_datagram_reception= django.dispatch.Signal(providing_args=["timestamp","Device","DatagramId","values"])
Device_datagram_reception.connect(RemoteDevices.signal_handlers.Device_datagram_reception_handler)

Device_datagram_exception= django.dispatch.Signal(providing_args=["DeviceName","DatagramId","HTMLCode"])
Device_datagram_exception.connect(RemoteDevices.signal_handlers.Device_datagram_exception_handler)

Device_datagram_timeout= django.dispatch.Signal(providing_args=["DeviceIP","DeviceName","DatagramId"])
Device_datagram_timeout.connect(RemoteDevices.signal_handlers.Device_datagram_timeout_handler)

Device_datagram_format_error= django.dispatch.Signal(providing_args=["DeviceName","DatagramId","values"])
Device_datagram_format_error.connect(RemoteDevices.signal_handlers.Device_datagram_format_error_handler)

DeviceName_changed= django.dispatch.Signal(providing_args=["OldDeviceName","NewDeviceName"])
DeviceName_changed.connect(RemoteDevices.signal_handlers.DeviceName_changed_handler)

Toggle_DeviceStatus= django.dispatch.Signal(providing_args=["DeviceName"])
Toggle_DeviceStatus.connect(RemoteDevices.signal_handlers.Toggle_DeviceStatus_handler)