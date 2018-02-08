import django.dispatch

import MainAPP.signal_handlers

SignalAutomationVariablesValueUpdated= django.dispatch.Signal(providing_args=["timestamp","Tags","Values"])
SignalAutomationVariablesValueUpdated.connect(MainAPP.signal_handlers.AutomationVariablesValueUpdated_handler)

