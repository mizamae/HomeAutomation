import datetime
from os.path import dirname, join, exists

from django.utils import timezone
from django.test import TestCase,Client
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission

import webtest

from .constants import DTYPE_DIGITAL,DTYPE_FLOAT,DTYPE_INTEGER,APP_TEMPLATE_NAMESPACE, \
                    FORM_FIRST_RENDER_MSG,FORM_ISVALID_MSG,FORM_ISNOTVALID_MSG,SCAN_DEVICENOFOUND, \
                    SCAN_DEVICEFOUND,TESTS_USER_AGENT,LOCAL_CONNECTION,LINE_PLOT,SPLINE_PLOT,COLUMN_PLOT,AREA_PLOT,\
                    DG_SYNCHRONOUS,DG_ASYNCHRONOUS,\
                    GPIO_DIRECTION_CHOICES,GPIO_OUTPUT,GPIO_INPUT,GPIO_SENSOR,GPIOVALUE_CHOICES,GPIO_HIGH,GPIO_LOW
                    
from .models import Devices,DeviceTypes,Datagrams,DatagramItems,ItemOrdering,MasterGPIOs
from .apps import DevicesAppException
from .forms import DevicesForm,DatagramCustomLabelsForm

P1=None
P2=None

MasterGPIODict={'Pin':17,'Label':'Test Output 1','Direction':GPIO_OUTPUT,'Default':GPIO_HIGH,'Value':GPIO_HIGH}
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
    os.remove(path=file)
    os.rename(src=file_bak,dst=file)

