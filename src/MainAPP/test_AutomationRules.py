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
        instance=AutomationRules(**AutomationRulesDict)
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        self.assertEqual(instance.pk,None)
        instance.store2DB()
        # checks that store2DB creates the corresponding table in the registers DB
        self.assertEqual(instance.pk,1)
    
    