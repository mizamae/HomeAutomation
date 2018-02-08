from .test_utils import *
from MainAPP.signals import SignalAutomationVariablesValueUpdated

print('######################################')
print('# TESTING OF Devices MODEL FUNCTIONS #')
print('######################################')

@tag('devices')
class DevicesModelTests(TestCase):
    fixtures=['DevicesAPP.json',]
    sensIO=None
    outIO=None
    inIO=None
    remoteDVT=None
    localDVT=None
    memoryDVT=None
    DB=None
    
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
         
        self.DB=getRegistersDBInstance()
        self.remoteDVT=DeviceTypes.objects.get(pk=1)
        self.localDVT=DeviceTypes.objects.get(pk=2)
        self.memoryDVT=DeviceTypes.objects.get(pk=3)
        MasterGPIOs(Pin=17,Label='Sensor IO',Direction=GPIO_SENSOR).save()
        self.sensIO=MasterGPIOs.objects.get(Pin=17)
        MasterGPIOs(Pin=18,Label='Output IO',Direction=GPIO_OUTPUT).save()
        self.outIO=MasterGPIOs.objects.get(Pin=18)
        self.inIO=MasterGPIOs(Pin=19,Label='Input IO',Direction=GPIO_INPUT)
        self.inIO.save()
        self.signal_was_called = False
        self.signaltimestamp=None
        self.signalTags=None
        self.signalValues=None
        def handler(sender, **kwargs):
            self.signal_was_called = True
            self.signaltimestamp=kwargs['timestamp']
            self.signalTags=kwargs['Tags']
            self.signalValues=kwargs['Values']
        
        self.handler=handler
        
             
    def __init__(self,*args,**kwargs):
        import psutil
        super().__init__(*args,**kwargs)
        if "httpd.exe" in (p.name() for p in psutil.process_iter()):
            stopApache()
        from utils.BBDD import createTSTDB
        createTSTDB()
             
