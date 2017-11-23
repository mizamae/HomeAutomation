from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from Events.models import EventModel

class EventModelAdmin(admin.ModelAdmin):
    
    list_display = ('Timestamp','Severity','Text')
    ordering=('Severity','Timestamp')
    actions=['markAsRead']
    
        
    def markAsRead(self,request, queryset):
        EVs=queryset
        if len(EVs)>0:
            for EV in EVs:
                EV.IsRead=True
                EV.save()
    markAsRead.short_description = _("Mark as read")
    

admin.site.register(EventModel,EventModelAdmin)