print('############################################')
print('# TESTING OF MasterGPIOs MODEL FUNCTIONS #')
print('############################################')
class MasterGPIOsModelTests(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
        pass

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
# INDIVIDUAL FUNCTIONS TESTING
    def test_store2DB(self):        
        print('## TESTING THE OPERATION OF THE store2DB METHOD ##')
        instance=MasterGPIOs(**MasterGPIODict)
        instance.store2DB()
        self.assertEqual(instance.Value,GPIO_HIGH)
        self.DB.dropTable(table=instance.getRegistersDBTableName())
        
    def test_update_value(self):        
        print('## TESTING THE OPERATION OF THE update_value METHOD ##')
        instance=MasterGPIOs(**MasterGPIODict)
        instance.store2DB()
        print('    -> Tested normal update')
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        instance.update_value(newValue=GPIO_LOW,timestamp=None,writeDB=True,force=False)
        table=instance.getRegistersDBTableName()
        vars='"timestamp","'+instance.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 2'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        self.assertEqual(rows[1][1],GPIO_HIGH)# previous to latest value equals the previous Value
        self.assertEqual(rows[0][1],GPIO_LOW) # latest value equals the newValue
        self.assertEqual(rows[0][0]-rows[1][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
        self.assertAlmostEqual(rows[0][0],now,delta=datetime.timedelta(seconds=1))# checks that the latest value is dated now
        
        print('    -> Tested update with timestamp')
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)+datetime.timedelta(seconds=10)
        instance.update_value(newValue=GPIO_HIGH,timestamp=now,writeDB=True,force=False)
        latest=instance.getLatestData()
        self.assertEqual(latest[instance.getRegistersDBTag()]['timestamp'],now)# latest value is dated now
        self.assertEqual(latest[instance.getRegistersDBTag()]['value'],GPIO_HIGH)# latest value is dated now
        
        self.DB.dropTable(table=instance.getRegistersDBTableName())
    
    def test_IntegrityError(self):
        print('## TESTING THE OPERATION OF THE registers DB Integrity Error handler METHOD ##')
        instance=MasterGPIOs(**MasterGPIODict)
        instance.store2DB()
        newDict=editDict(keys=['Pin','Label'], newValues=[15,'Test Output 2'], Dictionary=MasterGPIODict)
        instance2=MasterGPIOs(**newDict)
        instance2.store2DB()
        
        instance.setLow()
        instance2.setLow()
        self.assertTrue(self.DB.checkIfTableExist(instance.getRegistersDBTableName()))
        self.assertTrue(self.DB.checkIfTableExist(instance2.getRegistersDBTableName()))
        self.DB.dropTable(table=instance.getRegistersDBTableName())
        
    def test_setHigh(self):        
        print('## TESTING THE OPERATION OF THE setHigh METHOD ##')
        newDict=editDict(keys=['Value',], newValues=[GPIO_LOW,], Dictionary=MasterGPIODict)
        instance=MasterGPIOs(**newDict)
        instance.store2DB()
        instance.setHigh()
        self.assertEqual(instance.Value,GPIO_HIGH)# current value equals High
        latest=instance.getLatestData()
        self.assertEqual(latest[instance.getRegistersDBTag()]['value'],GPIO_HIGH)# last value on DB equals High
        self.DB.dropTable(table=instance.getRegistersDBTableName())
    
    def test_setLow(self):        
        print('## TESTING THE OPERATION OF THE setLow METHOD ##')
        newDict=editDict(keys=['Value',], newValues=[GPIO_HIGH,], Dictionary=MasterGPIODict)
        instance=MasterGPIOs(**newDict)
        instance.store2DB()
        instance.setLow()
        self.assertEqual(instance.Value,GPIO_LOW)# current value equals Low
        latest=instance.getLatestData()
        self.assertEqual(latest[instance.getRegistersDBTag()]['value'],GPIO_LOW)# last value on DB equals Low
        self.DB.dropTable(table=instance.getRegistersDBTableName())
        
    def test_str(self):        
        print('## TESTING THE OPERATION OF THE str METHOD ##')
        instance=MasterGPIOs(**MasterGPIODict)
        instance.store2DB()
        self.assertEqual(str(instance),instance.Label + ' on pin ' + str(instance.Pin) )
    
    def test_initializeIOs(self):
        print('## TESTING THE OPERATION OF THE initializeIOs METHOD ##')
        instance=MasterGPIOs(**MasterGPIODict)
        instance.store2DB()
        newDict=editDict(keys=['Pin','Label','Direction'], newValues=[15,'Test Input 1',GPIO_INPUT], Dictionary=MasterGPIODict)
        instance2=MasterGPIOs(**newDict)
        instance2.store2DB()
        
        print('    -> Tested declareInputEvent=True')
        MasterGPIOs.initializeIOs(declareInputEvent=True)
        print('    -> Tested declareInputEvent=False')
        MasterGPIOs.initializeIOs(declareInputEvent=False)
        
print('############################################')
print('# TESTING OF DatagramItems MODEL FUNCTIONS #')
print('############################################')
class DatagramItemsModelTests(TestCase):
    def setUp(self):
        global DatagramItemDict
        pass

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
         
         
# INDIVIDUAL FUNCTIONS TESTING
    def test_clean(self):        
        print('## TESTING THE OPERATION OF THE clean METHOD ##')
        instance=DatagramItems(**DatagramItemDict)
        instance.store2DB()
        self.assertEqual(instance.Units,'bits')
        self.assertEqual(instance.PlotType,LINE_PLOT)
     
    def test_str(self):        
        print('## TESTING THE OPERATION OF THE str METHOD ##')
        instance=DatagramItems(**DatagramItemDict)
        instance.store2DB()
        self.assertEqual(str(instance),DatagramItemDict['Tag'])
     
    def test_getHumanName(self):        
        print('## TESTING THE OPERATION OF THE getHumanName METHOD ##')
        instance=DatagramItems(**DatagramItemDict)
        instance.store2DB()
        self.assertEqual(instance.getHumanName(),DatagramItemDict['Tag']+'_'+instance.Units)
 
print('########################################')
print('# TESTING OF Datagrams MODEL FUNCTIONS #')
print('########################################')
class DatagramsModelTests(TestCase):
    fixtures=['DevicesAPP.json',]
    def setUp(self):
        global DatagramItemDict
        self.remoteDVT=DeviceTypes.objects.get(pk=1)
        self.localDVT=DeviceTypes.objects.get(pk=2)
        self.memoryDVT=DeviceTypes.objects.get(pk=3)
        pass
 
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
         
         
# INDIVIDUAL FUNCTIONS TESTING
    def test_clean(self):        
        print('## TESTING THE OPERATION OF THE save METHOD ##')
        newDict=editDict(keys=['DVT',],newValues=[self.localDVT,],Dictionary=DatagramDict)
         
        DG=Datagrams(**newDict)
        DG.store2DB()
        ITMs=[]
        for k in range(0,3):
            newDict=editDict(keys=['Tag',],newValues=['DigitalItem'+str(k),],Dictionary=DatagramItemDict)
            ITMs.append(DatagramItems(**newDict))
            newDict=editDict(keys=['Tag','DataType'],newValues=['AnalogItem'+str(k),DTYPE_FLOAT],Dictionary=DatagramItemDict)
            ITMs.append(DatagramItems(**newDict))
             
        for i,ITM in enumerate(ITMs):
            ITM.store2DB()
            newDict=editDict(keys=['Order','DG','ITM'],newValues=[i+1,DG,ITM],Dictionary=ItemOrderingDict)
            ITO=ItemOrdering(**newDict)
            ITO.save()
         
        DG=Datagrams.objects.get(Identifier=DatagramDict['Identifier'])
        for i,ITM in enumerate(DG.ITMs.all()):
            self.assertEqual(ITM,ITMs[i])
     
    def test_getDBTypes(self):        
        print('## TESTING THE OPERATION OF THE getDBTypes METHOD ##')
        DG=Datagrams.objects.get(Identifier='instant')
        types=DG.getDBTypes()
        self.assertEqual(types[0],'datetime')
        for type in types[1:]:
            self.assertEqual(type,'analog')
         
        DG=Datagrams.objects.get(Identifier='powers')
        types=DG.getDBTypes()
        self.assertEqual(types[0],'datetime')
        self.assertEqual(types[1],'digital')
        for type in types[2:]:
            self.assertEqual(type,'analog')
     
    def test_getInfoFromItemName(self):        
        print('## TESTING THE OPERATION OF THE getInfoFromItemName METHOD ##')
        with self.assertRaises(DevicesAppException):
            Datagrams.getInfoFromItemName('22_2_1')
            Datagrams.getInfoFromItemName('22_2_1_56')
        info=Datagrams.getInfoFromItemName('1_1_1')
        ITM=DatagramItems.objects.get(pk=1)
        self.assertEqual(info['type'],ITM.DataType)
         
print('######################################')
print('# TESTING OF Devices MODEL FUNCTIONS #')
print('######################################')
      
class DevicesModelTests(TestCase):
    fixtures=['DevicesAPP.json',]
    sensIO=None
    outIO=None
    inIO=None
    remoteDVT=None
    localDVT=None
    memoryDVT=None
    ApacheHTTPpath=r'C:\xampp\htdocs'
              
    def setUp(self):
        self.remoteDVT=DeviceTypes.objects.get(pk=1)
        self.localDVT=DeviceTypes.objects.get(pk=2)
        self.memoryDVT=DeviceTypes.objects.get(pk=3)
        MasterGPIOs(Pin=17,Label='Sensor IO',Direction=GPIO_SENSOR).save()
        self.sensIO=MasterGPIOs.objects.get(Pin=17)
        MasterGPIOs(Pin=18,Label='Output IO',Direction=GPIO_OUTPUT).save()
        self.outIO=MasterGPIOs.objects.get(Pin=18)
        self.inIO=MasterGPIOs(Pin=19,Label='Input IO',Direction=GPIO_INPUT)
        self.inIO.save()
          
    def __init__(self,*args,**kwargs):
        import psutil
        super().__init__(*args,**kwargs)
        if "httpd.exe" in (p.name() for p in psutil.process_iter()):
            stopApache()
         
        print('# TESTING OF Devices MODEL FUNCTIONS #')    
          
# INDIVIDUAL FUNCTIONS TESTING
    def test_errors_on_clean(self):        
        '''
        CHECKS THE ASSERTION OF VALIDATION ERROR WHEN IMPROPER VALUES ARE INTRODUCED
        '''
        print('## TESTING THE OPERATION OF THE clean METHOD ##')
        sampletimes=[600,6,6]
        RTsampletimes=[6,60,6]
        print('    --> Test_errors_on_clean test 0.1: Validation error due to too low Sampletime')
        newDict=editDict(keys=['Sampletime','DVT'],newValues=[6,self.remoteDVT])
        instance=Devices(**newDict)
        self.assertRaises(ValidationError,instance.clean)
          
        print('    --> Test_errors_on_clean test 0.2: Validation error due to too low RTSampletime')
        newDict=editDict(keys=['RTsampletime','DVT'],newValues=[6,self.remoteDVT])
        instance=Devices(**newDict)
        self.assertRaises(ValidationError,instance.clean)
          
        print('    --> Test_errors_on_clean test 0.3: Validation error due to wrong IO')
        IOfake=MasterGPIOs(Pin=17,Label='Test IO',Direction=GPIO_OUTPUT)
        newDict=editDict(keys=['IO','DVT'],newValues=[IOfake,self.localDVT])
        instance=Devices(**newDict)
        self.assertRaises(ValidationError,instance.clean)
  
    def test_OK_on_save(self):
        '''
        CHECKS THE SAVE OPERATION WHEN PROPER VALUES ARE INTRODUCED. 
        ADDITIONALLY, THE REGISTERS TABLES CREATION AND DELETION IS ALSO TESTED AS NEW DEVICE IS SAVED.
        '''            
        print('## TESTING THE OPERATION OF THE save METHOD ##')
        print('    --> Test_OK_on_save test 1.0: With datagrams defined for devicetype')
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        # CHECKED WITH DATAGRAMS DEFINED
        instance.save() # save creates the registers tables
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance()
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        for DG in DGs:
            table=instance.getRegistersDBTableName(DG=DG)
            row=DB.checkIfTableExist(table=table)
            self.assertNotEqual(row,[])
            self.assertEqual(DB.dropTable(table=table),0)
            row=DB.checkIfTableExist(table=table)
            self.assertEqual(row,False)
        instance.delete()
        print('    --> Test_OK_on_save test 1.1: Without datagrams defined for devicetype')
        #CHECKED WITHOUT DATAGRAMS DEFINED
        Datagrams.objects.filter(DVT=self.localDVT).delete()
        newDict=editDict(keys=['DVT',],newValues=[self.localDVT,])
        instance=Devices(**newDict)
        instance.save() # save creates the registers tables
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        self.assertQuerysetEqual(DGs,[])
 
 
    def test_request_datagram(self):
        '''
        CHECKS THE REQUEST TO DATAGRAM
        '''
        import psutil
        print('## TESTING THE OPERATION OF THE request_datagram METHOD ##')
        print('    --> Test_request_datagram test 2.0: Reception with writeDB=False')
           
        stopApache()
        instance=Devices.objects.get(pk=1)
          
        datagram=instance.request_datagram(DatagramId='powers',timeout=1,writeToDB=False,resetOrder=True,retries=1)
           
        if not "httpd.exe" in (p.name() for p in psutil.process_iter()):
            print('        Tested comm timeout and retrying')
            self.assertIn('Finished retrying',datagram['Error'])
           
        startApache()
        instance.IP='127.0.0.1'
        instance.save()
        setupPowersXML(code=1,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
        datagram=instance.request_datagram(DatagramId='powers',timeout=1,writeToDB=False,resetOrder=True,retries=1)
        resetPowersXML()
              
        if "httpd.exe" in (p.name() for p in psutil.process_iter()):
            print('        Tested comm OK')
            self.assertEqual(datagram['values'], [7,3.25,3.24,3.258])
        stopApache()
  
    def test_getLatestData(self):
        '''
        CHECKS THE RETRIEVAL OF THE LATETS DATA FROM THE REGISTER'S DB
        '''
        print('## TESTING THE OPERATION OF THE getLatestData METHOD ##')
        print('    --> Test_getLatestData test 3.0: Retrieval of latest data from registers DB with CustomLabels defined')
        pk=1
        # run with CustomLabels defined
        instance=Devices.objects.get(pk=pk)
        latest=instance.getLatestData()
        #print(str(latest))
        self.assertEqual(latest['1']['2_1_1'], 3.25)
        for datagram in latest:
            for name in latest[datagram]:
                if name!='timestamp':
                    info=Datagrams.getInfoFromItemName(name=name)
                    if info['type']==DTYPE_DIGITAL:
                        self.assertEqual(latest[datagram][name]['bit2'], 1)
                    elif info['type']==DTYPE_FLOAT:
                        self.assertIsInstance(latest[datagram][name], type(3.2))
                    elif info['type']==DTYPE_INTEGER:
                        self.assertIsInstance(latest[datagram][name], type(3))
        print('    --> Test_getLatestData test 3.1: Retrieval of latest data from registers DB with CustomLabels undefined')
        # run with CustomLabels empty
        prev=instance.CustomLabels
        instance.CustomLabels=''
        instance.save()
        latest=instance.getLatestData()
        #print(str(latest))
        for datagram in latest:
            for name in latest[datagram]:
                if name!='timestamp':
                    info=Datagrams.getInfoFromItemName(name=name)
                    if info['type']==DTYPE_DIGITAL:
                        self.assertEqual(latest[datagram][name]['bit2'], 1)
                    elif info['type']==DTYPE_FLOAT:
                        self.assertIsInstance(latest[datagram][name], type(3.2))
                    elif info['type']==DTYPE_INTEGER:
                        self.assertIsInstance(latest[datagram][name], type(3))
        print('    --> Test_getLatestData test 3.2: Retrieval of latest data from registers DB with CustomLabels undefined and no registers')
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.save()
        latest=instance.getLatestData()
        #print(str(latest))
        for datagram in latest:
            for name in latest[datagram]:
                if name!='timestamp':
                    info=Datagrams.getInfoFromItemName(name=name)
                    if info['type']==DTYPE_DIGITAL:
                        self.assertEqual(latest[datagram][name], None)
                    elif info['type']==DTYPE_FLOAT:
                        self.assertEqual(latest[datagram][name], None)
                    elif info['type']==DTYPE_INTEGER:
                        self.assertEqual(latest[datagram][name], None)
  
    def test_getDeviceVariables(self):
        print('## TESTING THE OPERATION OF THE getDeviceVariables METHOD ##')
        print('    --> Test_getDeviceVariables test 4.0: Retrieval of devices variables with CustomLabels defined')
        pk=1
        # run with CustomLabels defined
        instance=Devices.objects.get(pk=pk)
        variables=instance.getDeviceVariables()
        #print(str(variables))
        for variable in variables:
            info=Datagrams.getInfoFromItemName(name=variable['name'])
            self.assertEqual(variable['device'],pk)
            self.assertEqual(variable['table'].split('_')[0],str(pk))
            if info['type']==DTYPE_DIGITAL:
                self.assertIsInstance(variable['bit'], type(3))
                self.assertEqual(variable['label'],'Error '+str(variable['bit']))
            else:
                self.assertEqual(variable['bit'],None)
                self.assertIsInstance(variable['name'],type(''))
                self.assertIsInstance(variable['label'],type(''))
        print('    --> Test_getDeviceVariables test 4.1: Retrieval of devices variables with CustomLabels undefined')
        # run with CustomLabels empty
        prev=instance.CustomLabels
        instance.CustomLabels=''
        instance.save()
        variables=instance.getDeviceVariables()
        #print(str(variables))
        for variable in variables:
            info=Datagrams.getInfoFromItemName(name=variable['name'])
            self.assertEqual(variable['table'].split('_')[0],str(pk))
            self.assertEqual(variable['device'],pk)
            if info['type']==DTYPE_DIGITAL:
                self.assertIsInstance(variable['bit'], type(3))
                self.assertEqual(variable['label'],variable['name']+' bit '+str(variable['bit']))
            else:
                self.assertEqual(variable['bit'],None)
        instance.CustomLabels=prev
        instance.save()
  
    def test_getRegistersTables(self):
        print('## TESTING THE OPERATION OF THE getRegistersTables METHOD ##')
        print('    --> Retrieval of devices tables on registers DB')
        pk=1
        # run with CustomLabels defined
        instance=Devices.objects.get(pk=pk)
        tables=instance.getRegistersTables()
        self.assertEqual(tables,['1_1','1_2'])
  
    def test_setCustomLabels(self):
        print('## TESTING THE OPERATION OF THE setCustomLabels METHOD ##')
        print('    --> Modifies the value of the CustomLabels field')
        import json
        pk=1
        # run with CustomLabels undefined
        instance=Devices.objects.get(pk=pk)
        prev=instance.CustomLabels
        instance.CustomLabels=''
        instance.save()
        instance.setCustomLabels()
        CustomLabels=json.loads(instance.CustomLabels)
        for datagram in CustomLabels:
            for name in CustomLabels[datagram]:
                info=Datagrams.getInfoFromItemName(name=name)
                self.assertEqual(CustomLabels[datagram][name],info['human'])
  
    def test_update_requests(self):
        print('## TESTING THE OPERATION OF THE update_requests METHOD ##')
        print('    --> Starts/Stops polling of device and checks scheduler')
        from .constants import RUNNING_STATE,STOPPED_STATE
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.save()
        instance.startPolling()
        self.assertEqual(instance.State,RUNNING_STATE)
        jobs=instance.getPollingJobIDs()
        for job in jobs:
            scheduler=Devices.getScheduler()
            JOB=scheduler.getJobInStore(jobId=job['id'])
            self.assertIsNot(JOB,None)
              
        instance.stopPolling()
        self.assertEqual(instance.State,STOPPED_STATE)
        jobs=instance.getPollingJobIDs()
        for job in jobs:
            scheduler=Devices.getScheduler()
            JOB=scheduler.getJobInStore(jobId=job['id'])
            self.assertEqual(JOB,None)
        instance.deleteRegistersTables()
  
    def test_setNextUpdate(self):
        print('## TESTING THE OPERATION OF THE setNextUpdate METHOD ##')
        print('    --> Sets the next update time for a device')
        import datetime
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.save()
        instance.startPolling()
        now=datetime.datetime.now().replace(microsecond=0)
        jobs=instance.getPollingJobIDs()
        numJobs=len(jobs)
        offset=instance.Sampletime/numJobs
        for i,job in enumerate(jobs):
            nextUpdate=instance.setNextUpdate(jobID=job['id']).replace(microsecond=0).replace(tzinfo=None)
            self.assertAlmostEqual(nextUpdate,now+datetime.timedelta(seconds=i*offset+instance.Sampletime/2),delta=datetime.timedelta(seconds=1))
        instance.deleteRegistersTables()
  
    def test_request_callback(self):
        print('## TESTING THE OPERATION OF THE request_callback PROCEDURE  ##')
        import time
        import datetime
        from utils.dataMangling import checkBit
        from utils.BBDD import getRegistersDBInstance
        print('    --> On a remote device')
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.save()
         
        startApache()
        setupPowersXML(code=2,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
          
        from .models import request_callback
          
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        jobs=instance.getPollingJobIDs()
          
        for job in jobs:
            request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
         
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        resetPowersXML()
        latest=instance.getLatestData()
        for datagram in latest:
            for name in latest[datagram]:
                if latest[datagram][name]!=None:
                    if name!='timestamp':
                        info=Datagrams.getInfoFromItemName(name=name)
                        if info['type']==DTYPE_DIGITAL:
                            for i in range(0,8):
                                self.assertEqual(latest[datagram][name]['bit'+str(i)], int(checkBit(number=7,position=i)))
                        else:
                            self.assertIsInstance(latest[datagram][name], type(3.2))
                    else:
                        self.assertAlmostEqual(latest[datagram][name],now,delta=datetime.timedelta(seconds=5))
          
        stopApache()
              
        instance.deleteRegistersTables()
         
        print('    --> On a local device')
        newDict=editDict(keys=['DVT','IP','Code','Name','IO'],newValues=[self.localDVT,None,3,'Test Device 3',self.sensIO])
        instance=Devices(**newDict)
        instance.save()
         
        from .models import request_callback
          
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        jobs=instance.getPollingJobIDs()
          
        for job in jobs:
            request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
         
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        latest=instance.getLatestData()
        if latest!=None:
            for datagram in latest:
                for name in latest[datagram]:
                    if latest[datagram][name]!=None:
                        if name!='timestamp':
                            info=Datagrams.getInfoFromItemName(name=name)
                            if info['type']==DTYPE_DIGITAL:
                                for i in range(0,8):
                                    self.assertEqual(latest[datagram][name]['bit'+str(i)], int(checkBit(number=7,position=i)))
                            else:
                                self.assertIsInstance(latest[datagram][name], type(3.2))
                        else:
                            self.assertAlmostEqual(latest[datagram][name],now,delta=datetime.timedelta(seconds=5))
              
        instance.deleteRegistersTables()
         
        print('    --> On a memory device')
        newDict=editDict(keys=['DVT','IP','Code','Name'],newValues=[self.memoryDVT,None,4,'Test Device 4'])
        instance=Devices(**newDict)
        instance.save()
         
        from .models import request_callback
          
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        jobs=instance.getPollingJobIDs()
          
        for job in jobs:
            request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
         
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        latest=instance.getLatestData()
        if latest!=None:
            for datagram in latest:
                for name in latest[datagram]:
                    if latest[datagram][name]!=None:
                        if name!='timestamp':
                            info=Datagrams.getInfoFromItemName(name=name)
                            if info['type']==DTYPE_DIGITAL:
                                for i in range(0,8):
                                    self.assertEqual(latest[datagram][name]['bit'+str(i)], int(checkBit(number=7,position=i)))
                            else:
                                self.assertIsInstance(latest[datagram][name], type(3.2))
                        else:
                            self.assertAlmostEqual(latest[datagram][name],now,delta=datetime.timedelta(seconds=5))
              
        instance.deleteRegistersTables()
             
    def test_scan(self):
        print('## TESTING THE OPERATION OF THE scan PROCEDURE  ##')
        print('    --> Makes a polling through the scheduler simulating booting conditions')
         
        stopApache()
        scan=Devices.scan(FormModel=DevicesForm,IP='127.0.0.1')
        self.assertEqual(scan['devicetype'], None)
        self.assertEqual(scan['errors'], [])
          
        startApache()
        scan=Devices.scan(FormModel=DevicesForm,IP='127.0.0.1')
        stopApache()
        self.assertEqual(scan['devicetype'], '3xDHT22')
        self.assertTrue('Unknown Device type:' in scan['errors'][0])
          
print('####################################')
print('# TESTING OF Views MODEL FUNCTIONS #')
print('####################################') 
 
class ViewsTests(TestCase):
    fixtures=['DevicesAPP.json',]
     
    def setUp(self):
        User = get_user_model()
        self.testuser=User.objects.create_user(name='testUser', email="testUser@test.com",password='12345')
        self.testSuperuser=User.objects.create_user(name='testSuperuser', email="testSuperuser@test.com",
                                                    password='12345',is_superuser=True)
         
        self.simpleClient=Client()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
         
        self.superClient=Client()
        logged_in = self.superClient.login(username='testSuperuser@test.com', password='12345')
         
        group_name = "Permissions"
        self.group = Group(name=group_name)
        self.group.save()
         
        self.remoteDVT=DeviceTypes.objects.get(pk=1)
        self.localDVT=DeviceTypes.objects.get(pk=2)
        self.memoryDVT=DeviceTypes.objects.get(pk=3)
     
    # CHECKING THE VIEWS
    def test_homepage(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/home'
        print('## TESTING THE ACCESS TO HOMEPAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 301) # permament redirect status
        self.assertTrue('Devices/home' in response.url) 
        print('    --> Test to reach as simple user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 301) # permament redirect status
        self.assertTrue('Devices/home' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="add_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 301) # found status
     
    def test_addDevices(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/add/devices/'
        print('## TESTING THE ACCESS TO Devices/add/devices PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="add_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
         
    def test_addDeviceTypes(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/add/devicetypes/'
        print('## TESTING THE ACCESS TO Devices/add/devicetypes PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="add_devicetypes")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
         
    def test_setcustomlabels(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/setcustomlabels/1/'
        print('## TESTING THE ACCESS TO setCustomLabels PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
     
    def test_scanDevices(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/scan/devices/'
        print('## TESTING THE ACCESS TO Devices/scan PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="scan_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        # POSTING WITHOUT A DEVICE
        response = self.simpleClient.post(url,**{'HTTP_USER_AGENT':TESTS_USER_AGENT})
        self.assertTrue(SCAN_DEVICENOFOUND in str(response.content))# NO DEVICE FOUND
        startApache()
        response = self.simpleClient.post(url,**{'HTTP_USER_AGENT':TESTS_USER_AGENT})# this needs to be modified to poll on a loopback IP instead of the real
        stopApache()
        self.assertTrue(SCAN_DEVICEFOUND in str(response.content))# DEVICE FOUND
         
    def test_viewAllDevices(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/view_all/devices/'
        print('## TESTING THE ACCESS TO Devices/view_all PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="view_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
     
    def test_viewAllDevicetypes(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/view_all/devicetypes/'
        print('## TESTING THE ACCESS TO Devices/view_all PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="view_devicetypes")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
         
    def test_modifyDevices(self):
        print('## TESTING THE ACCESS TO Devices/modify/devices/ PAGE ##')
        print('    --> Test to reach as superuser')
        url='/'+APP_TEMPLATE_NAMESPACE+'/modify/devices/1/'
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="change_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
     
    def test_modifyDevicetypes(self):
        print('## TESTING THE ACCESS TO Devices/modify/devicetypes/ PAGE ##')
        print('    --> Test to reach as superuser')
        url='/'+APP_TEMPLATE_NAMESPACE+'/modify/devicetypes/1/'
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="change_devicetypes")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
         
    def test_advancedDevicepage(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/advanceddevicepage/1/'
        print('## TESTING THE ACCESS TO Devices/advancedevicepage PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="view_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
     
    def test_async_post(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/async_post/'
        print('--> Test to reach DevicesAPP async_post page')
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.save()
         
        file=join(DevicesModelTests.ApacheHTTPpath, 'powers.xml')
        setupPowersXML(code=2,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
        with open(file) as fp:
            text=''
            for line in fp:
                text+=line
            response=self.superClient.post(url, text,content_type="application/txt")
        resetPowersXML()
        instance.deleteRegistersTables()
        self.assertEqual(response.status_code, 204) # found but nothing returned status
         
    def test_addRemoteDeviceProcedure(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/add/devices/'
        print('## TESTING THE ADDITION OF A NEW REMOTE DEVICE ##')
        response = self.superClient.get(url)
        from .views import modelSplitter
        data=modelSplitter(model='devices')
        Header1='Adding a new ' +data['Header1']
        Model=data['Model']
        FormModel=data['FormModel']
        FormKwargs=data['FormKwargs']
        message=data['message']
        lastAction=data['lastAction']
         
        permission=Permission.objects.get(codename="add_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
         
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT.pk,])
         
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance()
         
        for client in [self.superClient,self.simpleClient]:
            print('    --> Test as superuser' if client==self.superClient else '    --> Test as authorized user')
            form = DevicesForm(newDict, action=FormKwargs['action'])
            IO=newDict.pop('IO')    # you have to remove extra fields from the dictionary before passing it to the view
            response = client.post(form.helper.form_action,newDict)
            self.assertEqual(response.status_code, 200) # form submitted OK
            self.assertTrue(FORM_ISVALID_MSG in str(response.content)) # Device saved OK
            instance = Devices.objects.get(Name=newDict['Name'])# Device saved OK
            self.assertEqual(instance.DVT,self.remoteDVT)# Device saved OK
            self.assertTrue('setcustomlabels' in str(response.content))# link to page to set custom labels
            form = DevicesForm(instance=instance, action=data['lastAction'])
            response = client.get(form.helper.form_action,newDict)
            self.assertEqual(response.status_code, 200) # CustomLabelsForm page received OK
            self.assertTrue(instance.Name in str(response.content))# device name found in the page
            DV=Devices.objects.get(pk=instance.pk)
            DGs=Datagrams.objects.filter(DVT=instance.DVT)
            form=DatagramCustomLabelsForm(None,DV=DV,DGs=DGs)
            response = client.post(form.helper.form_action,form.initial)
            self.assertEqual(response.status_code, 200) # CustomLabelsForm submitted OK
            self.assertTrue(DV.Name in str(response.content)) 
            self.assertTrue(FORM_ISVALID_MSG in str(response.content)) 
            instance = Devices.objects.get(Name=newDict['Name'])# Device saved OK
            self.assertTrue(instance.CustomLabels!='')# Custom labels set OK
            instance.deleteRegistersTables()
            newDict=editDict(keys=['DVT','Name','Code','IP'],newValues=[self.remoteDVT.pk,'Test Device 3',3,'10.10.10.3'])
             
        def test_addDevicetype(self):
            global DevicetypeDict
            url='/'+APP_TEMPLATE_NAMESPACE+'/add/devicetypes/'
            print('## TESTING THE ADDITION OF A NEW DEVICE TYPE ##')
            response = self.superClient.get(url)
            from .views import modelSplitter
            data=modelSplitter(model='devicetypes')
            Header1='Adding a new ' +data['Header1']
            Model=data['Model']
            FormModel=data['FormModel']
            FormKwargs=data['FormKwargs']
            message=data['message']
            lastAction=data['lastAction']
             
            permission=Permission.objects.get(codename="add_devicetypes")
            self.group.permissions.add(permission)
            self.testuser.groups.add(self.group)
            self.testuser.save()
            logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
             
            newDict=DevicetypeDict
             
            from utils.BBDD import getRegistersDBInstance
            DB=getRegistersDBInstance()
             
            for client in [self.superClient,self.simpleClient]:
                print('    --> Test as superuser' if client==self.superClient else '    --> Test as authorized user')
                form = DevicetypeForm(newDict, action=FormKwargs['action'])
                response = client.post(form.helper.form_action,newDict)
                self.assertEqual(response.status_code, 200) # form submitted OK
                self.assertTrue(FORM_ISVALID_MSG in str(response.content)) # Devicetype saved OK
                instance = Devicetypes.objects.get(Code=newDict['Code'])# Devicetype saved OK
                self.assertEqual(instance.Description, newDict['Description']) # form submitted OK
                instance.delete()
 
print('####################################')
print('# TESTING OF DevicesForm FUNCTIONS #')
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
#         print('--> test_init_without_action test 0.0: The form raises error if not a valid action in kwargs')
#         with self.assertRaises(KeyError):
#             form=DevicesForm()
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