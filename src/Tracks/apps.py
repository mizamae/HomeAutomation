from django.apps import AppConfig

import logging
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("processes")

# with this initialization we guarantee that only one process will have the input change detection configured.
# this avoids the multiple callbacks when an input changes its value as only one process will be aware of it.

from .constants import BOOTING_MSG
                
class TracksConfig(AppConfig):
    name = 'Tracks'
    verbose_name = _('Tracking manager')
    
    def ready(self):
        logger.info('Finished initializing Tracks on the process ' + str(os.getpid()))
        