import pandas as pd
import numpy as np
import datetime
from utils.BBDD import getRegistersDBInstance
from .constants import DTYPE_DIGITAL,PLOTTYPE_CHOICES

def generateChart(table,fromDate,toDate,names,types,labels,plottypes,sampletime):
    
    df=pd.DataFrame()
    #df['timestamp']=[fromDate.replace(tzinfo=None),toDate.replace(tzinfo=None)]
    #df.set_index(keys='timestamp',inplace=True)
    for anio in range(fromDate.year,toDate.year+1):
        DB=getRegistersDBInstance(year=anio)
        
        chart={}
        chart['title']=table
        chart['cols']=[]
        i=0
        tempname=[]
        tempnameEmpty=[]
        vars=''
        tempStats={'number':5,'num_rows':[],'mean':[],'max':[],'min':[],'on_time':[],'off_time':[]}
        for name,type,label,plottype in zip(names,types,labels,plottypes):
            if DB.checkIfColumnExist(table=table,column=name):
                vars+='"'+str(name)+'"'+','
                if type!=DTYPE_DIGITAL:
                    tempname.append({'name':name,'label':label,'type':type,'plottype':plottype})
                else:
                    labelx=label.split('$')
                    tempname.append({'name':name,'label':labelx,'type':type,'plottype':plottype})
                
            else:
                if type!=DTYPE_DIGITAL:
                    tempnameEmpty.append({'name':name,'label':label,'type':type,'plottype':plottype})
                else:
                    labelx=label.split('$')
                    tempnameEmpty.append({'name':name,'label':labelx,'type':type,'plottype':plottype})
    
        if vars!='' and vars!='"timestamp",':
            vars=vars[:-1]
            #chart['cols'].append(tempname)    
            
            limit=10000
            sql='SELECT '+vars+' FROM "'+ table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" ORDER BY timestamp ASC LIMIT ' + str(limit)
            
            df_temp=pd.read_sql_query(sql=sql,con=DB.getConn(),index_col='timestamp')
        else:
            #chart['cols'].append(tempnameEmpty)
            df_temp=pd.DataFrame()
        
        if not df_temp.empty:
            nulls=df_temp.isnull().sum() # number of null elements per column
            rows=df_temp.shape[0]    # total number of rows
            for i,null in enumerate(nulls):
                variable=vars.split(',')[i+1]
                firstData=df_temp.iloc[0, df_temp.columns.get_loc(variable.replace('"',''))]
                if null==rows: #or firstData==None or np.isnan(firstData):  # if all the rows are null or the first row is not numeric
                    sql='SELECT timestamp,'+variable+' FROM "'+table +'" WHERE timestamp < "' + str(fromDate).split('+')[0]+ '" AND '+variable +' not null ORDER BY timestamp DESC LIMIT 1'
                    row=DB.executeTransaction(SQLstatement=sql,arg=[])
                    if row != []:
                        row=row[0][1]
                    elif not df.empty: # if df already has data
                        try: # try getting the last value from df
                            row=df.iloc[-1, df.columns.get_loc(variable.replace('"',''))]
                        except:
                            row=None
                    else:
                        row=None
                    df_temp.iloc[0, df_temp.columns.get_loc(variable.replace('"',''))]=row
                    df_temp.iloc[-1, df_temp.columns.get_loc(variable.replace('"',''))]=row
        else:
            ts = pd.to_datetime(fromDate.replace(tzinfo=None))
            values=[]
            for i,col in enumerate(df_temp.columns):
                variable=vars.split(',')[i+1]
                sql='SELECT timestamp,'+variable+' FROM "'+table +'" WHERE timestamp < "' + str(fromDate).split('+')[0]+ '" AND '+variable +' not null ORDER BY timestamp DESC LIMIT 1'
                row=DB.executeTransaction(SQLstatement=sql,arg=[])
                if row != []:
                    values.append(row[0][1])
                elif not df.empty: # if df already has data
                    try: # try getting the last value from df
                        values.append(df.iloc[-1, df.columns.get_loc(variable.replace('"',''))])
                    except:
                        values.append(None)
                else:
                    values.append(None)

            # inserts None values in the first and last rows with timestamp fromDate and toDate
            new_row = pd.DataFrame([values], columns = df_temp.columns, index=[ts])
            df_temp=pd.concat([pd.DataFrame(new_row),df_temp], ignore_index=False)
            ts = pd.to_datetime(toDate.replace(tzinfo=None))
            new_row = pd.DataFrame([values], columns = df_temp.columns, index=[ts])
            df_temp=pd.concat([pd.DataFrame(new_row),df_temp], ignore_index=False)
            
        for var in tempnameEmpty:
            df_temp[var['name']] = np.nan
        
        df=pd.concat([df_temp,df], ignore_index=False)
    
    df.sort_index(axis='index',inplace=True)
    
    chart['cols'].append(tempname + tempnameEmpty)
    
    if not df.empty:
        
        # TO FORCE THAT THE INITIAL ROW CONTAINS THE INITIAL DATE
        addedtime=pd.to_datetime(arg=df.index.values[0])-fromDate.replace(tzinfo=None)
        if addedtime>datetime.timedelta(hours=1):
            ts = pd.to_datetime(fromDate.replace(tzinfo=None))
            new_row = pd.DataFrame([df.iloc[0].values], columns = df.columns, index=[ts])
            df=pd.concat([pd.DataFrame(new_row),df], ignore_index=False)
             
        # TO FORCE THAT THE LAST ROW CONTAINS THE END DATE
        addedtime=toDate.replace(tzinfo=None)-pd.to_datetime(arg=df.index.values[-1])
        if addedtime>datetime.timedelta(hours=1):
            ts = pd.to_datetime(toDate.replace(tzinfo=None))
            row_values=df.iloc[-1].values
