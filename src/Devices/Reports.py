import json
import logging
from tzlocal import get_localzone
from django.utils import timezone
import datetime
import Devices.BBDD
import Devices.GlobalVars
import Devices.models

logger = logging.getLogger("project")

def get_report(reporttitle,fromDate,toDate,aggregation):
    AppDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
    Report=Devices.models.ReportModel.objects.get(ReportTitle=reporttitle)
    jsonData=Report.ReportContentJSON.replace("'",'')
    #Reports.print('JSON downloaded '+jsonData) 
    data = json.loads(jsonData)
    #print('JSON parsed '+str(data)) 
    #[{'report_title': 'Final'}, [{'chart_title': 'Grafico 1'}, {'table': 'My_bedroom_data2', 'name': 'STATUS_bits', 'bitPos': '0', 'label': 'Alarm 0'}, {'table': 'My_bedroom_data2', 'name': 'STATUS_bits', 'bitPos': '1', 'label': 'Alarm 1'}, {'table': 'My_bedroom_data2', 'name': 'STATUS_bits', 'bitPos': '2', 'label': 'Alarm 2'}], [{'chart_title': 'Grafico 2'}, {'table': 'My_bedroom_data2', 'name': 'T_centdeg', 'bitPos': None, 'label': None}, {'table': 'My_bedroom_data2', 'name': 'RH_percent', 'bitPos': None, 'label': None}, {'table': 'My_bedroom_data2', 'name': 'DewPoint_centdeg', 'bitPos': None, 'label': None}]]
    ReportTitle=data[0]['report_title']
    #Reports.GlobalVars.print('ReportTitle '+str(ReportTitle)) 
    
    #del data[0] # to delete the report title
    charts=[]   # variable to capture all the graphs in the report
    local_tz=get_localzone()
    
    dateIni= fromDate-fromDate.utcoffset()
    dateEnd= toDate-toDate.utcoffset()
    reportData={'reportTitle':ReportTitle}#,'fromDate':dateIni,'toDate':dateEnd}
    logger.info('reportDate: ' + str(reportData))
    #fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Reports.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}
    queries={}
    
    for plot in data[1:]: 
        #Reports.print('Plot '+str(plot)) 
        temp={}
        temp['chart_title']=plot[0]['chart_title']
        temp['cols']=[]     #{'label': 'timestamp', 'type': 'datetime'}, {'label': 'Alarm 0', 'type': 'number', 'bitPos': '0'},{'label': 'T_centdeg', 'type': 'number', 'bitPos': None}
        temp['rows']=[]         
        for variables in plot[1:]:  
