from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import time

import Master_GPIOs.models

# this generates the IO model the first time this module is included.

@user_passes_test(lambda u: u.is_superuser)
def master_gpios(request,number=None,reset=False):
    GPIOs=Master_GPIOs.models.IOmodel.objects.all()
    return render(request, 'GPIOs.html', {'GPIOs': GPIOs})

