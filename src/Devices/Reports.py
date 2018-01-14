import pandas as pd
import numpy as np

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
    timezoneUTCoffset=datetime.datetime.now().hour-timezone.now().hour
    reportData={'reportTitle':ReportTitle}#,'fromDate':dateIni,'toDate':dateEnd}
    #logger.info('reportDate: ' + str(reportData))
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
            try:
                bitPos=variables['bitPos']
            except:
                bitPos=None
            try:
                type=variables['type']
            except:
                type='analog'
            try:
                extrapolate=variables['extrapolate']
            except:
                extrapolate=''
            try:
                plottype=variables['plottype']
            except:
                plottype=None
                
            if label==None:
                if type=='analog':
                    temp['cols'].insert(0,{'table':table,'name':name,'label':name,'type':type,'bitPos':None,'extrapolate':extrapolate,'plottype':plottype})   
                else:
                    temp['cols'].append({'table':table,'name':name,'label':name,'type':type,'bitPos':None,'extrapolate':extrapolate,'plottype':plottype})   
            else:
                if type=='analog':
                    temp['cols'].insert(0,{'table':table,'name':name,'label':label,'type':type,'bitPos':bitPos,'extrapolate':extrapolate,'plottype':plottype}) 
                else:
                    temp['cols'].append({'table':table,'name':name,'label':label,'type':type,'bitPos':bitPos,'extrapolate':extrapolate,'plottype':plottype}) 
                    
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
                    sql='SELECT timestamp,"'+variable+'" FROM "'+table +'" WHERE timestamp < "' + str(fromDate).split('+')[0]+ '" AND "'+variable +'" not null ORDER BY timestamp DESC LIMIT 1'
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
        resultDF=pd.DataFrame()
        resultDF_interpolated=pd.DataFrame()
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

            sql='SELECT timestamp,"'+variable+'" FROM "'+table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" AND "'+variable +'" not null ORDER BY timestamp ASC LIMIT ' + str(limit)
            
            df=pd.read_sql_query(sql=sql,con=AppDB.registersDB.conn,index_col='timestamp')
            
            if not df.empty:
                
                # TO FORCE THAT THE INITIAL ROW CONTAINS THE INITIAL DATE
                
                addedtime=pd.to_datetime(arg=df.index.values[0])-dateIni.replace(tzinfo=None)
                if addedtime>datetime.timedelta(minutes=1):
                    ts = pd.to_datetime(dateIni.replace(tzinfo=None))
                    new_row = pd.DataFrame([[df[variable].iloc[0]]], columns = [variable], index=[ts])
                    df=pd.concat([pd.DataFrame(new_row),df], ignore_index=False)
                    
                # TO FORCE THAT THE LAST ROW CONTAINS THE END DATE
                
                addedtime=dateEnd.replace(tzinfo=None)-pd.to_datetime(arg=df.index.values[-1])
                if addedtime>datetime.timedelta(minutes=1):
                    ts = pd.to_datetime(dateEnd.replace(tzinfo=None))
                    new_row = pd.DataFrame([[df[variable].iloc[-1]]], columns = [variable], index=[ts])
                    df=pd.concat([df,pd.DataFrame(new_row)], ignore_index=False)
            else:
                sql='SELECT timestamp,"'+variable+'" FROM "'+table +'" WHERE timestamp < "' + str(fromDate).split('+')[0]+ '" AND "'+variable +'" not null ORDER BY timestamp DESC LIMIT 1'
                df=pd.read_sql_query(sql=sql,con=AppDB.registersDB.conn,index_col='timestamp')
                if not df.empty:
                    values=np.concatenate([df.values,df.values])
                    ts_ini = pd.to_datetime(dateIni.replace(tzinfo=None))
                    ts_end = pd.to_datetime(dateEnd.replace(tzinfo=None))
                    df = pd.DataFrame(data=values,index=[ts_ini,ts_end],columns=df.columns)
                
            resultDF = pd.concat([resultDF, df], axis=1, join='outer')
            
            if not df.empty:
                # RESAMPLING DATA TO 1 MINUTE RESOLUTION AND INTERPOLATING VALUES
                df_resampled=df.resample('1T').mean()
                if extrapolate=='keepPrevious':
                    df_interpolated=df_resampled.interpolate(method='zero')
                else:
                    df_interpolated=df_resampled.interpolate(method='linear')
                    
                resultDF_interpolated = pd.concat([resultDF_interpolated, df_interpolated], axis=1, join='outer')
                                
                if datatype!='digital':
                    tempStats['mean'][columnNumber]=resultDF_interpolated[variable].mean()
                    tempStats['on_time'][columnNumber]=None
                    tempStats['off_time'][columnNumber]=None
                    tempStats['max'][columnNumber]=resultDF[variable].max()
                    tempStats['min'][columnNumber]=resultDF[variable].min()
                else:
                    from HomeAutomation.models import AdditionalCalculationsModel
                    kk=pd.DataFrame(resultDF[variable])
                    CALC=AdditionalCalculationsModel(df=kk,key=variable)
                    tempStats['mean'][columnNumber]=None
                    tempStats['on_time'][columnNumber]=CALC.duty(level=True,absoluteValue=True)
                    tempStats['off_time'][columnNumber]=CALC.duty(level=False,absoluteValue=True)
                    tempStats['max'][columnNumber]=None
                    tempStats['min'][columnNumber]=None
            else:
                tempStats['mean'][columnNumber]=None
                tempStats['on_time'][columnNumber]=None
                tempStats['off_time'][columnNumber]=None
                tempStats['max'][columnNumber]=None
                tempStats['min'][columnNumber]=None
                
        # AGGREGATING DATA ACCORDING TO REQUIREMENT
        if aggregation==1: #'hourly':
            resultDF = resultDF.resample('H').mean()
            resultDF=resultDF.tshift(-timezoneUTCoffset,freq='H')
        elif aggregation==2: #'daily':
            resultDF = resultDF.resample('D').mean()
            resultDF=resultDF.tshift(-timezoneUTCoffset,freq='H')
        
        tempX2 = [x / 1000000 for x in resultDF.index.values.tolist()]
        # TRANSFORMING THE NANs TO NONEs TO AVOID JSON ENCODING ISSUES
        tempY=resultDF.where(pd.notnull(resultDF), None).values.tolist()
            
        chart['rows']={'x_axis':tempX2,'y_axis':tempY}  
        chart['statistics']=tempStats
        
    reportData['charts']=charts
    return reportData
