from .test_utils import *
import numpy as np

print('##################################################')
print('# TESTING OF AdditionalCalculations MODEL FUNCTIONS #')
print('##################################################')

@tag('additionalcalculations')
class AdditionalCalculationsTests(TestCase):
    numData=50 # number of samples to perform the calculations
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
        #self.DB.dropTable(table='MainVariables')
        self.signal_was_called = False
        self.signaltimestamp=None
        self.signalTag=None
        self.signalValue=None
        
        newDict=editDict(keys=['Label','Tag'], \
                         newValues=['Test Automation Var0','1_1_1'], Dictionary=AutomationVariablesDict)
        self.AVAR0=AutomationVariables(**newDict)
        self.AVAR0.store2DB()
        
        newDict=editDict(keys=['Label','Tag'], \
                         newValues=['Test Automation Var1','2_1_1'], Dictionary=AutomationVariablesDict)
        self.AVAR1=AutomationVariables(**newDict)
        self.AVAR1.store2DB()
        
        self.deleteRegisters()
            
        def handler(sender, **kwargs):
            self.signal_was_called = True
            self.signaltimestamp=kwargs['timestamp']
            self.signalTag=kwargs['Tags'][0]
            self.signalValue=kwargs['Values'][0]
        
        self.handler=handler
    
    def deleteRegisters(self):
        for i in range(0,self.numData):
            DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR0.Table)
    
    def insertDutyRegisters(self,duty=0):
        now=timezone.now().replace(microsecond=0)
        timespace=datetime.timedelta(seconds=24*60*60/self.numData)
        for i in range(0,self.numData):
            if i>=duty*self.numData:
                value=0
            else:
                value=1
            InsertRegister2DB(DB=self.DB,table=self.AVAR0.Table,tags=['timestamp',self.AVAR0.Tag],
                              values=[now-i*timespace,value,])
    
    def insertMeanRegisters(self,mean):
        now=timezone.now().replace(microsecond=0)
        timespace=datetime.timedelta(seconds=24*60*60/self.numData)
        s = np.random.normal(loc=mean,scale=1.0,size=self.numData)
        for i,x in enumerate(np.nditer(s)):
            InsertRegister2DB(DB=self.DB,table=self.AVAR0.Table,tags=['timestamp',self.AVAR0.Tag],
                              values=[now-i*timespace,float(x),])
            
        
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
        newDict=editDict(keys=['SourceVar',], \
                         newValues=[self.AVAR0,], Dictionary=AdditionalCalculationsDict)
        instance=AdditionalCalculations(**newDict)
        self.assertEqual(instance.pk,None)
        # the sinkvar automationvar does not yet exist so raises error
        label= str(instance)
        self.assertRaises(AutomationVariables.DoesNotExist,AutomationVariables.objects.get,Label=label)
        instance.store2DB()
        self.assertEqual(instance.pk,1)
        # now the sink var has been created and assigned to the sinkvar field
        sinkVAR=AutomationVariables.objects.get(Label=label)
        self.assertEqual(instance.SinkVar,sinkVAR)
        
    def test_DutyCycleOFF(self):
        print('## TESTING THE OPERATION OF THE dutycycleOFF CALCULATION ##')
        self.numData=50 # number of samples to perform the calculations
        newDict=editDict(keys=['SourceVar',], \
                         newValues=[self.AVAR0,], Dictionary=AdditionalCalculationsDict)
        instance=AdditionalCalculations(**newDict)
        instance.store2DB()
        print('    -> checked with no data in the DB')
        result=instance.calculate()
        self.assertEqual(result,None)
        
        print('    -> checked with all 1s')
        self.insertDutyRegisters(duty=1)
        result=instance.calculate()
        print('    Calculated duty: ' + str(result))
        self.assertEqual(result,0.00)
        self.deleteRegisters()
        
        print('    -> checked with all 0s')
        self.insertDutyRegisters(duty=0)
        result=instance.calculate()
        print('    Calculated duty: ' + str(result))
        self.assertEqual(result,100.00)
        self.deleteRegisters()
        
        print('    -> checked with half 0s half 1s')
        self.insertDutyRegisters(duty=0.5)
        result=instance.calculate()
        print('    Calculated duty: ' + str(result))
        self.assertAlmostEqual(result,50.00,delta=0.1)
        self.deleteRegisters()
        
        print('    -> checked with 10% 1s')
        self.insertDutyRegisters(duty=0.1)
        result=instance.calculate()
        print('    Calculated duty: ' + str(result))
        self.assertAlmostEqual(result,90.00,delta=0.1)
        self.deleteRegisters()
        
    def test_Mean(self):
        print('## TESTING THE OPERATION OF THE Mean CALCULATION ##')
        self.numData=100 # number of samples to perform the calculations
        newDict=editDict(keys=['SourceVar','Calculation'], \
                         newValues=[self.AVAR0,2], Dictionary=AdditionalCalculationsDict)
        instance=AdditionalCalculations(**newDict)
        instance.store2DB()
        print('    -> checked with no data in the DB')
        result=instance.calculate()
        self.assertEqual(result,None)
        
        print('    -> checked with mean=1')
        self.insertMeanRegisters(mean=1)
        result=instance.calculate()
        print('    Calculated mean: ' + str(result))
        self.assertAlmostEqual(result,1,delta=0.1)
        self.deleteRegisters()
        
        print('    -> checked with mean=100')
        self.insertMeanRegisters(mean=100)
        result=instance.calculate()
        print('    Calculated mean: ' + str(result))
        self.assertAlmostEqual(result,100,delta=0.5)
        self.deleteRegisters()
        
    def test_Max(self):
        print('## TESTING THE OPERATION OF THE Max CALCULATION ##')
        self.numData=10 # number of samples to perform the calculations
        newDict=editDict(keys=['SourceVar','Calculation'], \
                         newValues=[self.AVAR0,3], Dictionary=AdditionalCalculationsDict)
        instance=AdditionalCalculations(**newDict)
        instance.store2DB()
        print('    -> checked with no data in the DB')
        result=instance.calculate()
        self.assertEqual(result,None)
        
        print('    -> checked with max=1')
        self.insertDutyRegisters(duty=0.2)
        result=instance.calculate()
        print('    Calculated max: ' + str(result))
        self.assertAlmostEqual(result,1)
        self.deleteRegisters()
        
    def test_cumsum(self):
        print('## TESTING THE OPERATION OF THE cumsum CALCULATION ##')
        self.numData=10 # number of samples to perform the calculations
        newDict=editDict(keys=['SourceVar','Calculation'], \
                         newValues=[self.AVAR0,5], Dictionary=AdditionalCalculationsDict)
        instance=AdditionalCalculations(**newDict)
        instance.store2DB()
        print('    -> checked with no data in the DB')
        result=instance.calculate()
        self.assertEqual(result,None)
        
        print('    -> checked with all 1s')
        self.insertDutyRegisters(duty=1)
        result=instance.calculate()
        for i in range(self.numData+1,0):
            latest=getLastRow(name=self.AVAR0.Tag,table=self.AVAR0.Table)
            self.assertEqual(latest[self.AVAR0.Tag]['value'],i)
            DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR0.Table)
    
    def test_timeintegral(self):
        print('## TESTING THE OPERATION OF THE integral over time CALCULATION ##')
        self.numData=10 # number of samples to perform the calculations
        newDict=editDict(keys=['SourceVar','Calculation'], \
                         newValues=[self.AVAR0,6], Dictionary=AdditionalCalculationsDict)
        instance=AdditionalCalculations(**newDict)
        instance.store2DB()
        print('    -> checked with no data in the DB')
        result=instance.calculate()
        self.assertEqual(result,None)
        
        print('    -> checked with all 1s')
        self.insertDutyRegisters(duty=1)
        result=instance.calculate()
        print('    Calculated integral: ' + str(result))
        self.assertEqual(result,24*3600-60)
        self.deleteRegisters()
        
        print('    -> checked with all 0s')
        self.insertDutyRegisters(duty=0)
        result=instance.calculate()
        print('    Calculated integral: ' + str(result))
        self.assertEqual(result,0)
        self.deleteRegisters()
        