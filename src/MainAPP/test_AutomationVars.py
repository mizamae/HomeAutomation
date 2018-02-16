from .test_utils import *


print('##################################################')
print('# TESTING OF AutomationVariables MODEL FUNCTIONS #')
print('##################################################')

@tag('automationvars')
class AutomationVariablesTests(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
        self.DB.dropTable(table='MainVariables')
        self.signal_was_called = False
        self.signaltimestamp=None
        self.signalTag=None
        self.signalValue=None
        
        newDict=editDict(keys=['Label','Tag','BitPos'], \
                         newValues=['Test Automation Var0 bit 0','1_1_1',0], Dictionary=AutomationVariablesDict)
        self.AVAR0_0=AutomationVariables(**newDict)
        self.AVAR0_0.store2DB()
        
        newDict=editDict(keys=['Label','Tag','BitPos'], \
                         newValues=['Test Automation Var0 bit 1','1_1_1',1], Dictionary=AutomationVariablesDict)
        self.AVAR0_1=AutomationVariables(**newDict)
        self.AVAR0_1.store2DB()
        
        MasterGPIOs(Pin=18,Label='Output IO',Direction=GPIO_OUTPUT,Value=GPIO_HIGH).save()
        self.outIO=MasterGPIOs.objects.get(Pin=18)
        
        def handler(sender, **kwargs):
            self.signal_was_called = True
            self.signaltimestamp=kwargs['timestamp']
            self.signalTag=kwargs['Tags'][0]
            self.signalValue=kwargs['Values'][0]
        
        self.handler=handler
 
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    

        
         
# INDIVIDUAL FUNCTIONS TESTING
    def test_store2DB(self):
        '''
        storeDB: method provided to perform the following steps:
            - Validate the input data
            - Saves the instance into the DB
        '''
        print('## TESTING THE OPERATION OF THE store2DB METHOD ##')
        instance=AutomationVariables(**AutomationVariablesDict)
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        self.assertEqual(instance.pk,None)
        instance.store2DB()
        # checks that store2DB creates the corresponding table in the registers DB
        self.assertEqual(instance.pk,3)
    
    def test_createSubsystem(self):
        '''
        createSubsystem: method provided to assign a subsystem to the var:
        '''
        print('## TESTING THE OPERATION OF THE createSubsystem METHOD ##')
        instance=AutomationVariables(**AutomationVariablesDict)
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        instance.store2DB()
        self.assertEqual(instance.checkSubsystem(Name=0),False)
        instance.createSubsystem(Name=0)
        self.assertEqual(instance.checkSubsystem(Name=0),True)
    
    def test_getLatestData(self):
        '''
        getLatestData: method provided to retrieve the latest DB data of the var:
        '''
        print('## TESTING THE OPERATION OF THE getLatestData METHOD ##')
        instance=AutomationVariables(**AutomationVariablesDict)
        now=timezone.now().replace(microsecond=0)
        instance.store2DB()
        newValue=25
        InsertRegister2DB(DB=self.DB,table=instance.Table,tags=['timestamp',instance.Tag],values=[now,newValue,])
        latest=instance.getLatestData(localized=True)
        DeleteLastRegisterFromDB(DB=self.DB,table=instance.Table)
        self.assertAlmostEqual(latest[instance.Tag]['timestamp'],now,datetime.timedelta(seconds=1))
        self.assertEqual(latest[instance.Tag]['value'],newValue)
    
    def test_getValues(self):
        '''
        getValues: method provided to retrieve the DB data of the var between given dates:
        '''
        print('## TESTING THE OPERATION OF THE getValues METHOD ##')
        instance=AutomationVariables(**AutomationVariablesDict)
        instance.store2DB()
        now=timezone.now().replace(microsecond=0)+datetime.timedelta(seconds=1)
        newValue=25
        for i in range(0,10):
            InsertRegister2DB(DB=self.DB,table=instance.Table,tags=['timestamp',instance.Tag],values=[now+i*datetime.timedelta(seconds=1),newValue+i,])
        fromDate=now
        toDate=fromDate+datetime.timedelta(seconds=11)
        rows=instance.getValues(fromDate=fromDate,toDate=toDate)
        self.assertEqual(len(rows),10)
        for i,row in enumerate(rows):
            self.assertEqual(row[0],now.replace(tzinfo=None)+i*datetime.timedelta(seconds=1))
            self.assertEqual(row[1],newValue+i)
            DeleteLastRegisterFromDB(DB=self.DB,table=instance.Table)
        DeleteLastRegisterFromDB(DB=self.DB,table=instance.Table)
    
    def test_executeAutomationRules(self):
        '''
        executeAutomationRules: method provided to execute the rules where self is included
        '''
        print('## TESTING THE OPERATION OF THE executeAutomationRules METHOD ##')
        
        Rule=AutomationRules(**AutomationRulesDict)
        Rule.store2DB()
        Rule.setActive(value=True)
        now=timezone.now().replace(microsecond=0)
        
        newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant','Constant'], \
                             newValues=[Rule,1,self.AVAR0_0,'>',self.AVAR0_1,True,0], Dictionary=RuleItemsDict)
        Item=RuleItems(**newDict)
        Item.store2DB()
        newValue=0
        InsertRegister2DB(DB=self.DB,table=self.AVAR0_0.Table,tags=['timestamp',self.AVAR0_0.Tag],values=[now,newValue,])
        self.AVAR0_0.executeAutomationRules()
        self.outIO=MasterGPIOs.objects.get(Pin=18)      # an update of the instance is required to refresh the value
        self.assertEqual(self.outIO.Value,GPIO_HIGH)
        DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR0_0.Table)
        
        newValue=1
        InsertRegister2DB(DB=self.DB,table=self.AVAR0_0.Table,tags=['timestamp',self.AVAR0_0.Tag],values=[now,newValue,])
        self.AVAR0_0.executeAutomationRules()
        self.outIO=MasterGPIOs.objects.get(Pin=18)      # an update of the instance is required to refresh the value
        self.assertEqual(self.outIO.Value,GPIO_LOW)
        DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR0_0.Table)
        