#             for i,element in enumerate(row_values): # this is to force Nan on missing data
#                 row_values[i]=np.nan
            new_row = pd.DataFrame([row_values], columns = df.columns, index=[ts])
            df=pd.concat([pd.DataFrame(new_row),df], ignore_index=False)
        
        # RESAMPLING DATA TO 1 MINUTE RESOLUTION AND INTERPOLATING VALUES
        df_int=df.resample('1T').fillna(method='ffill').fillna(method='bfill')
    else:
        df_int=df
        
    tempStats={'number':5,'num_rows':df.count().tolist(),'mean':[],
                'max':[None if pd.isnull(x) else x for x in df.max().tolist()],'min':[None if pd.isnull(x) else x for x in df.min().tolist()],
                'on_time':[],'off_time':[]}
    
    for col in chart['cols'][0][1:]:
        if col['type']==DTYPE_DIGITAL:
            from utils.dataMangling import dec2bin
                    
            try:
                df[col['name']]=df[col['name']].apply(func=dec2bin)
                df_int[col['name']]=df_int[col['name']].apply(func=dec2bin)
                from MainAPP.models import AdditionalCalculations
                kk=pd.DataFrame(df_int[col['name']])
                CALC=AdditionalCalculations(df=kk,key=col['name'])
                kk=CALC.duty(level=True,absoluteValue=True)
                if isinstance(kk, list):
                    for i,k in enumerate(kk):
                        if not pd.notnull(k):
                            kk[i]=None
                    tempStats['on_time'].append(kk)
                else:
                    tempStats['on_time'].append(kk if pd.notnull(kk) else None)
                kk=CALC.duty(level=False,absoluteValue=True)
                if isinstance(kk, list):
                    for i,k in enumerate(kk):
                        if not pd.notnull(k):
                            kk[i]=None
                    tempStats['off_time'].append(kk)
                else:
                    tempStats['off_time'].append(kk if pd.notnull(kk) else None)
            except KeyError:
                tempStats['on_time'].append(None)
                tempStats['off_time'].append(None)
            tempStats['mean'].append(None)
        else:
            try:
                # AN ERROR CAN OCCUR IF THE VARIABLE HAS NO VALUE ALONG THE TIMESPAN
                kk=df_int[str(col['name'])].mean()
                tempStats['mean'].append(kk if pd.notnull(kk) else None)
            except KeyError:
                tempStats['mean'].append(None)
            tempStats['on_time'].append(None)
            tempStats['off_time'].append(None)
    
    tempX2 = [x / 1000000 for x in df.index.values.tolist()]
    
    # TRANSFORMING THE NANs TO NONEs TO AVOID JSON ENCODING ISSUES
    tempData=df.where(pd.notnull(df), None).values.tolist()
    
    for row,timestamp in zip(tempData,tempX2):
        row.insert(0,timestamp)   
         
    chart['rows']=tempData
    chart['statistics']=tempStats
    
    return chart