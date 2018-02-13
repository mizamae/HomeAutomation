import django.dispatch

SignalSetGPIO= django.dispatch.Signal(providing_args=["pk","Value"])


