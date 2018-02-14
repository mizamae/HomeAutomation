from .test_utils import *


print('##################################################')
print('# TESTING OF AutomationVariables MODEL FUNCTIONS #')
print('##################################################')

@tag('automationrules')
class AutomationRulesTest(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
        self.DB.dropTable(table='MainVariables')
        self.signal_was_called = False
        self.signaltimestamp=None
        self.signalTag=None
        self.signalValue=None
        
        self.AVAR1=AutomationVariables(**AutomationVariablesDict)
        self.AVAR1.store2DB()
        newDict=editDict(keys=['Label','Tag'], \
                         newValues=['Test Automation Var2','3_1_1'], Dictionary=AutomationVariablesDict)
        self.AVAR2=AutomationVariables(**newDict)
        self.AVAR2.store2DB()
        
        MasterGPIOs(Pin=18,Label='Output IO',Direction=GPIO_OUTPUT,Value=GPIO_HIGH).save()
        self.outIO=MasterGPIOs.objects.get(Pin=18)
        
        def handler(sender, **kwargs):
            self.signal_was_called = True
            self.signalPK=kwargs['pk']
            self.signalValue=kwargs['Value']
        
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
        instance=AutomationRules(**AutomationRulesDict)
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        self.assertEqual(instance.pk,None)
        instance.store2DB()
        # checks that store2DB creates the corresponding table in the registers DB
        self.assertEqual(instance.pk,1)
    
    def test_setActive(self):
        '''
        setActive: method provided to activate the rule
        '''
        print('## TESTING THE OPERATION OF THE setActive METHOD ##')
        instance=AutomationRules(**AutomationRulesDict)
        instance.store2DB()
        self.assertEqual(instance.Active,False)
        instance.setActive(value=True)
        self.assertEqual(instance.Active,True)  
            
    def test_printEvaluation(self):
        '''
        printEvaluation: method provided to get the information of the current evaluation
        '''
        print('## TESTING THE OPERATION OF THE printEvaluation METHOD ##')
        instance=AutomationRules(**AutomationRulesDict)
        instance.store2DB()
        result=instance.printEvaluation()
        print('    --> Tested on an inactive rule')
        self.assertEqual(result['TRUE'],'')
        self.assertEqual(result['FALSE'],'')
        self.assertTrue('Inactive Rule' in result['ERROR'])
        print('    --> Tested on an active rule without items')
        instance.setActive(value=True)
        result=instance.printEvaluation()
        self.assertEqual(result['TRUE'],'')
        self.assertEqual(result['FALSE'],'')
        self.assertTrue('The rule has no items associated' in result['ERROR'])
        print('    --> Tested on an active rule with items')
        now=timezone.now()
        newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant'], \
                             newValues=[instance,1,self.AVAR1,'==',self.AVAR2,False], Dictionary=RuleItemsDict)
        item=RuleItems(**newDict)
        item.store2DB()
        newValue1=25
        newValue2=25
        InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                      values=[now,newValue1,newValue2])
        result=instance.printEvaluation()
        DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR1.Table)
        self.assertEqual(result['TRUE'],'True')
        self.assertEqual(result['FALSE'],'False')
        newValue1=25
        newValue2=24
        InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                      values=[now,newValue1,newValue2])
        result=instance.printEvaluation()
        DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR1.Table)
        self.assertEqual(result['TRUE'],'False')
        self.assertEqual(result['FALSE'],'True')
        
    def test_execute(self):
        '''
        execute: method provided to execute the rule
        '''
        print('## TESTING THE OPERATION OF THE execute METHOD ##')
        now=timezone.now()
        instance=AutomationRules(**AutomationRulesDict)
        instance.store2DB()
        instance.setActive(value=True)
        newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant'], \
                             newValues=[instance,1,self.AVAR1,'==',self.AVAR2,False], Dictionary=RuleItemsDict)
        item=RuleItems(**newDict)
        item.store2DB()
        newValue1=25
        newValue2=25
        InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                      values=[now,newValue1,newValue2])
        SignalSetGPIO.connect(self.handler)
        self.assertEqual(self.outIO.Value,GPIO_HIGH)
        self.assertEqual(instance.LastEval,False)
        instance.execute()
        DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR1.Table)
        
        self.assertEqual(instance.LastEval,True)
        print('    --> Tested the signal emmission for GPIO change to True')
        # checks values from the signal
        self.assertEqual(self.signalPK,self.outIO.pk)   # signal
        self.assertEqual(self.signalValue,GPIO_LOW)
        print('    --> Tested the effective change of the GPIO to True')
        # checks the update of the GPIO
        self.outIO=MasterGPIOs.objects.get(Pin=18)      # an update of the instance is required to refresh the value
        self.assertEqual(self.outIO.Value,GPIO_LOW)
        
        newValue1=25
        newValue2=24
        InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                      values=[now,newValue1,newValue2])
        instance.execute()
        print('    --> Tested the signal emmission for GPIO change to False')
        # checks values from the signal
        self.assertEqual(self.signalPK,self.outIO.pk)   # signal
        self.assertEqual(self.signalValue,GPIO_HIGH)
        print('    --> Tested the effective change of the GPIO to False')
        # checks the update of the GPIO
        self.outIO=MasterGPIOs.objects.get(Pin=18)      # an update of the instance is required to refresh the value
        self.assertEqual(self.outIO.Value,GPIO_HIGH)
        
        SignalSetGPIO.disconnect(self.handler)