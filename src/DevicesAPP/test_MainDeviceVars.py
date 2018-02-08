from .test_utils import *
from MainAPP.signals import SignalAutomationVariablesValueUpdated

print('#############################################')
print('# TESTING OF MainDeviceVars MODEL FUNCTIONS #')
print('#############################################')

@tag('maindevicevars')
class MainDeviceVarsModelTests(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
        self.DB.dropTable(table='MainVariables')
        self.signal_was_called = False
        self.signaltimestamp=None
        self.signalTag=None
        self.signalValue=None
        def handler(sender, **kwargs):
            self.signal_was_called = True
            self.signaltimestamp=kwargs['timestamp']
            self.signalTag=kwargs['Tags'][0]
            self.signalValue=kwargs['Values'][0]
        
        self.handler=handler
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
        SignalAutomationVariablesValueUpdated.connect(self.handler)
        instance=MainDeviceVars(**MainDeviceVarDict)
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        instance.store2DB()
        SignalAutomationVariablesValueUpdated.disconnect(self.handler)
        # checks values from the signal
        self.assertAlmostEqual(self.signaltimestamp,timezone.now().replace(microsecond=0),delta=datetime.timedelta(seconds=1))# signal timestamp value is dated now
        self.assertEqual(self.signalValue,MainDeviceVarDict['Value'])
        self.assertEqual(self.signalTag,str(instance.pk))
        # checks that store2DB creates the corresponding table in the registers DB and introduces a first record with the current value         
        self.assertEqual(instance.Value,MainDeviceVarDict['Value'])
        self.assertTrue(self.DB.checkIfTableExist(table=instance.getRegistersDBTableName()))
        latest=instance.getLatestData(localized=False)
        self.assertAlmostEqual(latest[instance.getRegistersDBTag()]['timestamp'],now,delta=datetime.timedelta(seconds=1))# latest value is dated now
        self.assertEqual(latest[instance.getRegistersDBTag()]['value'],MainDeviceVarDict['Value'])# latest value is the same as in the dict
        self.DB.dropTable(table=instance.getRegistersDBTableName())
         
    def test_updateValue(self):
        '''
        updateValue: method that handles the creation of registers DB rows. It has several alternative operational paths:
            - The standard one is when the pre-initialized parameters are defaulted. In this situation, it checks if newValue is different from the previous one
            and in case so, it introduces a row with the previous value, and a second one with the newValue. Both these rows are separated 1 second in the timestamps
            to provide step-like plots.
            - If a timestamp is provided, only one row is created with the passed timestamp if and only if newValue is different from the previous one.
            - If force=True, it generates the row independently of the newValue.
            Independently of the operational path followed, this method also sets up the value of the GPIO in case it is an output.
        '''
        print('## TESTING THE OPERATION OF THE updateValue METHOD ##')
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.save() # to avoid the creation of the DB tables and insertion of the first row that function store2DB does...
        print('    -> Tested standard path')
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        
        SignalAutomationVariablesValueUpdated.connect(self.handler)
        instance.updateValue(newValue=22,timestamp=None,writeDB=True,force=False)
        SignalAutomationVariablesValueUpdated.disconnect(self.handler)
        # checks values from the signal
        self.assertAlmostEqual(self.signaltimestamp,timezone.now().replace(microsecond=0),delta=datetime.timedelta(seconds=1))# signal timestamp value is dated now
        self.assertEqual(self.signalValue,instance.Value)
        self.assertEqual(self.signalTag,str(instance.pk))
        
        table=instance.getRegistersDBTableName()
        vars='"timestamp","'+instance.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 2'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        self.assertEqual(rows[1][1],MainDeviceVarDict['Value'])# previous to latest value equals the previous Value
        self.assertEqual(rows[0][1],22) # latest value equals the newValue
        self.assertEqual(rows[0][0]-rows[1][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
        self.assertAlmostEqual(rows[0][0],now,delta=datetime.timedelta(seconds=1))# checks that the latest value is dated now
          
        print('    -> Tested update with timestamp')
        now=timezone.now().replace(microsecond=0)+datetime.timedelta(seconds=10)
        SignalAutomationVariablesValueUpdated.connect(self.handler)
        instance.updateValue(newValue=21,timestamp=now,writeDB=True,force=False)
        SignalAutomationVariablesValueUpdated.disconnect(self.handler)
        # checks values from the signal
        self.assertAlmostEqual(self.signaltimestamp,timezone.now()+datetime.timedelta(seconds=10),delta=datetime.timedelta(seconds=1))# signal timestamp value is dated now
        self.assertEqual(self.signalValue,instance.Value)
        self.assertEqual(self.signalTag,str(instance.pk))
        
        latest=instance.getLatestData(localized=False)
        self.assertEqual(latest[instance.getRegistersDBTag()]['timestamp'],now.replace(tzinfo=None))# latest value is dated now
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
        instance.updateValue(newValue=newValue1,timestamp=now,writeDB=True,force=False)
        instance2.updateValue(newValue=newValue2,timestamp=now,writeDB=True,force=False)
        
        table=instance.getRegistersDBTableName()
        vars='"timestamp","'+instance.getRegistersDBTag()+'"'+ ',"'+instance2.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp ASC'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        # initialization
        self.assertEqual(rows[0][1],MainDeviceVarDict['Value']) # initial value of instance
        self.assertEqual(rows[0][2],None) # instance2 not yet created
        self.assertEqual(rows[1][2],newDict['Value']) # initial value of instance2
        # instance updateValue
        self.assertEqual(rows[2][1],newValue1) # new value of instance
        self.assertEqual(rows[2][2],newDict['Value']) # initial value of instance2
        # instance2 updateValue
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
        instance.updateValue(newValue=newValue1,timestamp=now,writeDB=True,force=False)
        instance2.updateValue(newValue=newValue2,timestamp=now,writeDB=True,force=False)

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
    
    def testAssignSubsystem(self):
        print('## TESTING THE ASSIGNMENET OF A SUBSYSTEM ##')
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.store2DB()
        SUBSYSTEMs=MainAPP.models.Subsystems.objects.filter(mainvars=instance)
        self.assertQuerysetEqual(SUBSYSTEMs,[]) # no subsystem assigned
        subsystem=MainAPP.models.Subsystems(Name=0,content_object=instance)
        subsystem.save()
        SUBSYSTEMs=MainAPP.models.Subsystems.objects.filter(mainvars=instance)
        self.assertEqual(list(SUBSYSTEMs),[subsystem,]) # a subsystem returned
        self.DB.dropTable(table=instance.getRegistersDBTableName())
    
    def testAutomationVarsManagement(self):
        print('## TESTING THE MANAGEMENT OF THE AUTOMATION VARS ##')
        instance=MainDeviceVars(**MainDeviceVarDict)
        instance.store2DB() # this should create automation var
        AVARs=MainAPP.models.AutomationVariables.objects.filter(Device='MainVars').filter(Tag=instance.getRegistersDBTag())
        self.assertEqual(1,AVARs.count()) # one automationvar is returned
        # one update is generated to check that no additional AVARs are created
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        newValue1=21
        instance.updateLabel(newLabel='Test new label')
        AVARs=MainAPP.models.AutomationVariables.objects.filter(Device='MainVars').filter(Tag=instance.getRegistersDBTag())
        self.assertEqual(1,AVARs.count()) # only one automationvar is still returned
        
        self.DB.dropTable(table=instance.getRegistersDBTableName())
        