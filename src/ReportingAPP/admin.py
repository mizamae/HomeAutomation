from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from .constants import APP_TEMPLATE_NAMESPACE
from .models import Reports,ReportItems


class ReportsAdmin(admin.ModelAdmin):
    pass

class ReportItemsAdmin(admin.ModelAdmin):
    list_display = ('Report','fromDate','toDate')
    ordering=('Report','fromDate')
    pass

admin.site.register(Reports,ReportsAdmin)
admin.site.register(ReportItems,ReportItemsAdmin)