from .test_utils import *


print('########################################')
print('# TESTING OF RuleItems MODEL FUNCTIONS #')
print('########################################')

@tag('ruleitems')
class RuleItemsTest(TestCase):
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
        
        newDict=editDict(keys=['Label','Tag','BitPos'], \
                         newValues=['Test Automation Var0 bit 0','1_1_1',0], Dictionary=AutomationVariablesDict)
        self.AVAR0_0=AutomationVariables(**newDict)
        self.AVAR0_0.store2DB()
        
        newDict=editDict(keys=['Label','Tag','BitPos'], \
                         newValues=['Test Automation Var0 bit 1','1_1_1',1], Dictionary=AutomationVariablesDict)
        self.AVAR0_1=AutomationVariables(**newDict)
        self.AVAR0_1.store2DB()
        
        MasterGPIOs(Pin=18,Label='Output IO',Direction=GPIO_OUTPUT).save()
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
        Rule=AutomationRules(**AutomationRulesDict)
        Rule.store2DB()
        newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant'], \
                         newValues=[Rule,1,self.AVAR1,'>',self.AVAR2,False], Dictionary=RuleItemsDict)
        instance=RuleItems(**newDict)
        instance.store2DB()
        # checks that store2DB creates the corresponding table in the registers DB
        self.assertEqual(instance.pk,1)
    
    def test_evaluate_analog(self):
        '''
        evaluate: method provided to evaluate the mathematical expression:
        '''
        print('## TESTING THE OPERATION OF THE evaluate METHOD WITH ANALOG VARIABLES ##')
        Rule=AutomationRules(**AutomationRulesDict)
        Rule.store2DB()
        print('--> Evaluation of analog operators')
        operators=RuleItems.OPERATOR_CHOICES
        for i,operator in enumerate(operators):
            operator=operator[0]
            print('  --> Evaluation operator ' + operator)
            newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant'], \
                             newValues=[Rule,i+1,self.AVAR1,operator,self.AVAR2,False], Dictionary=RuleItemsDict)
            instance=RuleItems(**newDict)
            instance.store2DB()
            now=timezone.now()
            
            print('    --> Evaluation with too old data on VAR1. Defaults to the Rule OnError field')
            result=instance.evaluate()
            self.assertTrue('Too old data' in result['ERROR'])
            self.assertEqual(int(result['TRUE']),int(Rule.OnError))
            self.assertEqual(int(result['FALSE']),int(not Rule.OnError))
            
            print('    --> Evaluation with too old data on VAR2. Defaults to the Rule OnError field')
            newValue1=25
            InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,],\
                              values=[now,newValue1,])
            result=instance.evaluate()
            self.assertTrue('Too old data' in result['ERROR'])
            self.assertEqual(int(result['TRUE']),int(Rule.OnError))
            self.assertEqual(int(result['FALSE']),int(not Rule.OnError))
            
            print('    --> Evaluation TRUE with good data and two vars.')
            if '>' in operator or '!=' in operator:
                newValue1=25
                newValue2=20
            elif '<' in operator:
                newValue1=20
                newValue2=25
            elif '==' in operator:
                newValue1=25
                newValue2=25
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                              values=[now,newValue1,newValue2])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and two vars.')
            if '>' in operator or '==' in operator:
                newValue1=20
                newValue2=25
            elif '<' in operator:
                newValue1=25
                newValue2=20
            elif '!=' in operator:
                newValue1=25
                newValue2=25
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                              values=[now,newValue1,newValue2])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            if '>' in operator or '<' in operator:
                print('    --> Evaluation UNDEFINED with good data and two vars.')
                newValue1=25
                newValue2=25
                InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                                  values=[now,newValue1,newValue2])
                result=instance.evaluate()
                self.assertEqual(result['ERROR'],'')
                self.assertEqual(result['TRUE'],False)
                self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation TRUE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '>' in operator or '!=' in operator:
                instance.Constant=0
            elif '<' in operator:
                instance.Constant=100
            elif '==' in operator:
                instance.Constant=newValue1
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '>' in operator or '==' in operator:
                instance.Constant=100
            elif '<' in operator:
                instance.Constant=0
            elif '!=' in operator:
                instance.Constant=newValue1
                
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            if '>' in operator or '<' in operator:
                print('    --> Evaluation UNDEFINED with good data and isConstant.')
                instance.IsConstant=True
                instance.Var2=None
                instance.Constant=newValue1
                instance.save()
                result=instance.evaluate()
                self.assertEqual(result['ERROR'],'')
                self.assertEqual(result['TRUE'],False)
                self.assertEqual(result['FALSE'],False)
                
                print('    --> Evaluation UNDEFINED at max hysteresis limit.')
                instance.IsConstant=True
                instance.Var2=None
                instance.Constant=newValue1+0.999*instance.Var2Hyst
                instance.save()
                result=instance.evaluate()
                self.assertEqual(result['ERROR'],'')
                self.assertEqual(result['TRUE'],False)
                self.assertEqual(result['FALSE'],False)
                
                print('    --> Evaluation UNDEFINED at min hysteresis limit.')
                instance.IsConstant=True
                instance.Var2=None
                instance.Constant=newValue1-0.999*instance.Var2Hyst
                instance.save()
                result=instance.evaluate()
                self.assertEqual(result['ERROR'],'')
                self.assertEqual(result['TRUE'],False)
                self.assertEqual(result['FALSE'],False)
                
                print('    --> Evaluation FALSE surpassed max hysteresis limit.')
                instance.IsConstant=True
                instance.Var2=None
                if '>' in operator:
                    instance.Constant=newValue1+1.0001*instance.Var2Hyst
                elif '<' in operator:
                    instance.Constant=newValue1-1.0001*instance.Var2Hyst
                instance.save()
                result=instance.evaluate()
                self.assertEqual(result['ERROR'],'')
                self.assertEqual(result['TRUE'],False)
                self.assertEqual(result['FALSE'],True)
                
                print('    --> Evaluation TRUE surpassed min hysteresis limit.')
                instance.IsConstant=True
                instance.Var2=None
                if '>' in operator:
                    instance.Constant=newValue1-1.0001*instance.Var2Hyst
                elif '<' in operator:
                    instance.Constant=newValue1+1.0001*instance.Var2Hyst
                instance.save()
                result=instance.evaluate()
                self.assertEqual(result['ERROR'],'')
                self.assertEqual(result['TRUE'],True)
                self.assertEqual(result['FALSE'],False)
            for i in range(0,5):
                DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR1.Table)
                
    def test_evaluate_boolean(self):
        '''
        evaluate: method provided to evaluate the mathematical expression:
        '''
        print('## TESTING THE OPERATION OF THE evaluate METHOD WITH ANALOG VARIABLES ##')
        Rule=AutomationRules(**AutomationRulesDict)
        Rule.store2DB()
        print('--> Evaluation of boolean operators')
        operators=RuleItems.BOOL_OPERATOR_CHOICES
        for i,operator in enumerate(operators):
            operator=operator[0]
            print('  --> Evaluation operator ' + operator)
            newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant'], \
                             newValues=[Rule,i+1,self.AVAR1,operator,self.AVAR2,False], Dictionary=RuleItemsDict)
            instance=RuleItems(**newDict)
            instance.store2DB()
            now=timezone.now()
            
            print('    --> Evaluation TRUE with good data and two vars.')
            if '&' in operator:
                newValue1=1
                newValue2=1
            elif '|' in operator:
                newValue1=0
                newValue2=1
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                              values=[now,newValue1,newValue2])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and two vars.')
            if '&' in operator:
                newValue1=1
                newValue2=0
            elif '|' in operator:
                newValue1=0
                newValue2=0
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR1.Tag,self.AVAR2.Tag],\
                              values=[now,newValue1,newValue2])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            print('    --> Evaluation TRUE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '&' in operator:
                instance.Constant=1
            elif '|' in operator:
                instance.Constant=1
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '&' in operator:
                instance.Constant=0
            elif '|' in operator:
                instance.Constant=0
                
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            for i in range(0,5):
                DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR1.Table)
    
    def test_evaluate_analog_with_digital(self):
        '''
        evaluate: method provided to evaluate the mathematical expression:
        '''
        print('## TESTING THE OPERATION OF THE evaluate METHOD WITH DIGITAL VARIABLES ##')
        Rule=AutomationRules(**AutomationRulesDict)
        Rule.store2DB()
        print('--> Evaluation of analog operators')
        operators=RuleItems.OPERATOR_CHOICES
        for i,operator in enumerate(operators):
            operator=operator[0]
            print('  --> Evaluation operator ' + operator)
            newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant'], \
                             newValues=[Rule,i+1,self.AVAR0_0,operator,self.AVAR0_1,False], Dictionary=RuleItemsDict)
            instance=RuleItems(**newDict)
            instance.store2DB()
            now=timezone.now()
            
            print('    --> Evaluation TRUE with good data and two vars.')
            if '>' in operator or '!=' in operator:
                newValue1=1
            elif '<' in operator:
                newValue1=2
            elif '==' in operator:
                newValue1=3
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR0_0.Table,tags=['timestamp',self.AVAR0_0.Tag,],\
                              values=[now,newValue1,])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and two vars.')
            if '>' in operator or '==' in operator:
                newValue1=2
            elif '<' in operator:
                newValue1=1
            elif '!=' in operator:
                newValue1=3
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR0_0.Table,tags=['timestamp',self.AVAR0_0.Tag],\
                              values=[now,newValue1])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            print('    --> Evaluation TRUE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '>' in operator or '!=' in operator:
                instance.Constant=-1
            elif '<' in operator:
                instance.Constant=100
            elif '==' in operator:
                instance.Constant=newValue1 & (1<<self.AVAR0_0.BitPos)
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '>' in operator or '==' in operator:
                instance.Constant=100
            elif '<' in operator:
                instance.Constant=-1
            elif '!=' in operator:
                instance.Constant=newValue1 & (1<<self.AVAR0_0.BitPos)
                
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            for i in range(0,5):
                DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR1.Table)
                
    def test_evaluate_boolean_with_digital(self):
        '''
        evaluate: method provided to evaluate the mathematical expression:
        '''
        print('## TESTING THE OPERATION OF THE evaluate METHOD WITH DIGITAL VARIABLES ##')
        Rule=AutomationRules(**AutomationRulesDict)
        Rule.store2DB()
        print('--> Evaluation of boolean operators')
        operators=RuleItems.BOOL_OPERATOR_CHOICES
        for i,operator in enumerate(operators):
            operator=operator[0]
            print('  --> Evaluation operator ' + operator)
            newDict=editDict(keys=['Rule','Order','Var1','Operator12','Var2','IsConstant'], \
                             newValues=[Rule,i+1,self.AVAR0_0,operator,self.AVAR0_1,False], Dictionary=RuleItemsDict)
            instance=RuleItems(**newDict)
            instance.store2DB()
            now=timezone.now()
            
            print('    --> Evaluation TRUE with good data and two vars.')
            if '&' in operator:
                newValue1=3
            elif '|' in operator:
                newValue1=1
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR0_0.Tag,],\
                              values=[now,newValue1,])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and two vars.')
            if '&' in operator:
                newValue1=1
            elif '|' in operator:
                newValue1=0
                
            InsertRegister2DB(DB=self.DB,table=self.AVAR1.Table,tags=['timestamp',self.AVAR0_0.Tag],\
                              values=[now,newValue1])
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            print('    --> Evaluation TRUE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '&' in operator:
                instance.Constant=1
            elif '|' in operator:
                instance.Constant=1
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],True)
            self.assertEqual(result['FALSE'],False)
            
            print('    --> Evaluation FALSE with good data and isConstant.')
            instance.IsConstant=True
            instance.Var2=None
            if '&' in operator:
                instance.Constant=0
            elif '|' in operator:
                instance.Constant=0
                
            instance.save()
            result=instance.evaluate()
            self.assertEqual(result['ERROR'],'')
            self.assertEqual(result['TRUE'],False)
            self.assertEqual(result['FALSE'],True)
            
            for i in range(0,5):
                DeleteLastRegisterFromDB(DB=self.DB,table=self.AVAR0_0.Table)
                