#Plot: [{'chart_title': 'Grafico 1'}, {'table': 'My_bedroom_data2', 'name': 'STATUS_bits', 'bitPos': '0', 'label': 'Alarm 0'}, {'table': 'My_bedroom_data2', 'name': 'STATUS_bits', 'bitPos': '1', 'label': 'Alarm 1'}, {'table': 'My_bedroom_data2', 'name': 'STATUS_bits', 'bitPos': '2', 'label': 'Alarm 2'}]             
            table=variables['table']
            name=variables['name']
            label=variables['label']
            bitPos=variables['bitPos']
            try:
                type=variables['type']
            except:
                type='analog'
            try:
                extrapolate=variables['extrapolate']
            except:
                extrapolate=''
            if label==None:
                if type=='analog':
                    temp['cols'].insert(0,{'table':table,'name':name,'label':name,'type':type,'bitPos':None,'extrapolate':extrapolate})   
                else:
                    temp['cols'].append({'table':table,'name':name,'label':name,'type':type,'bitPos':None,'extrapolate':extrapolate})   
            else:
                if type=='analog':
                    temp['cols'].insert(0,{'table':table,'name':name,'label':label,'type':type,'bitPos':bitPos,'extrapolate':extrapolate}) 
                else:
                    temp['cols'].append({'table':table,'name':name,'label':label,'type':type,'bitPos':bitPos,'extrapolate':extrapolate}) 
                    
        #Reports.print('temp '+str(temp)) 
        charts.append(temp)
    #logger.info('Charts: '+str(charts))  
    #Charts: [{'chart_title': 'Temperatura', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'Temperature_degC', 'label': 'Temperature_degC', 'type': 'number', 'bitPos': None}, {'table': 'Ambiente en salon_data', 'name': 'Heat Index_degC', 'label': 'Heat Index_degC', 'type': 'number', 'bitPos': None}], 'rows': []}, 
            #{'chart_title': 'Humedad', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'RH_%', 'label': 'RH_%', 'type': 'number', 'bitPos': None}], 'rows': []}]

    frames=[]
    
    for chart in charts:      
        cols=chart['cols']
        tempStats={'number':5,'num_rows':0,'mean':[],'max':[],'min':[],'on_time':[],'off_time':[]}
        tempX=[]
        tempX2=[]
        tempY=[]
        newRow=[]   
        firstRow=[]
        actualXValue=0
        localdate = fromDate
        localdate=localdate+localdate.utcoffset()
        fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}
        #tempX.append(localdate)
        #tempX2.append(fecha)
        
        for col in cols:
            try:
                extrapolate=col['extrapolate']
                datatype=col['type']
            except:
                extrapolate=''
                datatype=''
            
            variable=col['name']
            table=col['table']
            if aggregation!=0 and extrapolate!='keepPrevious':
                firstRow.append(0)
            else:
                if extrapolate=='keepPrevious':
                    sql='SELECT timestamp,"'+variable+'" FROM "'+table +'" WHERE timestamp < "' + str(fromDate).split('+')[0]+ '" ORDER BY timestamp DESC LIMIT 1'
                    row=AppDB.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
                    if row != None:
                        firstRow.append(row[1])
                    else:
                        firstRow.append(None)
                else:
                    firstRow.append(None)
                    
            newRow.append(None)
                    
            tempStats['mean'].append(0)
            tempStats['max'].append(-100000)
            tempStats['min'].append(100000)
            tempStats['on_time'].append(0)
            tempStats['off_time'].append(0)
        #tempY.append(newRow[:])
        num_items=0 # counts the number of items aggregated in each variable
        for columnNumber,col in enumerate(cols):
            tempStats['num_rows']=0
            table=col['table']
            variable=col['name']
                
            bitPos=col['bitPos']
            
            try:
                extrapolate=col['extrapolate']
                datatype=col['type']
            except:
                extrapolate=''
                datatype=''
            limit=10000
                    
            #sql='SELECT timestamp,"'+variable+'" FROM "'+table +'" ORDER BY timestamp DESC LIMIT '+str(limit)
            sql='SELECT timestamp,"'+variable+'" FROM "'+table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" ORDER BY timestamp ASC LIMIT ' + str(limit)
            #logger.info(str(sql))
            data_rows=AppDB.registersDB.retrieve_from_table(sql=sql,single=False,values=(None,))
            #logger.info(str(data_rows))
            
            i=0
            j=0
            tempData=[]
            isFirstRow=True
            if len(data_rows):
                for row in data_rows:
                    tempStats['num_rows']+=1
                    match=False # checks if the x-axis data coincide
                    localdate = local_tz.localize(row[0])
                    localdate=localdate+localdate.utcoffset()-datetime.timedelta(microseconds=localdate.microsecond) 
                    if datatype!='digital':
                        if aggregation==1: #'hourly':
                            localdate=localdate-datetime.timedelta(minutes=localdate.minute)+datetime.timedelta(minutes=30)-datetime.timedelta(seconds=localdate.second)-datetime.timedelta(microseconds=localdate.microsecond)
                            if localdate!=actualXValue:
                                actualXValue=localdate
                                num_items=0
                        elif aggregation==2: #'daily':
                            localdate=localdate-datetime.timedelta(hours=localdate.hours)+datetime.timedelta(hours=12)-datetime.timedelta(minutes=localdate.minute)-datetime.timedelta(seconds=localdate.second)-datetime.timedelta(microseconds=localdate.microsecond)
                            if localdate!=actualXValue:
                                actualXValue=localdate
                                num_items=0                
                        
                    fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}            
                    if isFirstRow==False:
                        sampletime=row[0]-prevRow[0]
                        
                    for data in row[1:]:
                        if aggregation!=0 and (data==None or data==''):
                            data=0
                        if data!=None:
                            if bitPos!=None or datatype=='digital':
                                data= 1 if (data & (1<<int(bitPos)))>0 else 0
                                if isFirstRow==False:
                                    try:
                                        tempStats['on_time'][columnNumber]=0
                                        tempStats['off_time'][columnNumber]=0
                                    except IndexError:
                                        tempStats['on_time'].append(0)
                                        tempStats['off_time'].append(0)
                            else:
                                try:
                                    tempStats['mean'][columnNumber]+=(data-tempStats['mean'][columnNumber])/tempStats['num_rows'] # moving average
                                    if data>tempStats['max'][columnNumber]:
                                        tempStats['max'][columnNumber]=data
                                    if data<tempStats['min'][columnNumber]:
                                        tempStats['min'][columnNumber]=data
                                except IndexError: # this can happen when some variables are added to a datagram and want to show on a same plot the previous and the new datagram (with added variables)
                                    tempStats['mean'].append(data)
                                    tempStats['max'].append(data)
                                    tempStats['min'].append(data)
                                
                        if len(tempX)>0:
                            for i, x in enumerate(tempX):
                                if x==localdate:
                                    match=True
                                    break
                                elif x>localdate:
                                    break
                            if match:
                                if data!=None:
                                    num_items+=1
                                if data!=None and tempY[i][columnNumber]!=None and aggregation!=0:
                                    tempY[i][columnNumber]+=(data-tempY[i][columnNumber])/num_items
                                else:
                                    tempY[i][columnNumber]=data
                                
                            elif i>0 and x>localdate:
                                num_items+=1
                                tempY.insert(i,newRow[:])
                                tempY[i][columnNumber]=data
                                tempX.insert(i,localdate)
                                tempX2.insert(i,fecha)
                            else:
                                num_items+=1
                                tempY.append(newRow[:])
                                tempY[-1][columnNumber]=data
                                tempX.append(localdate)
                                tempX2.append(fecha)
                        else:
                            num_items+=1
                            tempX.append(localdate)
                            tempX2.append(fecha)
                            tempY.append(newRow[:])
                            tempY[-1][columnNumber]=data
                        
                    isFirstRow=False
                    prevRow=row
            else:
                sql='SELECT timestamp,"'+variable+'" FROM "'+table +'" WHERE timestamp < "' + str(fromDate).split('+')[0]+ '" ORDER BY timestamp DESC LIMIT 1'
                row=AppDB.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
                if row != None:
                    if extrapolate=='keepPrevious':
                        data=row[1]
                        newRow[columnNumber]=data
                        if len(tempX)>0:
                            for i, x in enumerate(tempX):
                                tempY[i][columnNumber]=data
                        else:
                            localdate = timezone.localtime(dateIni)
                            localdate=localdate-datetime.timedelta(microseconds=localdate.microsecond)
                            tempX.insert(0,localdate)
                            fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}  
                            tempX2.insert(0,fecha)
                            value=newRow[:]
                            tempY.insert(0,value)
                            localdate = timezone.localtime(dateEnd)
                            localdate=localdate-datetime.timedelta(microseconds=localdate.microsecond)
                            tempX.append(localdate)
                            fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}  
                            tempX2.append(fecha)
                            tempY.append(value)
                    else:
                        newRow[columnNumber]=None
                        if len(tempX)>0:
                            for i, x in enumerate(tempX):
                                tempY[i][columnNumber]=None
                        else:
                            localdate = timezone.localtime(dateIni)
                            localdate=localdate-datetime.timedelta(microseconds=localdate.microsecond)
                            tempX.insert(0,localdate)
                            fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}  
                            tempX2.insert(0,fecha)
                            value=newRow[:]
                            tempY.insert(0,value)
                            localdate = timezone.localtime(dateEnd)
                            localdate=localdate-datetime.timedelta(microseconds=localdate.microsecond)
                            tempX.append(localdate)
                            fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}  
                            tempX2.append(fecha)
                            tempY.append(value)
        
        logger.info('chart: ' + chart['chart_title'])
        for columnNumber,col in enumerate(cols):
            try:
                extrapolate=col['extrapolate']
            except:
                extrapolate=''
            if extrapolate=='keepPrevious':
                Previous=tempY[0][columnNumber]
                if Previous==None:
                    Previous=0
                for row in tempY:
                    if row[columnNumber]==None:
                        row[columnNumber]=Previous
                    else:
                        Previous=row[columnNumber]
            try:
                type=col['type']
            except: 
                type=''
            if type=='digital':
                previousDate=tempX[0]
                for date,data in zip(tempX,tempY):
                    if data[columnNumber]!=None:
                        sampletime=date-previousDate
                        tempStats['on_time'][columnNumber]+=data[columnNumber]*(sampletime.days*86400+sampletime.seconds)
                        tempStats['off_time'][columnNumber]+=(not data[columnNumber])*(sampletime.days*86400+sampletime.seconds)
                    previousDate=date
                        
            
        localdate = timezone.localtime(dateIni)
        localdate=localdate-datetime.timedelta(microseconds=localdate.microsecond)
        addedtime=tempX[0]-localdate
        if addedtime>datetime.timedelta(minutes=30):
            tempX.insert(0,localdate)
            fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}  
            tempX2.insert(0,fecha)
            value=firstRow[:]
            tempY.insert(0,value)
            for i,data in enumerate(value):
                if data!=None:
                    tempStats['on_time'][i]+=data*(addedtime.days*86400+addedtime.seconds)
                    tempStats['off_time'][i]+=(not data)*(addedtime.days*86400+addedtime.seconds)
        localdate = timezone.localtime(dateEnd)
        localdate=localdate-datetime.timedelta(microseconds=localdate.microsecond)
        addedtime=localdate-tempX[-1]
        if addedtime>datetime.timedelta(minutes=30):
            tempX.append(localdate)
            fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}  
            tempX2.append(fecha)
            value=tempY[-1]
            tempY.append(value)
            for i,data in enumerate(value):
                if data!=None:
                    tempStats['on_time'][i]+=data*(addedtime.days*86400+addedtime.seconds)
                    tempStats['off_time'][i]+=(not data)*(addedtime.days*86400+addedtime.seconds)

            
        chart['rows']={'x_axis':tempX2,'y_axis':tempY}  
        chart['statistics']=tempStats
        
    reportData['charts']=charts
    return reportData
    
                   