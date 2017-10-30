import django.dispatch
import Master_GPIOs.signal_handlers

OUT_toggle_request = django.dispatch.Signal(providing_args=["number",])
OUT_toggle_request.connect(Master_GPIOs.signal_handlers.OUT_toggle_request_handler)

IN_change_notification = django.dispatch.Signal(providing_args=["number","value"])
IN_change_notification.connect(Master_GPIOs.signal_handlers.IN_change_notification_handler)

