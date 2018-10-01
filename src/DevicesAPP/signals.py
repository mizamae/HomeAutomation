import django.dispatch

SignalVariableValueUpdated= django.dispatch.Signal(providing_args=["timestamp","Tags","Values","Types"])
SignalNewDataFromDevice= django.dispatch.Signal(providing_args=["DV","DG",])