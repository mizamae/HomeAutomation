from .test_utils import *


print('############################################################')
print('# TESTING OF MainDeviceVarsWeeklySchedules MODEL FUNCTIONS #')
print('############################################################')

@tag('maindevicevarsweeklyschedules')
class MainDeviceVarsWeeklySchedulesTests(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
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
        self.VAR1=MainDeviceVars(**MainDeviceVarDict)
        self.VAR1.save()
        newDict=editDict(keys=['Value','Label'], newValues=[15,'Test MainVar 2'], Dictionary=MainDeviceVarDict)
        self.VAR2=MainDeviceVars(**newDict)
        self.VAR2.save()
        self.hours=[0 for x in range(0,24)]
        pass
 
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    
    def setHours(self,instance,ones=False):
        if ones:
            self.hours=[1 for x in range(0,24)]
        for i in range(0,7):
            day=inlineDaily(Day=i,Weekly=instance)
            self.hours[i]=1
            day.setInlineHours(self.hours)
            day.save()
            self.hours[i]=0
         
# INDIVIDUAL FUNCTIONS TESTING
    def test_store2DB(self):
        '''
        storeDB: method provided to perform the foloowing steps:
            - Validate the input data for the GPIO
            - Saves the instance into the DB
            - If is Active, checks the schedule and assigns the value to the variable
        '''
        print('## TESTING THE OPERATION OF THE store2DB METHOD ##')
        print('    --> Checked with Active=False')
        newDict=editDict(keys=['Var',], newValues=[self.VAR1,], Dictionary=VARWeeklyScheduleDict)
        instance=MainDeviceVarWeeklySchedules(**newDict)
        instance.store2DB()
        self.assertEqual(instance.pk,1)
        instance.delete()
        
        print('    --> Checked with Active=True')
        newDict1=editDict(keys=['Var',], newValues=[self.VAR1,], Dictionary=VARWeeklyScheduleDict)
        newDict1['Active']=True
        instance1=MainDeviceVarWeeklySchedules(**newDict1)
        instance1.store2DB()
        self.assertEqual(instance1.pk,2)
        self.DB.dropTable(table=instance1.Var.getRegistersDBTable())
        
    def test_setActive(self):
        '''
        setActive: method that modifies the status of the schedule. It activates or deactivates it.
            - If activated, ensures that the rest of the schedules affecting it variable are deactivated.
            - Additionally, it checks the schedule and assigns current value to the variable
        '''
        print('## TESTING THE OPERATION OF THE setActive METHOD ##')
        newDict1=editDict(keys=['Var',], newValues=[self.VAR1,], Dictionary=VARWeeklyScheduleDict)
        newDict1['Active']=True
        instance1=MainDeviceVarWeeklySchedules(**newDict1)
        instance1.store2DB()
        
        newDict2=editDict(keys=['Var','Label'], newValues=[self.VAR1,'Schedule 2'], Dictionary=VARWeeklyScheduleDict)
        instance2=MainDeviceVarWeeklySchedules(**newDict2)
        instance2.store2DB()
        
        self.assertEqual(instance2.Active,False)
        instance2.setActive(value=True)
        self.assertEqual(instance2.Active,True)
        instance1=MainDeviceVarWeeklySchedules.objects.get(Label=newDict1['Label']) # a refreshing of the instance is needed to get the changes
        self.assertEqual(instance1.Active,False)
        instance1.setActive(value=True)
        self.assertEqual(instance1.Active,True)
        instance2=MainDeviceVarWeeklySchedules.objects.get(Label=newDict2['Label']) # a refreshing of the instance is needed to get the changes
        self.assertEqual(instance2.Active,False)
        
        self.DB.dropTable(table=instance1.Var.getRegistersDBTable())
        
    def test_getTodaysPattern(self):
        '''
        getTodaysPattern: method that retrieves the schedule pattern of today
        '''
        print('## TESTING THE OPERATION OF THE getTodaysPattern METHOD ##')
        newDict1=editDict(keys=['Var',], newValues=[self.VAR1,], Dictionary=VARWeeklyScheduleDict)
        newDict1['Active']=True
        instance1=MainDeviceVarWeeklySchedules(**newDict1)
        instance1.store2DB()
        self.setHours(instance1)
        pattern=instance1.getTodaysPattern()
        import datetime 
        timestamp=datetime.datetime.now() 
        weekDay=timestamp.weekday() 
        hour=timestamp.hour
        self.hours[weekDay]=1
        self.assertEqual(pattern,self.hours)
        
        self.DB.dropTable(table=instance1.Var.getRegistersDBTable())
        
    def test_modify(self):
        '''
        modify: method that allows to modify the HValue and LValue an schedule 
        '''
        print('## TESTING THE OPERATION OF THE modify METHOD ##')
        newDict1=editDict(keys=['Var',], newValues=[self.VAR1,], Dictionary=VARWeeklyScheduleDict)
        instance1=MainDeviceVarWeeklySchedules(**newDict1)
        instance1.save()
        self.setHours(instance1)
        instance1.setActive(value=True)
        self.assertEqual(instance1.LValue,newDict1['LValue'])
        self.assertEqual(instance1.HValue,newDict1['HValue'])
        instance1.modify(value='LValue',sense='+')
        self.assertEqual(instance1.LValue,newDict1['LValue']+0.5)
        self.assertEqual(instance1.Var.Value,newDict1['LValue']+0.5) # checks that the variable value is changed
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        table=instance1.Var.getRegistersDBTable()
        vars='"timestamp","'+instance1.Var.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 2'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        self.assertEqual(rows[1][1],newDict1['LValue'])# previous to latest value equals the previous Value
        self.assertEqual(rows[0][1],newDict1['LValue']+0.5) # latest value equals the newValue
        self.assertEqual(rows[0][0]-rows[1][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
        self.assertAlmostEqual(rows[0][0],now+datetime.timedelta(seconds=3),delta=datetime.timedelta(seconds=1))# checks that the latest value is dated now+3sec due to the anti-collision strategy on registers DB
        
        instance1.modify(value='LValue',sense='-')
        self.assertEqual(instance1.LValue,newDict1['LValue'])
        self.assertEqual(instance1.Var.Value,newDict1['LValue']) # checks that the variable value is changed
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        table=instance1.Var.getRegistersDBTable()
        vars='"timestamp","'+instance1.Var.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 2'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        self.assertEqual(rows[1][1],newDict1['LValue']+0.5)# previous to latest value equals the previous Value
        self.assertEqual(rows[0][1],newDict1['LValue']) # latest value equals the newValue
        self.assertEqual(rows[0][0]-rows[1][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
        self.assertAlmostEqual(rows[0][0],now+datetime.timedelta(seconds=3),delta=datetime.timedelta(seconds=1))# checks that the latest value is dated now+3sec due to the anti-collision strategy on registers DB
        
        instance1.modify(value='HValue',sense='+')
        self.assertEqual(instance1.HValue,newDict1['HValue']+0.5)
        instance1.modify(value='HValue',sense='-')
        self.assertEqual(instance1.HValue,newDict1['HValue'])
        instance1.modify(value='REFValue')
        
        self.assertEqual(instance1.Var.Value,newDict1['HValue'])
        
        self.DB.dropTable(table=instance1.Var.getRegistersDBTable())
        
    def test_checkAll(self):
        '''
        checkAll: method that checks all the active schedules and updates the VAR value in case needed. 
        '''
        newDict1=editDict(keys=['Var',], newValues=[self.VAR1,], Dictionary=VARWeeklyScheduleDict)
        newDict1['Active']=True
        instance1=MainDeviceVarWeeklySchedules(**newDict1)
        instance1.save()
        self.setHours(instance1)
        
        newDict2=editDict(keys=['Var','Label'], newValues=[self.VAR2,'Label 2'], Dictionary=VARWeeklyScheduleDict)
        newDict2['Active']=True
        instance2=MainDeviceVarWeeklySchedules(**newDict2)
        instance2.save()
        self.setHours(instance2,ones=True)
        
        instance1.checkAll(init=True)
        
        table=instance1.Var.getRegistersDBTable()
        vars='"timestamp","'+instance1.Var.getRegistersDBTag()+'","'+instance2.Var.getRegistersDBTag()+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 2'
        rows=self.DB.executeTransaction(SQLstatement=sql)
        self.assertEqual(rows[0][1],newDict1['LValue'])# on instance 1 all is LValue
        self.assertEqual(rows[0][2],newDict2['HValue'])# on instance 2 all is HValue
        self.assertEqual(rows[0][0]-rows[1][0],datetime.timedelta(seconds=1))# checks that it inserts two rows with 1 second difference
        
        self.DB.dropTable(table=instance1.Var.getRegistersDBTable())