import datetime
from os.path import dirname, join, exists

from django.utils import timezone
from django.test import TestCase,Client
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from tzlocal import get_localzone

import webtest

from .constants import DTYPE_DIGITAL,DTYPE_FLOAT,DTYPE_INTEGER,APP_TEMPLATE_NAMESPACE, \
                    FORM_FIRST_RENDER_MSG,FORM_ISVALID_MSG,FORM_ISNOTVALID_MSG,SCAN_DEVICENOFOUND, \
                    SCAN_DEVICEFOUND,TESTS_USER_AGENT,LOCAL_CONNECTION,LINE_PLOT,SPLINE_PLOT,COLUMN_PLOT,AREA_PLOT,\
                    DG_SYNCHRONOUS,DG_ASYNCHRONOUS,\
                    GPIO_DIRECTION_CHOICES,GPIO_OUTPUT,GPIO_INPUT,GPIO_SENSOR,GPIOVALUE_CHOICES,GPIO_HIGH,GPIO_LOW
                    
from .models import Devices,DeviceTypes,Datagrams,DatagramItems,ItemOrdering,MasterGPIOs,MainDeviceVars
from .apps import DevicesAppException
from .forms import DevicesForm,DatagramCustomLabelsForm

# CREATES A BACKUP OF THE REGISTERS DB
from utils.BBDD import backupRegistersDB
backupRegistersDB()

P1=None
P2=None

MainDeviceVarDict={'Label':'Test Main Var','Value':23,'DataType':DTYPE_DIGITAL,'PlotType':LINE_PLOT,'Units':'H','UserEditable':True}
MasterGPIODict={'Pin':17,'Label':'Test Output 1','Direction':GPIO_OUTPUT,'Value':GPIO_HIGH}
DatagramItemDict={'Tag':'Digital Item 1','DataType':DTYPE_DIGITAL,'PlotType':SPLINE_PLOT,'Units':''}
ItemOrderingDict={'DG':'','ITM':'','Order':0}
DatagramDict={'Identifier':'Datagram','Code':0,'Type':DG_SYNCHRONOUS,'DVT':0}

DeviceDict={
                'Name' : 'Test Device 2',
                'IO' : None,
                'Code' : 2,
                'IP' : '127.0.0.1',
                'DVT' : 0,
                'State': 0,
                'Sampletime':10,
                'RTsampletime':10,
                'LastUpdated': None,
                'NextUpdate': None,
                'Connected' : False,  
                'CustomLabels' : '',
                'Error':'',
            }

DevicetypeDict={
                'Code' : 'TestType',
                'Description' : 'Test Description',
                'MinSampletime':60,
                'Connection' : LOCAL_CONNECTION,
            }


def editDict(keys,newValues,Dictionary=DeviceDict):
    import copy
    newDict= copy.deepcopy(Dictionary)
    for key,newValue in zip(keys,newValues):
        if not key in newDict:
            raise ValueError('The key ' + key+ ' is not in dictionary DeviceDict')
        newDict[key]=newValue
    return newDict


def startApache():
    global P1
    import subprocess,time
    P1=subprocess.Popen(r'c:\xampp\apache_start.bat')
    time.sleep(2)
 
def stopApache():
    global P2
    import subprocess,time
    P2=subprocess.Popen(r'c:\xampp\apache_stop.bat')
    time.sleep(2)

