import django.dispatch

SignalSetGPIO= django.dispatch.Signal(providing_args=["pk","Value"])
SignalToggleAVAR= django.dispatch.Signal(providing_args=["Tag","Device","newValue","force"])
SignalCreateMainDeviceVars= django.dispatch.Signal(providing_args=["Data"])
SignalUpdateValueMainDeviceVars= django.dispatch.Signal(providing_args=["Tag","timestamp","newValue","force"])
