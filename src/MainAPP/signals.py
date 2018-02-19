import django.dispatch

SignalSetGPIO= django.dispatch.Signal(providing_args=["pk","Value"])
SignalToggleAVAR= django.dispatch.Signal(providing_args=["Tag","Device"])
SignalCreateMainDeviceVars= django.dispatch.Signal(providing_args=["Data"])