# INDIVIDUAL FUNCTIONS TESTING
    def test_getCharts(self):
        print('## TESTING THE OPERATION OF THE getCharts METHOD ##')
        import time
        print('    -> Tested with valid records in the DB')
        local_tz=get_localzone()
          
        dateIni=(timezone.now()-datetime.timedelta(hours=1)).replace(microsecond=0)
  
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.save()
          
        instance.deleteRegistersTables()
          
        dateEnd=timezone.now().replace(microsecond=0)
          
        timestamps= [dateIni + datetime.timedelta(minutes=x) for x in range(0, 70,10)]
        values=[[7,3.25,0.5,3.5],[220.5,]]
          
        for ts in timestamps:
            instance.insertRegister(TimeStamp=ts,DatagramId='powers',year=dateIni.year,values=values[0],NULL=False)
            instance.insertRegister(TimeStamp=ts,DatagramId='instant',year=dateIni.year,values=values[1],NULL=False)
  
        charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
        for k,chart in enumerate(charts):
            title=chart['title']
              
            self.assertTrue(len(chart['rows'])==len(timestamps))
            for i,col in enumerate(chart['cols'][0]):
                self.assertTrue('label' in col)
                self.assertTrue('type' in col)
                self.assertTrue('plottype' in col)
                if col['type']==DTYPE_DIGITAL:
                    self.assertTrue(chart['rows'][0][i]==[1,1,1,0,0,0,0,0])
                elif col['type']!='datetime':
                    self.assertEqual(chart['rows'][0][i],values[k][i-1]) 
          
        print('    -> Tested with no records in the solicited timespan but yes in the DB')
        dateIni=(timezone.now()+datetime.timedelta(seconds=1)).replace(microsecond=0)
        dateEnd=(dateIni+datetime.timedelta(hours=1)).replace(microsecond=0)
        charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
        for chart in charts:
            title=chart['title']
            self.assertTrue(len(chart['rows'])==2) # there are 2 rows with data dated at dateIni and dateEnd resp.
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][0][0]/1000,tz=local_tz),dateIni,delta=datetime.timedelta(seconds=1))# checks that the first row is dated as dateIni
            self.assertAlmostEqual(datetime.datetime.fromtimestamp(chart['rows'][1][0]/1000,tz=local_tz),dateEnd,delta=datetime.timedelta(seconds=1))# checks that the second row is dated as dateEnd
              
        instance.deleteRegistersTables()
          
        print('    -> Tested with no table in the DB')
        charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
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
              
        print('    -> Tested with empty table in the DB')
        instance.checkRegistersDB(Database=self.DB)
        tables=instance.getRegistersTables()
        for table in tables:
            self.assertTrue(self.DB.checkIfTableExist(table=table))
        charts=instance.getCharts(fromDate=dateIni,toDate=dateEnd)
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
              
        instance.deleteRegistersTables()
          
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
     
    def test_store2DB(self):
        '''
        CHECKS THE SAVE OPERATION WHEN PROPER VALUES ARE INTRODUCED. 
        ADDITIONALLY, THE REGISTERS TABLES CREATION AND DELETION IS ALSO TESTED AS NEW DEVICE IS SAVED.
        '''            
        print('## TESTING THE OPERATION OF THE store2DB METHOD ##')
        print('    --> Test_OK_on_save test 1.0: With datagrams defined for devicetype')
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        # CHECKED WITH DATAGRAMS DEFINED
        instance.store2DB() # creates the registers tables
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
        newDict=editDict(keys=['DVT','Sampletime','RTsampletime'],newValues=[self.localDVT,600,60])
        instance=Devices(**newDict)
        instance.store2DB() # save creates the registers tables
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        self.assertQuerysetEqual(DGs,[])
 
    def test_requestDatagram(self):
        '''
        CHECKS THE REQUEST TO DATAGRAM
        '''
        import psutil
        print('## TESTING THE OPERATION OF THE requestDatagram METHOD ##')
        print('    --> Test_requestDatagram test 2.0: Reception with writeDB=False')
              
        stopApache()
        instance=Devices.objects.get(pk=1)
             
        datagram=instance.requestDatagram(DatagramId='powers',timeout=1,writeToDB=False,resetOrder=True,retries=1)
              
        if not "httpd.exe" in (p.name() for p in psutil.process_iter()):
            print('        Tested comm timeout and retrying')
            self.assertIn('Finished retrying',datagram['Error'])
              
        startApache()
        instance.IP='127.0.0.1'
        instance.save()
        setupPowersXML(code=1,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
        datagram=instance.requestDatagram(DatagramId='powers',timeout=1,writeToDB=False,resetOrder=True,retries=1)
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
        latest=instance.getLatestData(localized=False)
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
        instance.store2DB()
        latest=instance.getLatestData(localized=False)
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
        instance.store2DB()
        latest=instance.getLatestData(localized=False)
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
            self.assertEqual(variable['device'],str(pk))
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
            self.assertEqual(variable['device'],str(pk))
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
     
    def test_updateRequests(self):
        print('## TESTING THE OPERATION OF THE update_requests METHOD ##')
        print('    --> Starts/Stops polling of device and checks scheduler')
        from .constants import RUNNING_STATE,STOPPED_STATE
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.store2DB()
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
        instance.store2DB()
            
        startApache()
        setupPowersXML(code=2,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
             
        from .models import request_callback
             
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        jobs=instance.getPollingJobIDs()
        
        SignalAutomationVariablesValueUpdated.connect(self.handler)
        
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        for job in jobs:
            request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
            # checks values from the signal
            self.assertAlmostEqual(self.signaltimestamp.replace(tzinfo=None),now,delta=datetime.timedelta(seconds=1))# signal timestamp value is dated now
            if job['DG'].Identifier=='powers':
                self.assertEqual(self.signalValues,[7,3.25,3.24,3.258])
            else:
                self.assertEqual(self.signalValues,[238])
            datagram=job['DG'].getStructure()
            self.assertEqual(self.signalTags,datagram['names'])
            
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        resetPowersXML()
        latest=instance.getLatestData(localized=False)
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
        SignalAutomationVariablesValueUpdated.disconnect(self.handler)
        instance.deleteRegistersTables()
            
        print('    --> On a local device')
        newDict=editDict(keys=['DVT','IP','Code','Name','IO','Sampletime','RTsampletime'],newValues=[self.localDVT,None,3,'Test Device 3',self.sensIO,600,60])
        instance=Devices(**newDict)
        instance.store2DB()
            
        from .models import request_callback
             
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        jobs=instance.getPollingJobIDs()
             
        for job in jobs:
            request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
            
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        latest=instance.getLatestData(localized=False)
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
        newDict=editDict(keys=['DVT','IP','Code','Name','Sampletime','RTsampletime'],newValues=[self.memoryDVT,None,4,'Test Device 4',600,600])
        instance=Devices(**newDict)
        instance.store2DB()
            
        from .models import request_callback
             
        DGs=Datagrams.objects.filter(DVT=instance.DVT)
        jobs=instance.getPollingJobIDs()
             
        for job in jobs:
            request_callback(DV=instance,DG=job['DG'],jobID=job['id'])
            
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        latest=instance.getLatestData(localized=False)
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
        print('    --> If no device found')
            
        stopApache()
        scan=Devices.scan(FormModel=DevicesForm,IP='127.0.0.1')
        self.assertEqual(scan['devicetype'], None)
        self.assertEqual(scan['errors'], [])
         
        print('    --> If device found but DVT not found in DB')
        startApache()
        scan=Devices.scan(FormModel=DevicesForm,IP='127.0.0.1')
        stopApache()
        self.assertEqual(scan['devicetype'], '3xDHT22')
        self.assertTrue('Unknown Device type:' in scan['errors'][0])
 
print('####################################')
print('# TESTING OF DevicesForm FUNCTIONS #')
print('####################################')

@tag('devices')
class DevicesFormTests(TestCase):
    fixtures=['DevicesAPP.json',]
    remoteDVT=None
    localDVT=None
    memoryDVT=None
          
    def setUp(self):
        self.remoteDVT=DeviceTypes.objects.get(pk=1)
        self.localDVT=DeviceTypes.objects.get(pk=2)
        self.memoryDVT=DeviceTypes.objects.get(pk=3)
      
    def test_init_without_action(self):
        print('--> test_init_without_action test 0.0: The form assigns action="add" if not an action in kwargs')
        form=DevicesForm()
 
        with self.assertRaises(DevicesAppException):
            form=DevicesForm(action='unregistered_action')
                  
    def test_valid_data(self):
        print('--> test_valid_data test 1.0: The form is valid with good data')
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT.pk,])
        form = DevicesForm(newDict, action='add')
          
        self.assertTrue(form.is_valid())
        DV = form.save()
        for key in newDict:
            if key!='DVT':
                self.assertEqual(getattr(DV,key), newDict[key])
            else:
                self.assertEqual(getattr(DV,key), self.remoteDVT)