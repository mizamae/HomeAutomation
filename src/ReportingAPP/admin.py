from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from .constants import APP_TEMPLATE_NAMESPACE
from .models import ReportModel,ReportItems


class ReportModelAdmin(admin.ModelAdmin):
    pass

class ReportItemsModelAdmin(admin.ModelAdmin):
    list_display = ('Report','fromDate','toDate')
    ordering=('Report','fromDate')
    pass

admin.site.register(ReportModel,ReportModelAdmin)
admin.site.register(ReportItems,ReportItemsModelAdmin)