def setupPowersXML(code,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0'):
    file=join(DevicesModelTests.ApacheHTTPpath, 'powers.xml')
    import fileinput

    with fileinput.FileInput(files=file, inplace=True, backup='.bak') as file:
        for line in file:
            print(line.replace('#code#', str(code))
                  .replace('#dId#', str(datagramId))
                  .replace('#status#', str(status))
                  .replace('#p#', str(p))
                  .replace('#q#', str(q))
                  .replace('#s#', str(s))
                  , end='')
         
def resetPowersXML():
    file=join(DevicesModelTests.ApacheHTTPpath, 'powers.xml')
    file_bak=join(DevicesModelTests.ApacheHTTPpath, 'powers.xml.bak')
    import os
    try:
        os.remove(path=file)
    except:
        pass
    os.rename(src=file_bak,dst=file)

print('############################################')
print('# TESTING OF MasterGPIOs MODEL FUNCTIONS #')
print('############################################')
class MainDeviceVarsModelTests(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
        self.DB.dropTable(table='MainVariables')
        pass
 
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
         
# INDIVIDUAL FUNCTIONS TESTING
    def test_store2DB(self):
        '''
        storeDB: method provided to perform the foloowing steps:
            - Validate the input data for the GPIO
            - Saves the instance into the DB
            - Introduces a first register into the registers DB with the current value reading it for Inputs, and forcing it in Outputs
        '''
        print('## TESTING THE OPERATION OF THE store2DB METHOD ##')
        instance=MainDeviceVars(**MainDeviceVarDict)
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        instance.store2DB()
        # checks that store2DB creates the corresponding table in the registers DB and introduces a first record with the current value
        self.assertEqual(instance.Value,MainDeviceVarDict['Value'])
        self.assertTrue(self.DB.checkIfTableExist(table=instance.getRegistersDBTableName()))
        latest=instance.getLatestData(localized=False)
        self.assertAlmostEqual(latest[instance.getRegistersDBTag()]['timestamp'],now,delta=datetime.timedelta(seconds=1))# latest value is dated now
        self.assertEqual(latest[instance.getRegistersDBTag()]['value'],MainDeviceVarDict['Value'])# latest value is the same as in the dict
        self.DB.dropTable(table=instance.getRegistersDBTableName())
         
    def test_update_value(self):
        '''
        update_value: method that handles the creation of registers DB rows. It has several alternative operational paths:
            - The standard one is when the pre-initialized parameters are defaulted. In this situation, it checks if newValue is different from the previous one
            and in case so, it introduces a row with the previous value, and a second one with the newValue. Both these rows are separated 1 second in the timestamps
            to provide step-like plots.
            - If a timestamp is provided, only one row is created with the passed timestamp if and only if newValue is different from the previous one.
            - If force=True, it generates the row independently of the newValue.
            Independently of the operational path followed, this method also sets up the value of the GPIO in case it is an output.
        '''
        print('## TESTING THE OPERATION OF THE update_value METHOD ##')
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.save() # to avoid the creation of the DB tables and insertion of the first row that function store2DB does...
        print('    -> Tested standard path')
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        instance.update_value(newValue=22,timestamp=None,writeDB=True,force=False)
        table=instance.getRegistersDBTableName()
        vars='"timestamp","'+instance.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 2'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        self.assertEqual(rows[1][1],MainDeviceVarDict['Value'])# previous to latest value equals the previous Value
        self.assertEqual(rows[0][1],22) # latest value equals the newValue
        self.assertEqual(rows[0][0]-rows[1][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
        self.assertAlmostEqual(rows[0][0],now,delta=datetime.timedelta(seconds=1))# checks that the latest value is dated now
          
        print('    -> Tested update with timestamp')
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)+datetime.timedelta(seconds=10)
        instance.update_value(newValue=21,timestamp=now,writeDB=True,force=False)
        latest=instance.getLatestData(localized=False)
        self.assertEqual(latest[instance.getRegistersDBTag()]['timestamp'],now)# latest value is dated now
        self.assertEqual(latest[instance.getRegistersDBTag()]['value'],21)# latest value is dated now
          
        self.DB.dropTable(table=instance.getRegistersDBTableName())
     
    def test_IntegrityError(self):
        '''
        This tests checks that in case of two semi-simultaneous MainVars queries to registers DB, no error occurs. In fact, the 
        DB driver handles it by delaying in time the conflicting row up to when there is no more integrity error.
        '''
        import time
        print('## TESTING THE OPERATION OF THE registers DB Integrity Error handler METHOD ##')
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.store2DB()
        newDict=editDict(keys=['Value','Label'], newValues=[15,'Test MainVar 2'], Dictionary=MainDeviceVarDict)
        instance2=MainDeviceVars(**newDict)
        time.sleep(1)
        instance2.store2DB()
        
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        newValue1=21
        newValue2=16
        instance.update_value(newValue=newValue1,timestamp=now,writeDB=True,force=False)
        instance2.update_value(newValue=newValue2,timestamp=now,writeDB=True,force=False)
        
        table=instance.getRegistersDBTableName()
        vars='"timestamp","'+instance.getRegistersDBTag()+'"'+ ',"'+instance2.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp ASC'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        # initialization
        self.assertEqual(rows[0][1],MainDeviceVarDict['Value']) # initial value of instance
        self.assertEqual(rows[0][2],None) # instance2 not yet created
        self.assertEqual(rows[1][2],newDict['Value']) # initial value of instance2
        # instance update_value
        self.assertEqual(rows[2][1],newValue1) # new value of instance
        self.assertEqual(rows[2][2],newDict['Value']) # initial value of instance2
        # instance2 update_value
        self.assertEqual(rows[3][1],newValue1) # new value of instance
        self.assertEqual(rows[3][2],newValue2) # initial value of instance2
        # time span
        for i in range(0,2):
            self.assertEqual(rows[i+1][0]-rows[i][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
 
        self.DB.dropTable(table=instance.getRegistersDBTableName())
        self.DB.dropTable(table=instance2.getRegistersDBTableName())
          
    def test_str(self):        
        print('## TESTING THE OPERATION OF THE str METHOD ##')
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.store2DB()
        self.assertEqual(str(instance),instance.Label)
        self.DB.dropTable(table=instance.getRegistersDBTableName())
 
    def test_getCharts(self):
        '''
        getCharts: method that retrieves the chart structured in a dictionary with the following keys:
            - title : the table name
            - cols : a list with the first element being a list of dictionaries describing data of each of the columns in the graph
                . label : human readable label for the variable (a list of 8 elements in case of digital variables)
                . name : the name of the variable
                . type : the type (digital, analog, datetime) of the variable
                . plottype : the type of plot desired for the variable
            - rows : a list of the row values of the graph. Each row is a list with the first element being a unix timestamp and the following ones are the values of the variables.
            - statistics: a dictionary with teh following keys:
                . number : the number of the statistic indicators
                . num_rows : the number of rows of the graph
                . mean : a list with the mean values of each of the columns. A None value is introduced for digital variables
                . max : a list with the max values of each of the columns.
                . min : a list with the min values of each of the columns.
                . on_time : a list with the amount of seconds being at value==1 of each of the columns (for digital variables only, None else)
                . off_time : a list with the amount of seconds being at value==0 of each of the columns (for digital variables only, None else)
        In case no values are in the DB in the time span required, it returns two rows with date dateIni and dateEnd respectively with the rows
        being:
            - the last values present in the DB if there are any.
            - None in case no register can be found at all.
        '''
         
        print('## TESTING THE OPERATION OF THE getCharts METHOD ##')
        import time
        print('    -> Tested with valid records in the DB')
        local_tz=get_localzone()
          
        dateIni=(timezone.now()-datetime.timedelta(seconds=1)).replace(microsecond=0)
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.store2DB()
          
        newDict=editDict(keys=['Value','Label'], newValues=[15,'Test MainVar 2'], Dictionary=MainDeviceVarDict)
        instance2=MainDeviceVars(**newDict)
        instance2.store2DB()
        
        newValue1=21
        newValue2=16
        now=timezone.now()
        instance.update_value(newValue=newValue1,timestamp=now,writeDB=True,force=False)
        instance2.update_value(newValue=newValue2,timestamp=now,writeDB=True,force=False)

        dateEnd=(timezone.now()+datetime.timedelta(seconds=4)).replace(microsecond=0)
          
        charts=MainDeviceVars.getCharts(fromDate=dateIni,toDate=dateEnd)
        for chart in charts:
            title=chart['title']
            self.assertTrue('MainVariables' in title)
            self.assertEqual(chart['cols'][0][0]['label'],'timestamp') # first column is timestamp
            self.assertEqual(chart['cols'][0][1]['label'],MainDeviceVarDict['Label']) # second column is the first var
            self.assertEqual(chart['cols'][0][2]['label'],newDict['Label']) # third column is the second var

            self.assertEqual(len(chart['rows']),4) # there are 4 rows with data
            self.assertEqual(chart['rows'][0][1],MainDeviceVarDict['Value'])
            self.assertEqual(chart['rows'][0][2],None)
            self.assertEqual(chart['rows'][1][1],MainDeviceVarDict['Value'])
            self.assertEqual(chart['rows'][1][2],newDict['Value'])
            self.assertEqual(chart['rows'][2][1],newValue1)
            self.assertEqual(chart['rows'][2][2],newDict['Value'])
            self.assertEqual(chart['rows'][3][1],newValue1)
            self.assertEqual(chart['rows'][3][2],newValue2)
          
        print('    -> Tested with no records in the solicited timespan but yes in the DB')
        ''' creates two registers dated in dateIni and dateEnd with the last value from the registers DB
        '''
        dateIni=(timezone.now()+datetime.timedelta(seconds=10)).replace(microsecond=0)
        dateEnd=(dateIni+datetime.timedelta(seconds=10)).replace(microsecond=0)
        charts=MainDeviceVars.getCharts(fromDate=dateIni,toDate=dateEnd)
        for chart in charts:
            title=chart['title']
            self.assertEqual(len(chart['rows']),2) # there are 2 rows with data dated at dateIni and dateEnd resp.
            self.assertEqual(chart['rows'][0][1], chart['rows'][1][1]) # checks both rows have the same value
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
               
        self.DB.dropTable(table=instance.getRegistersDBTableName())
        self.DB.dropTable(table=instance2.getRegistersDBTableName())
        
        print('    -> Tested with no table in the DB')
        instance.delete()
        instance2.delete()
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.save()
        instance2=MainDeviceVars(**newDict)
        instance2.save()
        
        charts=MainDeviceVars.getCharts(fromDate=dateIni,toDate=dateEnd)
        for chart in charts:
            title=chart['title']
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
            for i,col in enumerate(chart['cols'][0]):
                if col['type']==DTYPE_DIGITAL:
                    self.assertEqual(chart['rows'][0][i],[None,None,None,None,None,None,None,None]) # all None values
                elif col['type']!='datetime':
                    self.assertEqual(chart['rows'][0][i],None) # all None values
                      
        print('    -> Tested with empty table in the DB')
        instance.checkRegistersDB(Database=self.DB)
        instance2.checkRegistersDB(Database=self.DB)
        self.assertTrue(self.DB.checkIfTableExist(instance.getRegistersDBTableName()))
        self.assertTrue(self.DB.checkIfTableExist(instance2.getRegistersDBTableName()))
        charts=MasterGPIOs.getCharts(fromDate=dateIni,toDate=dateEnd)
        for chart in charts:
            title=chart['title']
            self.assertTrue(len(chart['rows'])==2) # there are 2 rows with data dated at dateIni and dateEnd resp.
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
            for i,col in enumerate(chart['cols'][0]):
                if col['type']==DTYPE_DIGITAL:
                    self.assertEqual(chart['rows'][0][i],[None,None,None,None,None,None,None,None]) # all None values
                elif col['type']!='datetime':
                    self.assertEqual(chart['rows'][0][i],None) # all None values
              
        self.DB.dropTable(table=instance.getRegistersDBTableName())
        self.DB.dropTable(table=instance2.getRegistersDBTableName())
        
        
# print('############################################')
# print('# TESTING OF MasterGPIOs MODEL FUNCTIONS #')
# print('############################################')
# class MasterGPIOsModelTests(TestCase):
#     def setUp(self):
#         from utils.BBDD import getRegistersDBInstance
#         self.DB=getRegistersDBInstance()
#         self.DB.dropTable(table='inputs')
#         self.DB.dropTable(table='outputs')
#         pass
#  
#     def __init__(self,*args,**kwargs):
#         super().__init__(*args,**kwargs)
#         
#          
# # INDIVIDUAL FUNCTIONS TESTING
#     def test_store2DB(self):
#         '''
#         storeDB: method provided to perform the foloowing steps:
#             - Validate the input data for the GPIO
#             - Saves the instance into the DB
#             - Introduces a first register into the registers DB with the current value reading it for Inputs, and forcing it in Outputs
#         '''
#         print('## TESTING THE OPERATION OF THE store2DB METHOD ##')
#         instance=MasterGPIOs(**MasterGPIODict)
#         now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
#         instance.store2DB()
#         # checks that store2DB creates the corresponding table in the registers DB and introduces a first record with the current value
#         self.assertEqual(instance.Value,GPIO_HIGH)
#         self.assertTrue(self.DB.checkIfTableExist(table=instance.getRegistersDBTableName()))
#         latest=instance.getLatestData(localized=False)
#         self.assertAlmostEqual(latest[instance.getRegistersDBTag()]['timestamp'],now,delta=datetime.timedelta(seconds=1))# latest value is dated now
#         self.assertEqual(latest[instance.getRegistersDBTag()]['value'],GPIO_HIGH)# latest value is high
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#          
#     def test_update_value(self):
#         '''
#         update_value: method that handles the creation of registers DB rows. It has several alternative operational paths:
#             - The standard one is when the pre-initialized parameters are defaulted. In this situation, it checks if newValue is different from the previous one
#             and in case so, it introduces a row with the previous value, and a second one with the newValue. Both these rows are separated 1 second in the timestamps
#             to provide step-like plots.
#             - If a timestamp is provided, only one row is created with the passed timestamp if and only if newValue is different from the previous one.
#             - If force=True, it generates the row independently of the newValue.
#             Independently of the operational path followed, this method also sets up the value of the GPIO in case it is an output.
#         '''
#         print('## TESTING THE OPERATION OF THE update_value METHOD ##')
#         instance=MasterGPIOs(**MasterGPIODict)
#         instance.save() # to avoid the creation of the DB tables and insertion of the first row that function store2DB does...
#         print('    -> Tested standard path')
#         now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
#         instance.update_value(newValue=GPIO_LOW,timestamp=None,writeDB=True,force=False)
#         table=instance.getRegistersDBTableName()
#         vars='"timestamp","'+instance.getRegistersDBTag()+'"'
#         sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 2'
#         rows=self.DB.executeTransaction(SQLstatement=sql)
#         self.assertEqual(rows[1][1],GPIO_HIGH)# previous to latest value equals the previous Value
#         self.assertEqual(rows[0][1],GPIO_LOW) # latest value equals the newValue
#         self.assertEqual(rows[0][0]-rows[1][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
#         self.assertAlmostEqual(rows[0][0],now,delta=datetime.timedelta(seconds=1))# checks that the latest value is dated now
#          
#         print('    -> Tested update with timestamp')
#         now=timezone.now().replace(microsecond=0).replace(tzinfo=None)+datetime.timedelta(seconds=10)
#         instance.update_value(newValue=GPIO_HIGH,timestamp=now,writeDB=True,force=False)
#         latest=instance.getLatestData(localized=False)
#         self.assertEqual(latest[instance.getRegistersDBTag()]['timestamp'],now)# latest value is dated now
#         self.assertEqual(latest[instance.getRegistersDBTag()]['value'],GPIO_HIGH)# latest value is dated now
#          
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#     
#     def test_setHigh(self):
#         '''
#         Method that sets the value of an output to high and updates the value in the registers DB.
#         '''
#         print('## TESTING THE OPERATION OF THE setHigh METHOD ##')
#         newDict=editDict(keys=['Value',], newValues=[GPIO_LOW,], Dictionary=MasterGPIODict)
#         instance=MasterGPIOs(**newDict)
#         instance.store2DB()
#         instance.setHigh()
#         self.assertEqual(instance.Value,GPIO_HIGH)# current value equals High
#         latest=instance.getLatestData(localized=False)
#         self.assertEqual(latest[instance.getRegistersDBTag()]['value'],GPIO_HIGH)# last value on DB equals High
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#      
#     def test_setLow(self):
#         '''
#         Method that sets the value of an output to low and updates the value in the registers DB.
#         '''
#         print('## TESTING THE OPERATION OF THE setLow METHOD ##')
#         newDict=editDict(keys=['Value',], newValues=[GPIO_HIGH,], Dictionary=MasterGPIODict)
#         instance=MasterGPIOs(**newDict)
#         instance.store2DB()
#         instance.setLow()
#         self.assertEqual(instance.Value,GPIO_LOW)# current value equals Low
#         latest=instance.getLatestData(localized=False)
#         self.assertEqual(latest[instance.getRegistersDBTag()]['value'],GPIO_LOW)# last value on DB equals Low
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#         
#     def test_IntegrityError(self):
#         '''
#         This tests checks that in case of two semi-simultaneous GPIO queries to registers DB, no error occurs. In fact, the 
#         DB driver handles it by delaying in time the conflicting row up to when there is no more integrity error.
#         '''
#         import time
#         print('## TESTING THE OPERATION OF THE registers DB Integrity Error handler METHOD ##')
#         instance=MasterGPIOs(**MasterGPIODict)
#         instance.store2DB()
#         newDict=editDict(keys=['Pin','Label'], newValues=[15,'Test Output 2'], Dictionary=MasterGPIODict)
#         instance2=MasterGPIOs(**newDict)
#         time.sleep(1)
#         instance2.store2DB()
#          
#         instance.setLow()
#         instance2.setLow()
#         table=instance.getRegistersDBTableName()
#         vars='"timestamp","'+instance.getRegistersDBTag()+'"'+ ',"'+instance2.getRegistersDBTag()+'"'
#         sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp ASC'
#         rows=self.DB.executeTransaction(SQLstatement=sql)
#         # initialization
#         self.assertEqual(rows[0][1],GPIO_HIGH) # initial value of instance
#         self.assertEqual(rows[0][2],None) # instance2 not yet created
#         self.assertEqual(rows[1][2],GPIO_HIGH) # initial value of instance2
#         # instance setLow
#         self.assertEqual(rows[2][1],GPIO_HIGH) # previous value of instance
#         self.assertEqual(rows[3][1],GPIO_LOW) # new value of instance
#         self.assertEqual(rows[2][2],GPIO_HIGH) # initial value of instance2
#         self.assertEqual(rows[3][2],GPIO_HIGH) # initial value of instance2
#         # instance2 setLow
#         self.assertEqual(rows[4][1],GPIO_LOW) # value of instance
#         self.assertEqual(rows[5][1],GPIO_LOW) # value of instance
#         self.assertEqual(rows[4][2],GPIO_HIGH) # previous value of instance2
#         self.assertEqual(rows[5][2],GPIO_LOW) # new value of instance2
#         # time span
#         for i in range(2,4):
#             self.assertEqual(rows[i+1][0]-rows[i][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
# 
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#         self.DB.dropTable(table=instance2.getRegistersDBTableName())
#          
#     def test_str(self):        
#         print('## TESTING THE OPERATION OF THE str METHOD ##')
#         instance=MasterGPIOs(**MasterGPIODict)
#         instance.store2DB()
#         self.assertEqual(str(instance),instance.Label + ' on pin ' + str(instance.Pin) )
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#      
#     def test_initializeIOs(self):
#         print('## TESTING THE OPERATION OF THE initializeIOs METHOD ##')
#         instance=MasterGPIOs(**MasterGPIODict)
#         instance.store2DB()
#         newDict=editDict(keys=['Pin','Label','Direction','Value'], newValues=[15,'Test Input 1',GPIO_INPUT,GPIO_LOW], Dictionary=MasterGPIODict)
#         instance2=MasterGPIOs(**newDict)
#         instance2.store2DB()
#          
#         print('    -> Tested declareInputEvent=True')
#         MasterGPIOs.initializeIOs(declareInputEvent=True)
#         print('    -> Tested declareInputEvent=False')
#         MasterGPIOs.initializeIOs(declareInputEvent=False)
#         
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#         self.DB.dropTable(table=instance2.getRegistersDBTableName())
#          
#     def test_getCharts(self):
#         '''
#         getCharts: method that retrieves the chart structured in a dictionary with the following keys:
#             - title : the table name
#             - cols : a list with the first element being a list of dictionaries describing data of each of the columns in the graph
#                 . label : human readable label for the variable (a list of 8 elements in case of digital variables)
#                 . name : the name of the variable
#                 . type : the type (digital, analog, datetime) of the variable
#                 . plottype : the type of plot desired for the variable
#             - rows : a list of the row values of the graph. Each row is a list with the first element being a unix timestamp and the following ones are the values of the variables.
#             - statistics: a dictionary with teh following keys:
#                 . number : the number of the statistic indicators
#                 . num_rows : the number of rows of the graph
#                 . mean : a list with the mean values of each of the columns. A None value is introduced for digital variables
#                 . max : a list with the max values of each of the columns.
#                 . min : a list with the min values of each of the columns.
#                 . on_time : a list with the amount of seconds being at value==1 of each of the columns (for digital variables only, None else)
#                 . off_time : a list with the amount of seconds being at value==0 of each of the columns (for digital variables only, None else)
#         In case no values are in the DB in the time span required, it returns two rows with date dateIni and dateEnd respectively with the rows
#         being:
#             - the last values present in the DB if there are any.
#             - None in case no register can be found at all.
#         '''
#         
#         print('## TESTING THE OPERATION OF THE getCharts METHOD ##')
#         import time
#         print('    -> Tested with valid records in the DB')
#         local_tz=get_localzone()
#          
#         dateIni=(timezone.now()-datetime.timedelta(seconds=1)).replace(microsecond=0)
#         outDict=editDict(keys=['Value',], newValues=[GPIO_LOW,], Dictionary=MasterGPIODict)
#         instance=MasterGPIOs(**outDict)
#         instance.store2DB()
#          
#         inDict=editDict(keys=['Pin','Label','Direction','Value'], newValues=[15,'Test Input 1',GPIO_INPUT,GPIO_LOW], Dictionary=MasterGPIODict)
#         instance2=MasterGPIOs(**inDict)
#         instance2.store2DB()
#         instance.update_value(newValue=GPIO_HIGH,timestamp=None,writeDB=True,force=False)
#         instance2.update_value(newValue=GPIO_HIGH,timestamp=None,writeDB=True,force=False)
#         time.sleep(4)
#         instance.update_value(newValue=GPIO_LOW,timestamp=None,writeDB=True,force=False)
#         instance2.update_value(newValue=GPIO_LOW,timestamp=None,writeDB=True,force=False)
#          
#         dateEnd=timezone.now().replace(microsecond=0)
#          
#         charts=MasterGPIOs.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for chart in charts:
#             title=chart['title']
#             self.assertTrue(title in 'inputs outputs')
#             self.assertTrue(chart['cols'][0][0]['label']=='timestamp') # first column is timestamp
#             if title=='inputs':
#                 self.assertTrue(chart['cols'][0][1]['label'][0]==inDict['Label']) # second column is the GPIO
#             else:
#                 self.assertTrue(chart['cols'][0][1]['label'][0]==outDict['Label']) # second column is the GPIO
#             self.assertEqual(len(chart['rows']),5) # there are 5 rows with data
#             self.assertTrue(chart['rows'][0][1][0]==0)
#             self.assertTrue(chart['rows'][1][1][0]==0)
#             self.assertTrue(chart['rows'][2][1][0]==1)
#             self.assertTrue(chart['rows'][3][1][0]==1)
#             self.assertTrue(chart['rows'][4][1][0]==0)
#          
#         print('    -> Tested with no records in the solicited timespan but yes in the DB')
#         ''' creates two registers dated in dateIni and dateEnd with the last value from the registers DB
#         '''
#         dateIni=(timezone.now()+datetime.timedelta(seconds=1)).replace(microsecond=0)
#         dateEnd=(dateIni+datetime.timedelta(seconds=10)).replace(microsecond=0)
#         charts=MasterGPIOs.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for chart in charts:
#             title=chart['title']
#             self.assertTrue(len(chart['rows'])==2) # there are 2 rows with data dated at dateIni and dateEnd resp.
#             self.assertEqual(chart['rows'][0][1][0], chart['rows'][1][1][0]) # checks both rows have the same value
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
#              
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#         self.DB.dropTable(table=instance2.getRegistersDBTableName())
#         print('    -> Tested with no table in the DB')
#         instance.delete()
#         instance2.delete()
#         instance=MasterGPIOs(**outDict)
#         instance.save()
#         instance2=MasterGPIOs(**inDict)
#         instance2.save()
#         charts=MasterGPIOs.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for chart in charts:
#             title=chart['title']
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
#             for i,col in enumerate(chart['cols'][0]):
#                 if col['type']==DTYPE_DIGITAL:
#                     self.assertEqual(chart['rows'][0][i],[None,None,None,None,None,None,None,None]) # all None values
#                 elif col['type']!='datetime':
#                     self.assertEqual(chart['rows'][0][i],None) # all None values
#                     
#         print('    -> Tested with empty table in the DB')
#         instance.checkRegistersDB(Database=self.DB)
#         instance2.checkRegistersDB(Database=self.DB)
#         self.assertTrue(self.DB.checkIfTableExist(instance.getRegistersDBTableName()))
#         self.assertTrue(self.DB.checkIfTableExist(instance2.getRegistersDBTableName()))
#         charts=MasterGPIOs.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for chart in charts:
#             title=chart['title']
#             self.assertTrue(len(chart['rows'])==2) # there are 2 rows with data dated at dateIni and dateEnd resp.
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
#             for i,col in enumerate(chart['cols'][0]):
#                 if col['type']==DTYPE_DIGITAL:
#                     self.assertEqual(chart['rows'][0][i],[None,None,None,None,None,None,None,None]) # all None values
#                 elif col['type']!='datetime':
#                     self.assertEqual(chart['rows'][0][i],None) # all None values
#              
#         self.DB.dropTable(table=instance.getRegistersDBTableName())
#         self.DB.dropTable(table=instance2.getRegistersDBTableName())
#         
#          
# print('############################################')
# print('# TESTING OF DatagramItems MODEL FUNCTIONS #')
# print('############################################')
# class DatagramItemsModelTests(TestCase):
#     def setUp(self):
#         global DatagramItemDict
#         pass
#   
#     def __init__(self,*args,**kwargs):
#         super().__init__(*args,**kwargs)
#            
#            
# # INDIVIDUAL FUNCTIONS TESTING
#     def test_clean(self):        
#         print('## TESTING THE OPERATION OF THE clean METHOD ##')
#         instance=DatagramItems(**DatagramItemDict)
#         instance.store2DB()
#         self.assertEqual(instance.Units,'bits')
#         self.assertEqual(instance.PlotType,LINE_PLOT)
#        
#     def test_str(self):        
#         print('## TESTING THE OPERATION OF THE str METHOD ##')
#         instance=DatagramItems(**DatagramItemDict)
#         instance.store2DB()
#         self.assertEqual(str(instance),DatagramItemDict['Tag'])
#        
#     def test_getHumanName(self):        
#         print('## TESTING THE OPERATION OF THE getHumanName METHOD ##')
#         instance=DatagramItems(**DatagramItemDict)
#         instance.store2DB()
#         self.assertEqual(instance.getHumanName(),DatagramItemDict['Tag']+'_'+instance.Units)
#    
# print('########################################')
# print('# TESTING OF Datagrams MODEL FUNCTIONS #')
# print('########################################')
# class DatagramsModelTests(TestCase):
#     fixtures=['DevicesAPP.json',]
#     def setUp(self):
#         global DatagramItemDict
#         self.remoteDVT=DeviceTypes.objects.get(pk=1)
#         self.localDVT=DeviceTypes.objects.get(pk=2)
#         self.memoryDVT=DeviceTypes.objects.get(pk=3)
#         pass
#    
#     def __init__(self,*args,**kwargs):
#         super().__init__(*args,**kwargs)
#            
#            
# # INDIVIDUAL FUNCTIONS TESTING
#     def test_clean(self):        
#         print('## TESTING THE OPERATION OF THE save METHOD ##')
#         newDict=editDict(keys=['DVT',],newValues=[self.localDVT,],Dictionary=DatagramDict)
#            
#         DG=Datagrams(**newDict)
#         DG.store2DB()
#         ITMs=[]
#         for k in range(0,3):
#             newDict=editDict(keys=['Tag',],newValues=['DigitalItem'+str(k),],Dictionary=DatagramItemDict)
#             ITMs.append(DatagramItems(**newDict))
#             newDict=editDict(keys=['Tag','DataType'],newValues=['AnalogItem'+str(k),DTYPE_FLOAT],Dictionary=DatagramItemDict)
#             ITMs.append(DatagramItems(**newDict))
#                
#         for i,ITM in enumerate(ITMs):
#             ITM.store2DB()
#             newDict=editDict(keys=['Order','DG','ITM'],newValues=[i+1,DG,ITM],Dictionary=ItemOrderingDict)
#             ITO=ItemOrdering(**newDict)
#             ITO.save()
#            
#         DG=Datagrams.objects.get(Identifier=DatagramDict['Identifier'])
#         for i,ITM in enumerate(DG.ITMs.all()):
#             self.assertEqual(ITM,ITMs[i])
#        
#     def test_getDBTypes(self):        
#         print('## TESTING THE OPERATION OF THE getDBTypes METHOD ##')
#         DG=Datagrams.objects.get(Identifier='instant')
#         types=DG.getDBTypes()
#         self.assertEqual(types[0],'datetime')
#         for type in types[1:]:
#             self.assertEqual(type,DTYPE_FLOAT)
#            
#         DG=Datagrams.objects.get(Identifier='powers')
#         types=DG.getDBTypes()
#         self.assertEqual(types[0],'datetime')
#         self.assertEqual(types[1],DTYPE_DIGITAL)
#         for type in types[2:]:
#             self.assertEqual(type,DTYPE_FLOAT)
#        
#     def test_getInfoFromItemName(self):        
#         print('## TESTING THE OPERATION OF THE getInfoFromItemName METHOD ##')
#         with self.assertRaises(DevicesAppException):
#             Datagrams.getInfoFromItemName('22_2_1')
#             Datagrams.getInfoFromItemName('22_2_1_56')
#         info=Datagrams.getInfoFromItemName('1_1_1')
#         ITM=DatagramItems.objects.get(pk=1)
#         self.assertEqual(info['type'],ITM.DataType)
#            
# 
# print('######################################')
# print('# TESTING OF Devices MODEL FUNCTIONS #')
# print('######################################')
#         
# class DevicesModelTests(TestCase):
#     fixtures=['DevicesAPP.json',]
#     sensIO=None
#     outIO=None
#     inIO=None
#     remoteDVT=None
#     localDVT=None
#     memoryDVT=None
#     DB=None
#     ApacheHTTPpath=r'C:\xampp\htdocs'
#                 
#     def setUp(self):
#         from utils.BBDD import getRegistersDBInstance
#         
#         self.DB=getRegistersDBInstance()
#         self.remoteDVT=DeviceTypes.objects.get(pk=1)
#         self.localDVT=DeviceTypes.objects.get(pk=2)
#         self.memoryDVT=DeviceTypes.objects.get(pk=3)
#         MasterGPIOs(Pin=17,Label='Sensor IO',Direction=GPIO_SENSOR).save()
#         self.sensIO=MasterGPIOs.objects.get(Pin=17)
#         MasterGPIOs(Pin=18,Label='Output IO',Direction=GPIO_OUTPUT).save()
#         self.outIO=MasterGPIOs.objects.get(Pin=18)
#         self.inIO=MasterGPIOs(Pin=19,Label='Input IO',Direction=GPIO_INPUT)
#         self.inIO.save()
#             
#     def __init__(self,*args,**kwargs):
#         import psutil
#         super().__init__(*args,**kwargs)
#         if "httpd.exe" in (p.name() for p in psutil.process_iter()):
#             stopApache()
#         from utils.BBDD import createTSTDB
#         createTSTDB()
#             
# # INDIVIDUAL FUNCTIONS TESTING
#     def test_getCharts(self):
#         print('## TESTING THE OPERATION OF THE getCharts METHOD ##')
#         import time
#         print('    -> Tested with valid records in the DB')
#         local_tz=get_localzone()
#          
#         dateIni=(timezone.now()-datetime.timedelta(hours=1)).replace(microsecond=0)
#  
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
#         instance=Devices(**newDict)
#         instance.save()
#          
#         instance.deleteRegistersTables()
#          
#         dateEnd=timezone.now().replace(microsecond=0)
#          
#         timestamps= [dateIni + datetime.timedelta(minutes=x) for x in range(0, 70,10)]
#         values=[[7,3.25,0.5,3.5],[220.5,]]
#          
#         for ts in timestamps:
#             instance.insertRegister(TimeStamp=ts,DatagramId='powers',year=dateIni.year,values=values[0],NULL=False)
#             instance.insertRegister(TimeStamp=ts,DatagramId='instant',year=dateIni.year,values=values[1],NULL=False)
#  
#         charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for k,chart in enumerate(charts):
#             title=chart['title']
#              
#             self.assertTrue(len(chart['rows'])==len(timestamps))
#             for i,col in enumerate(chart['cols'][0]):
#                 self.assertTrue('label' in col)
#                 self.assertTrue('type' in col)
#                 self.assertTrue('plottype' in col)
#                 if col['type']==DTYPE_DIGITAL:
#                     self.assertTrue(chart['rows'][0][i]==[1,1,1,0,0,0,0,0])
#                 elif col['type']!='datetime':
#                     self.assertEqual(chart['rows'][0][i],values[k][i-1]) 
#          
#         print('    -> Tested with no records in the solicited timespan but yes in the DB')
#         dateIni=(timezone.now()+datetime.timedelta(seconds=1)).replace(microsecond=0)
#         dateEnd=(dateIni+datetime.timedelta(hours=1)).replace(microsecond=0)
#         charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for chart in charts:
#             title=chart['title']
#             self.assertTrue(len(chart['rows'])==2) # there are 2 rows with data dated at dateIni and dateEnd resp.
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
#              
#         instance.deleteRegistersTables()
#          
#         print('    -> Tested with no table in the DB')
#         charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for chart in charts:
#             title=chart['title']
#             self.assertTrue(len(chart['rows'])==2) # there are 2 rows with data dated at dateIni and dateEnd resp.
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
#             for i,col in enumerate(chart['cols'][0]):
#                 if col['type']==DTYPE_DIGITAL:
#                     self.assertEqual(chart['rows'][0][i],[None,None,None,None,None,None,None,None]) # all None values
#                 elif col['type']!='datetime':
#                     self.assertEqual(chart['rows'][0][i],None) # all None values
#              
#         print('    -> Tested with empty table in the DB')
#         instance.checkRegistersDB(Database=self.DB)
#         tables=instance.getRegistersTables()
#         for table in tables:
#             self.assertTrue(self.DB.checkIfTableExist(table=table))
#         charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
#         for chart in charts:
#             title=chart['title']
#             self.assertTrue(len(chart['rows'])==2) # there are 2 rows with data dated at dateIni and dateEnd resp.
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
#             self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
#             for i,col in enumerate(chart['cols'][0]):
#                 if col['type']==DTYPE_DIGITAL:
#                     self.assertEqual(chart['rows'][0][i],[None,None,None,None,None,None,None,None]) # all None values
#                 elif col['type']!='datetime':
#                     self.assertEqual(chart['rows'][0][i],None) # all None values
#              
#         instance.deleteRegistersTables()
#          
#     def test_errors_on_clean(self):        
#         '''
#         CHECKS THE ASSERTION OF VALIDATION ERROR WHEN IMPROPER VALUES ARE INTRODUCED
#         '''
#         print('## TESTING THE OPERATION OF THE clean METHOD ##')
#         sampletimes=[600,6,6]
#         RTsampletimes=[6,60,6]
#         print('    --> Test_errors_on_clean test 0.1: Validation error due to too low Sampletime')
#         newDict=editDict(keys=['Sampletime','DVT'],newValues=[6,self.remoteDVT])
#         instance=Devices(**newDict)
#         self.assertRaises(ValidationError,instance.clean)
#             
#         print('    --> Test_errors_on_clean test 0.2: Validation error due to too low RTSampletime')
#         newDict=editDict(keys=['RTsampletime','DVT'],newValues=[6,self.remoteDVT])
#         instance=Devices(**newDict)
#         self.assertRaises(ValidationError,instance.clean)
#             
#         print('    --> Test_errors_on_clean test 0.3: Validation error due to wrong IO')
#         IOfake=MasterGPIOs(Pin=17,Label='Test IO',Direction=GPIO_OUTPUT)
#         newDict=editDict(keys=['IO','DVT'],newValues=[IOfake,self.localDVT])
#         instance=Devices(**newDict)
#         self.assertRaises(ValidationError,instance.clean)
#     
#     def test_store2DB(self):
#         '''
#         CHECKS THE SAVE OPERATION WHEN PROPER VALUES ARE INTRODUCED. 
#         ADDITIONALLY, THE REGISTERS TABLES CREATION AND DELETION IS ALSO TESTED AS NEW DEVICE IS SAVED.
#         '''            
#         print('## TESTING THE OPERATION OF THE store2DB METHOD ##')
#         print('    --> Test_OK_on_save test 1.0: With datagrams defined for devicetype')
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
#         instance=Devices(**newDict)
#         # CHECKED WITH DATAGRAMS DEFINED
#         instance.store2DB() # creates the registers tables
#         from utils.BBDD import getRegistersDBInstance
#         DB=getRegistersDBInstance()
#         DGs=Datagrams.objects.filter(DVT=instance.DVT)
#         for DG in DGs:
#             table=instance.getRegistersDBTableName(DG=DG)
#             row=DB.checkIfTableExist(table=table)
#             self.assertNotEqual(row,[])
#             self.assertEqual(DB.dropTable(table=table),0)
#             row=DB.checkIfTableExist(table=table)
#             self.assertEqual(row,False)
#         instance.delete()
#         print('    --> Test_OK_on_save test 1.1: Without datagrams defined for devicetype')
#         #CHECKED WITHOUT DATAGRAMS DEFINED
#         Datagrams.objects.filter(DVT=self.localDVT).delete()
#         newDict=editDict(keys=['DVT','Sampletime','RTsampletime'],newValues=[self.localDVT,600,60])
#         instance=Devices(**newDict)
#         instance.store2DB() # save creates the registers tables
#         DGs=Datagrams.objects.filter(DVT=instance.DVT)
#         self.assertQuerysetEqual(DGs,[])
# 
#     def test_request_datagram(self):
#         '''
#         CHECKS THE REQUEST TO DATAGRAM
#         '''
#         import psutil
#         print('## TESTING THE OPERATION OF THE request_datagram METHOD ##')
#         print('    --> Test_request_datagram test 2.0: Reception with writeDB=False')
#              
#         stopApache()
#         instance=Devices.objects.get(pk=1)
#             
#         datagram=instance.request_datagram(DatagramId='powers',timeout=1,writeToDB=False,resetOrder=True,retries=1)
#              
#         if not "httpd.exe" in (p.name() for p in psutil.process_iter()):
#             print('        Tested comm timeout and retrying')
#             self.assertIn('Finished retrying',datagram['Error'])
#              
#         startApache()
#         instance.IP='127.0.0.1'
#         instance.save()
#         setupPowersXML(code=1,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
#         datagram=instance.request_datagram(DatagramId='powers',timeout=1,writeToDB=False,resetOrder=True,retries=1)
#         resetPowersXML()
#                 
#         if "httpd.exe" in (p.name() for p in psutil.process_iter()):
#             print('        Tested comm OK')
#             self.assertEqual(datagram['values'], [7,3.25,3.24,3.258])
#         stopApache()
# 
#     def test_getLatestData(self):
#         '''
#         CHECKS THE RETRIEVAL OF THE LATETS DATA FROM THE REGISTER'S DB
#         '''
#         print('## TESTING THE OPERATION OF THE getLatestData METHOD ##')
#         print('    --> Test_getLatestData test 3.0: Retrieval of latest data from registers DB with CustomLabels defined')
#         pk=1
#         # run with CustomLabels defined
#         instance=Devices.objects.get(pk=pk)
#         latest=instance.getLatestData(localized=False)
#         #print(str(latest))
#         self.assertEqual(latest['1']['2_1_1'], 3.25)
#         for datagram in latest:
#             for name in latest[datagram]:
#                 if name!='timestamp':
#                     info=Datagrams.getInfoFromItemName(name=name)
#                     if info['type']==DTYPE_DIGITAL:
#                         self.assertEqual(latest[datagram][name]['bit2'], 1)
#                     elif info['type']==DTYPE_FLOAT:
#                         self.assertIsInstance(latest[datagram][name], type(3.2))
#                     elif info['type']==DTYPE_INTEGER:
#                         self.assertIsInstance(latest[datagram][name], type(3))
#         print('    --> Test_getLatestData test 3.1: Retrieval of latest data from registers DB with CustomLabels undefined')
#         # run with CustomLabels empty
#         prev=instance.CustomLabels
#         instance.CustomLabels=''
#         instance.store2DB()
#         latest=instance.getLatestData(localized=False)
#         #print(str(latest))
#         for datagram in latest:
#             for name in latest[datagram]:
#                 if name!='timestamp':
#                     info=Datagrams.getInfoFromItemName(name=name)
#                     if info['type']==DTYPE_DIGITAL:
#                         self.assertEqual(latest[datagram][name]['bit2'], 1)
#                     elif info['type']==DTYPE_FLOAT:
#                         self.assertIsInstance(latest[datagram][name], type(3.2))
#                     elif info['type']==DTYPE_INTEGER:
#                         self.assertIsInstance(latest[datagram][name], type(3))
#         print('    --> Test_getLatestData test 3.2: Retrieval of latest data from registers DB with CustomLabels undefined and no registers')
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
#         instance=Devices(**newDict)
#         instance.store2DB()
#         latest=instance.getLatestData(localized=False)
#         #print(str(latest))
#         for datagram in latest:
#             for name in latest[datagram]:
#                 if name!='timestamp':
#                     info=Datagrams.getInfoFromItemName(name=name)
#                     if info['type']==DTYPE_DIGITAL:
#                         self.assertEqual(latest[datagram][name], None)
#                     elif info['type']==DTYPE_FLOAT:
#                         self.assertEqual(latest[datagram][name], None)
#                     elif info['type']==DTYPE_INTEGER:
#                         self.assertEqual(latest[datagram][name], None)
#     
#     def test_getDeviceVariables(self):
#         print('## TESTING THE OPERATION OF THE getDeviceVariables METHOD ##')
#         print('    --> Test_getDeviceVariables test 4.0: Retrieval of devices variables with CustomLabels defined')
#         pk=1
#         # run with CustomLabels defined
#         instance=Devices.objects.get(pk=pk)
#         variables=instance.getDeviceVariables()
#         #print(str(variables))
#         for variable in variables:
#             info=Datagrams.getInfoFromItemName(name=variable['name'])
#             self.assertEqual(variable['device'],pk)
#             self.assertEqual(variable['table'].split('_')[0],str(pk))
#             if info['type']==DTYPE_DIGITAL:
#                 self.assertIsInstance(variable['bit'], type(3))
#                 self.assertEqual(variable['label'],'Error '+str(variable['bit']))
#             else:
#                 self.assertEqual(variable['bit'],None)
#                 self.assertIsInstance(variable['name'],type(''))
#                 self.assertIsInstance(variable['label'],type(''))
#         print('    --> Test_getDeviceVariables test 4.1: Retrieval of devices variables with CustomLabels undefined')
#         # run with CustomLabels empty
#         prev=instance.CustomLabels
#         instance.CustomLabels=''
#         instance.save()
#         variables=instance.getDeviceVariables()
#         #print(str(variables))
#         for variable in variables:
#             info=Datagrams.getInfoFromItemName(name=variable['name'])
#             self.assertEqual(variable['table'].split('_')[0],str(pk))
#             self.assertEqual(variable['device'],pk)
#             if info['type']==DTYPE_DIGITAL:
#                 self.assertIsInstance(variable['bit'], type(3))
#                 self.assertEqual(variable['label'],variable['name']+' bit '+str(variable['bit']))
#             else:
#                 self.assertEqual(variable['bit'],None)
#         instance.CustomLabels=prev
#         instance.save()
#     
#     def test_getRegistersTables(self):
#         print('## TESTING THE OPERATION OF THE getRegistersTables METHOD ##')
#         print('    --> Retrieval of devices tables on registers DB')
#         pk=1
#         # run with CustomLabels defined
#         instance=Devices.objects.get(pk=pk)
#         tables=instance.getRegistersTables()
#         self.assertEqual(tables,['1_1','1_2'])
#     
#     def test_setCustomLabels(self):
#         print('## TESTING THE OPERATION OF THE setCustomLabels METHOD ##')
#         print('    --> Modifies the value of the CustomLabels field')
#         import json
#         pk=1
#         # run with CustomLabels undefined
#         instance=Devices.objects.get(pk=pk)
#         prev=instance.CustomLabels
#         instance.CustomLabels=''
#         instance.save()
#         instance.setCustomLabels()
#         CustomLabels=json.loads(instance.CustomLabels)
#         for datagram in CustomLabels:
#             for name in CustomLabels[datagram]:
#                 info=Datagrams.getInfoFromItemName(name=name)
#                 self.assertEqual(CustomLabels[datagram][name],info['human'])
#     
#     def test_update_requests(self):
#         print('## TESTING THE OPERATION OF THE update_requests METHOD ##')
#         print('    --> Starts/Stops polling of device and checks scheduler')
#         from .constants import RUNNING_STATE,STOPPED_STATE
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
#         instance=Devices(**newDict)
#         instance.store2DB()
#         instance.startPolling()
#         self.assertEqual(instance.State,RUNNING_STATE)
#         jobs=instance.getPollingJobIDs()
#         for job in jobs:
#             scheduler=Devices.getScheduler()
#             JOB=scheduler.getJobInStore(jobId=job['id'])
#             self.assertIsNot(JOB,None)
# 
#         instance.stopPolling()
#         self.assertEqual(instance.State,STOPPED_STATE)
#         jobs=instance.getPollingJobIDs()
#         for job in jobs:
#             scheduler=Devices.getScheduler()
#             JOB=scheduler.getJobInStore(jobId=job['id'])
#             self.assertEqual(JOB,None)
#         instance.deleteRegistersTables()
#     
#     def test_setNextUpdate(self):
#         print('## TESTING THE OPERATION OF THE setNextUpdate METHOD ##')
#         print('    --> Sets the next update time for a device')
#         import datetime
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
#         instance=Devices(**newDict)
#         instance.save()
#         instance.startPolling()
#         now=datetime.datetime.now().replace(microsecond=0)
#         jobs=instance.getPollingJobIDs()
#         numJobs=len(jobs)
#         offset=instance.Sampletime/numJobs
#         for i,job in enumerate(jobs):
#             nextUpdate=instance.setNextUpdate(jobID=job['id']).replace(microsecond=0).replace(tzinfo=None)
#             self.assertAlmostEqual(nextUpdate,now+datetime.timedelta(seconds=i*offset+instance.Sampletime/2),delta=datetime.timedelta(seconds=1))
#         instance.deleteRegistersTables()
#     
#     def test_request_callback(self):
#         print('## TESTING THE OPERATION OF THE request_callback PROCEDURE  ##')
#         import time
#         import datetime
#         from utils.dataMangling import checkBit
#         from utils.BBDD import getRegistersDBInstance
#         print('    --> On a remote device')
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
#         instance=Devices(**newDict)
#         instance.store2DB()
#            
#         startApache()
#         setupPowersXML(code=2,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
#             
#         from .models import request_callback
#             
#         DGs=Datagrams.objects.filter(DVT=instance.DVT)
#         jobs=instance.getPollingJobIDs()
#             
#         for job in jobs:
#             request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
#            
#         now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
#         resetPowersXML()
#         latest=instance.getLatestData(localized=False)
#         for datagram in latest:
#             for name in latest[datagram]:
#                 if latest[datagram][name]!=None:
#                     if name!='timestamp':
#                         info=Datagrams.getInfoFromItemName(name=name)
#                         if info['type']==DTYPE_DIGITAL:
#                             for i in range(0,8):
#                                 self.assertEqual(latest[datagram][name]['bit'+str(i)], int(checkBit(number=7,position=i)))
#                         else:
#                             self.assertIsInstance(latest[datagram][name], type(3.2))
#                     else:
#                         self.assertAlmostEqual(latest[datagram][name],now,delta=datetime.timedelta(seconds=5))
#             
#         stopApache()
#                 
#         instance.deleteRegistersTables()
#            
#         print('    --> On a local device')
#         newDict=editDict(keys=['DVT','IP','Code','Name','IO','Sampletime','RTsampletime'],newValues=[self.localDVT,None,3,'Test Device 3',self.sensIO,600,60])
#         instance=Devices(**newDict)
#         instance.store2DB()
#            
#         from .models import request_callback
#             
#         DGs=Datagrams.objects.filter(DVT=instance.DVT)
#         jobs=instance.getPollingJobIDs()
#             
#         for job in jobs:
#             request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
#            
#         now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
#         latest=instance.getLatestData(localized=False)
#         if latest!=None:
#             for datagram in latest:
#                 for name in latest[datagram]:
#                     if latest[datagram][name]!=None:
#                         if name!='timestamp':
#                             info=Datagrams.getInfoFromItemName(name=name)
#                             if info['type']==DTYPE_DIGITAL:
#                                 for i in range(0,8):
#                                     self.assertEqual(latest[datagram][name]['bit'+str(i)], int(checkBit(number=7,position=i)))
#                             else:
#                                 self.assertIsInstance(latest[datagram][name], type(3.2))
#                         else:
#                             self.assertAlmostEqual(latest[datagram][name],now,delta=datetime.timedelta(seconds=5))
#                 
#         instance.deleteRegistersTables()
#            
#         print('    --> On a memory device')
#         newDict=editDict(keys=['DVT','IP','Code','Name','Sampletime','RTsampletime'],newValues=[self.memoryDVT,None,4,'Test Device 4',600,600])
#         instance=Devices(**newDict)
#         instance.store2DB()
#            
#         from .models import request_callback
#             
#         DGs=Datagrams.objects.filter(DVT=instance.DVT)
#         jobs=instance.getPollingJobIDs()
#             
#         for job in jobs:
#             request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
#            
#         now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
#         latest=instance.getLatestData(localized=False)
#         if latest!=None:
#             for datagram in latest:
#                 for name in latest[datagram]:
#                     if latest[datagram][name]!=None:
#                         if name!='timestamp':
#                             info=Datagrams.getInfoFromItemName(name=name)
#                             if info['type']==DTYPE_DIGITAL:
#                                 for i in range(0,8):
#                                     self.assertEqual(latest[datagram][name]['bit'+str(i)], int(checkBit(number=7,position=i)))
#                             else:
#                                 self.assertIsInstance(latest[datagram][name], type(3.2))
#                         else:
#                             self.assertAlmostEqual(latest[datagram][name],now,delta=datetime.timedelta(seconds=5))
#                 
#         instance.deleteRegistersTables()
#                
#     def test_scan(self):
#         print('## TESTING THE OPERATION OF THE scan PROCEDURE  ##')
#         print('    --> If no device found')
#            
#         stopApache()
#         scan=Devices.scan(FormModel=DevicesForm,IP='127.0.0.1')
#         self.assertEqual(scan['devicetype'], None)
#         self.assertEqual(scan['errors'], [])
#         
#         print('    --> If device found but DVT not found in DB')
#         startApache()
#         scan=Devices.scan(FormModel=DevicesForm,IP='127.0.0.1')
#         stopApache()
#         self.assertEqual(scan['devicetype'], '3xDHT22')
#         self.assertTrue('Unknown Device type:' in scan['errors'][0])
#             
# print('####################################')
# print('# TESTING OF Views MODEL FUNCTIONS #')
# print('####################################') 
#    
# class ViewsTests(TestCase):
#     fixtures=['DevicesAPP.json',]
#        
#     def setUp(self):
#         User = get_user_model()
#         self.testuser=User.objects.create_user(name='testUser', email="testUser@test.com",password='12345')
#         self.testSuperuser=User.objects.create_user(name='testSuperuser', email="testSuperuser@test.com",
#                                                     password='12345',is_superuser=True)
# 
#         self.simpleClient=Client()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#            
#         self.superClient=Client()
#         logged_in = self.superClient.login(username='testSuperuser@test.com', password='12345')
#            
#         group_name = "Permissions"
#         self.group = Group(name=group_name)
#         self.group.save()
#            
#         self.remoteDVT=DeviceTypes.objects.get(pk=1)
#         self.localDVT=DeviceTypes.objects.get(pk=2)
#         self.memoryDVT=DeviceTypes.objects.get(pk=3)
#        
#     # CHECKING THE VIEWS
#     def test_homepage(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/home'
#         print('## TESTING THE ACCESS TO HOMEPAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 301) # permament redirect status
#         self.assertTrue('Devices/home' in response.url) 
#         print('    --> Test to reach as simple user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 301) # permament redirect status
#         self.assertTrue('Devices/home' in response.url) 
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="add_devices")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 301) # found status
#        
#     def test_addDevices(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/add/devices/'
#         print('## TESTING THE ACCESS TO Devices/add/devices PAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url) 
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="add_devices")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#            
#     def test_addDeviceTypes(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/add/devicetypes/'
#         print('## TESTING THE ACCESS TO Devices/add/devicetypes PAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url) 
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="add_devicetypes")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#            
#     def test_setcustomlabels(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/setcustomlabels/1/'
#         print('## TESTING THE ACCESS TO setCustomLabels PAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#        
#     def test_scanDevices(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/scan/devices/'
#         print('## TESTING THE ACCESS TO Devices/scan PAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url) 
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="scan_devices")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         # POSTING WITHOUT A DEVICE
#         response = self.simpleClient.post(url,**{'HTTP_USER_AGENT':TESTS_USER_AGENT})
#         self.assertTrue(SCAN_DEVICENOFOUND in str(response.content))# NO DEVICE FOUND
#         startApache()
#         response = self.simpleClient.post(url,**{'HTTP_USER_AGENT':TESTS_USER_AGENT})# this needs to be modified to poll on a loopback IP instead of the real
#         stopApache()
#         self.assertTrue(SCAN_DEVICEFOUND in str(response.content))# DEVICE FOUND
#            
#     def test_viewAllDevices(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/view_all/devices/'
#         print('## TESTING THE ACCESS TO Devices/view_all PAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url)
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="view_devices")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#        
#     def test_viewAllDevicetypes(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/view_all/devicetypes/'
#         print('## TESTING THE ACCESS TO Devices/view_all PAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url)
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="view_devicetypes")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#            
#     def test_modifyDevices(self):
#         print('## TESTING THE ACCESS TO Devices/modify/devices/ PAGE ##')
#         print('    --> Test to reach as superuser')
#         url='/'+APP_TEMPLATE_NAMESPACE+'/modify/devices/1/'
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url)
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="change_devices")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#        
#     def test_modifyDevicetypes(self):
#         print('## TESTING THE ACCESS TO Devices/modify/devicetypes/ PAGE ##')
#         print('    --> Test to reach as superuser')
#         url='/'+APP_TEMPLATE_NAMESPACE+'/modify/devicetypes/1/'
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url)
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="change_devicetypes")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#            
#     def test_advancedDevicepage(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/advanceddevicepage/1/'
#         print('## TESTING THE ACCESS TO Devices/advancedevicepage PAGE ##')
#         print('    --> Test to reach as superuser')
#         response = self.superClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#         print('    --> Test to reach as unauthorized user')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 302) # redirection to login
#         self.assertTrue('login' in response.url)
#         print('    --> Test to reach as authorized user')
#         permission=Permission.objects.get(codename="view_devices")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#         response = self.simpleClient.get(url)
#         self.assertEqual(response.status_code, 200) # found status
#        
#     def test_async_post(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/async_post/'
#         print('--> Test to reach DevicesAPP async_post page')
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
#         instance=Devices(**newDict)
#         instance.store2DB()
#            
#         file=join(DevicesModelTests.ApacheHTTPpath, 'powers.xml')
#         setupPowersXML(code=2,datagramId=0,status=8,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
#         with open(file) as fp:
#             text=''
#             for line in fp:
#                 text+=line
#             response=self.superClient.post(url, text,content_type="application/txt")
#         resetPowersXML()
#         latest=instance.getLatestData(localized=False)
#         instance.deleteRegistersTables()
#         self.assertEqual(response.status_code, 204) # found but nothing returned status
#         self.assertEqual(latest['1']['1_1_1']['bit3'], 1)
#            
#     def test_addRemoteDeviceProcedure(self):
#         url='/'+APP_TEMPLATE_NAMESPACE+'/add/devices/'
#         print('## TESTING THE ADDITION OF A NEW REMOTE DEVICE ##')
#         response = self.superClient.get(url)
#         from .views import modelSplitter
#         data=modelSplitter(model='devices')
#         Header1='Adding a new ' +data['Header1']
#         Model=data['Model']
#         FormModel=data['FormModel']
#         FormKwargs=data['FormKwargs']
#         message=data['message']
#         lastAction=data['lastAction']
#            
#         permission=Permission.objects.get(codename="add_devices")
#         self.group.permissions.add(permission)
#         self.testuser.groups.add(self.group)
#         self.testuser.save()
#         logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#            
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT.pk,])
#            
#         from utils.BBDD import getRegistersDBInstance
#         DB=getRegistersDBInstance()
#            
#         for client in [self.superClient,self.simpleClient]:
#             print('    --> Test as superuser' if client==self.superClient else '    --> Test as authorized user')
#             form = DevicesForm(newDict, action=FormKwargs['action'])
#             IO=newDict.pop('IO')    # you have to remove extra fields from the dictionary before passing it to the view
#             response = client.post(form.helper.form_action,newDict)
#             self.assertEqual(response.status_code, 200) # form submitted OK
#             self.assertTrue(FORM_ISVALID_MSG in str(response.content)) # Device saved OK
#             instance = Devices.objects.get(Name=newDict['Name'])# Device saved OK
#             self.assertEqual(instance.DVT,self.remoteDVT)# Device saved OK
#             self.assertTrue('setcustomlabels' in str(response.content))# link to page to set custom labels
#             form = DevicesForm(instance=instance, action=data['lastAction'])
#             response = client.get(form.helper.form_action,newDict)
#             self.assertEqual(response.status_code, 200) # CustomLabelsForm page received OK
#             self.assertTrue(instance.Name in str(response.content))# device name found in the page
#             DV=Devices.objects.get(pk=instance.pk)
#             DGs=Datagrams.objects.filter(DVT=instance.DVT)
#             form=DatagramCustomLabelsForm(None,DV=DV,DGs=DGs)
#             response = client.post(form.helper.form_action,form.initial)
#             self.assertEqual(response.status_code, 200) # CustomLabelsForm submitted OK
#             self.assertTrue(DV.Name in str(response.content)) 
#             self.assertTrue(FORM_ISVALID_MSG in str(response.content)) 
#             instance = Devices.objects.get(Name=newDict['Name'])# Device saved OK
#             self.assertTrue(instance.CustomLabels!='')# Custom labels set OK
#             instance.deleteRegistersTables()
#             newDict=editDict(keys=['DVT','Name','Code','IP'],newValues=[self.remoteDVT.pk,'Test Device 3',3,'10.10.10.3'])
#                
#         def test_addDevicetype(self):
#             global DevicetypeDict
#             url='/'+APP_TEMPLATE_NAMESPACE+'/add/devicetypes/'
#             print('## TESTING THE ADDITION OF A NEW DEVICE TYPE ##')
#             response = self.superClient.get(url)
#             from .views import modelSplitter
#             data=modelSplitter(model='devicetypes')
#             Header1='Adding a new ' +data['Header1']
#             Model=data['Model']
#             FormModel=data['FormModel']
#             FormKwargs=data['FormKwargs']
#             message=data['message']
#             lastAction=data['lastAction']
#                
#             permission=Permission.objects.get(codename="add_devicetypes")
#             self.group.permissions.add(permission)
#             self.testuser.groups.add(self.group)
#             self.testuser.save()
#             logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
#                
#             newDict=DevicetypeDict
#                
#             from utils.BBDD import getRegistersDBInstance
#             DB=getRegistersDBInstance()
#                
#             for client in [self.superClient,self.simpleClient]:
#                 print('    --> Test as superuser' if client==self.superClient else '    --> Test as authorized user')
#                 form = DevicetypeForm(newDict, action=FormKwargs['action'])
#                 response = client.post(form.helper.form_action,newDict)
#                 self.assertEqual(response.status_code, 200) # form submitted OK
#                 self.assertTrue(FORM_ISVALID_MSG in str(response.content)) # Devicetype saved OK
#                 instance = Devicetypes.objects.get(Code=newDict['Code'])# Devicetype saved OK
#                 self.assertEqual(instance.Description, newDict['Description']) # form submitted OK
#                 instance.delete()
   
