import django.dispatch

import Devices.signal_handlers

Device_datagram_reception= django.dispatch.Signal(providing_args=["timestamp","Device","values"])
Device_datagram_reception.connect(Devices.signal_handlers.Device_datagram_reception_handler)

Device_datagram_exception= django.dispatch.Signal(providing_args=["Device","Datagram","Error"])
Device_datagram_exception.connect(Devices.signal_handlers.Device_datagram_exception_handler)

Device_datagram_timeout= django.dispatch.Signal(providing_args=["Device","Datagram"])
Device_datagram_timeout.connect(Devices.signal_handlers.Device_datagram_timeout_handler)

Device_datagram_format_error= django.dispatch.Signal(providing_args=["Device","Datagram","values"])
Device_datagram_format_error.connect(Devices.signal_handlers.Device_datagram_format_error_handler)

DeviceName_changed= django.dispatch.Signal(providing_args=["OldDeviceName","NewDeviceName"])
DeviceName_changed.connect(Devices.signal_handlers.DeviceName_changed_handler)

Toggle_DeviceStatus= django.dispatch.Signal(providing_args=["Device"])
Toggle_DeviceStatus.connect(Devices.signal_handlers.Toggle_DeviceStatus_handler)