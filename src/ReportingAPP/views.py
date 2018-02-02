from django.conf import settings
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import HttpResponse,HttpResponseNotFound,HttpResponseRedirect
from django.shortcuts import render, render_to_response,get_object_or_404,redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import generic

import logging
logger = logging.getLogger("project")

from . import forms
from . import models

from .constants import APP_TEMPLATE_NAMESPACE

def home(request):
    if request.method == 'POST': # the form has been submited
        return render(request, APP_TEMPLATE_NAMESPACE+'/home.html') 
    else:
        return render(request, APP_TEMPLATE_NAMESPACE+'/home.html') 

def modelSplitter(model):
    if model=='reports':
        Header1 = models.Reports._meta.verbose_name.title()
        Model=models.Reports
        FormModel=forms.ReportsForm
        FormKwargs={'action':'add'}
        message=models.Reports._meta.verbose_name.title()+ str(_(' saved OK'))
        lastAction='add'
    elif model=='reportitems':
        Header1 = models.ReportItems._meta.verbose_name.title()
        Model=models.ReportItems
        FormModel=None
        FormKwargs={'action':'add'}
        message=models.ReportItems._meta.verbose_name.title()+ str(_(' saved OK'))
        lastAction='add'
    else:
        return None
    return {'Header1':Header1,'Model':Model,'FormModel':FormModel,'FormKwargs':FormKwargs,'message':message,'lastAction':lastAction}

def checkUserPermissions(request,action,model):
    # performing some custom type of logic
    if not request.user.has_perm('DevicesAPP.'+action+'_'+model):
        return False
    else:
        return True
    
def add(request,number=0):
    
    applicationDBs=DevicesAPP.BBDD.DIY4dot0_Databases(registerDBPath=REGISTERS_DB_PATH) 
    form_data={'ReportTitle':'','Periodicity':2,'DataAggregation':0}
    form=forms.ReportForm(form_data)  
    if request.method == 'POST':
        json_data=request.body.decode('utf-8')
        #logger.info('Received the post! - '+ json_data)
        data = json.loads(json_data)
        #logger.info('JSON loaded OK')
        ReportTitle=str(data[0]['report_title'])
        Periodicity=data[0]['Periodicity']
        DataAggregation=data[0]['DataAggregation']
        ReportContentJSON=json_data
        #logger.debug('Report content: ' + ReportContentJSON)             
        form_data={'ReportTitle':ReportTitle,'Periodicity':Periodicity,'DataAggregation':DataAggregation,'ReportContentJSON':ReportContentJSON}
        form=DevicesAPP.forms.ReportForm(form_data)
        #logger.info('Trying to create a report with the title ' + ReportTitle) 
        if form.is_valid(): 
            #logger.info('Form is valid!')
            REP=DevicesAPP.models.ReportModel.objects.create_Report(ReportTitle=ReportTitle,Periodicity=Periodicity,DataAggregation=DataAggregation,ReportContentJSON=ReportContentJSON)
            
            #applicationDBs.devicesDB.insert_row(SQL_statement=applicationDBs.devicesDB.SQLinsertReport_statement,row_values=(ReportTitle,ReportCode,ReportContentJSON))
            return HttpResponse(json.dumps({'Confirmation': 'OK'})) 
        else:
            logger.error('Form error ' + str(form.errors))
            return HttpResponse(json.dumps({'Error': form.errors})) 
    else:
        info=DevicesAPP.models.getAllVariables()
        #logger.debug(info)       
        return render(request, APP_TEMPLATE_NAMESPACE+'/reportconfigurator.html', {'Form':form,
                                                                                   'data': json.dumps(info)})    
    
    return render(request, APP_TEMPLATE_NAMESPACE+'/reportconfigurator.html', {'Form':form,
                                                                               'data': json.dumps({'Error':'Database is not reachable'})})    

def preview(request,title):
    RP=models.Reports.objects.get(Title=title)
    ReportData,fromDate,toDate=RP.getReport()
    ReportItem=models.ReportItems(Report=RP,fromDate=fromDate,toDate=toDate,data=json.dumps(ReportData))
    return render(request, APP_TEMPLATE_NAMESPACE+'/reportTemplate.html',{'reportTitle':ReportItem.Report.ReportTitle,
                                                        'fromDate':ReportItem.fromDate,
                                                        'toDate':ReportItem.toDate,
                                                        'reportData':ReportItem.data})

def view(request,model,pk):
    return HttpResponseNotFound('<h1>No Page Here</h1>')

def viewList(request,model):
    if not checkUserPermissions(request=request,action='view',model=model):
        return HttpResponseRedirect(reverse('accounts:login'))
    
    data=modelSplitter(model=model)
    if data==None:
        return HttpResponseNotFound('<h1>No Page Here</h1>') 
    else:
        Header1=str(_('List of ')) +data['Header1']
        Model=data['Model']
        FormModel=data['FormModel']
        message=data['message']
        lastAction=data['lastAction']
    
    if request.method == 'POST': # the form has been submited
        return HttpResponseNotFound('<h1>No Page Here</h1>') 
    else:
        if Model == models.Reports:
            RPs=Model.objects.all()
            numrows=RPs.count()
            message_norows=str(_('There are no ')) + data['Header1'] +str(_(' registered.'))
            return render(request, APP_TEMPLATE_NAMESPACE+'/showReports.html',{'Header1':Header1,
                                                                            'numrows_table1':numrows,
                                                                            'message_norows1':message_norows,
                                                                            'rows_table1':RPs
                                                                            })
        elif Model == models.ReportItems:
            RIs=Model.objects.all()
            elements=[]
            reportTitles=[]
            for Item in RIs:
                if not Item.Report.Title in reportTitles:
                    reportTitles.append(Item.Report.Title)
            for Item in RIs:
                elements.append(Item)
            numrows=RIs.count()
            message_norows=str(_('There are no ')) + data['Header1'] +str(_(' generated.'))
            return render(request, APP_TEMPLATE_NAMESPACE+'/showReportItems.html',{'Header1':Header1,
                                                                            'numrows_table1':numrows,
                                                                            'reportTitles':reportTitles,
                                                                            'items':elements,
                                                                            'message_norows1':message_norows,
                                                                            })
        else:
            return HttpResponseNotFound('<h1>No Page Here for Model '+str(model)+'</h1>') 

def delete(request,model,pk):
    return HttpResponseNotFound('<h1>No Page Here</h1>')