# print('####################################')
# print('# TESTING OF DevicesForm FUNCTIONS #')
# print('####################################')             
# class DevicesFormTests(TestCase):
#     fixtures=['DevicesAPP.json',]
#     remoteDVT=None
#     localDVT=None
#     memoryDVT=None
#          
#     def setUp(self):
#         self.remoteDVT=DeviceTypes.objects.get(pk=1)
#         self.localDVT=DeviceTypes.objects.get(pk=2)
#         self.memoryDVT=DeviceTypes.objects.get(pk=3)
#      
#     def test_init_without_action(self):
#         print('--> test_init_without_action test 0.0: The form assigns action="add" if not an action in kwargs')
#         form=DevicesForm()
# 
#         with self.assertRaises(DevicesAppException):
#             form=DevicesForm(action='unregistered_action')
#                  
#     def test_valid_data(self):
#         print('--> test_valid_data test 1.0: The form is valid with good data')
#         newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT.pk,])
#         form = DevicesForm(newDict, action='add')
#          
#         self.assertTrue(form.is_valid())
#         DV = form.save()
#         for key in newDict:
#             if key!='DVT':
#                 self.assertEqual(getattr(DV,key), newDict[key])
#             else:
#                 self.assertEqual(getattr(DV,key), self.remoteDVT)
