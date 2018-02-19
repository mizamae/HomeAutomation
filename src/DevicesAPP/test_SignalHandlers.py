from .test_utils import *

from MainAPP.signals import SignalToggleAVAR,SignalSetGPIO
print('#########################################')
print('# TESTING OF DevicesAPP SIGNAL HANDLERS #')
print('#########################################')

@tag('signalhandlers')
class MasterGPIOsModelTests(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
        self.DB.dropTable(table='inputs')
        self.DB.dropTable(table='outputs')
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
  
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
         
          
# INDIVIDUAL FUNCTIONS TESTING
    def test_SignalSetGPIO_handler(self):
        '''
        SignalSetGPIO: signal triggered when a MasterGPIO needs to be set from outside of DevicesAPP such as from AutomationAPP
        '''
        print('## TESTING THE OPERATION OF THE SignalSetGPIO METHOD ##')
        instance=MasterGPIOs(**MasterGPIODict)
        now=timezone.now().replace(microsecond=0).replace(tzinfo=None)
        instance.store2DB()
        self.assertEqual(instance.Value,GPIO_HIGH)
        SignalSetGPIO.send(sender=None,pk=instance.pk,Value=0)
        instance=MasterGPIOs.objects.get(pk=instance.pk)    # a refresh on the instance is required 
        self.assertEqual(instance.Value,GPIO_LOW)
        self.DB.dropTable(table=instance.getRegistersDBTable())
          
    def test_SignalToggleAVAR_handler(self):
        '''
        SignalToggleAVAR: signal triggered when a, automationvar needs to be toggled
        '''
        print('## TESTING THE OPERATION OF THE SignalToggleAVAR METHOD ##')
        print('    -> Tested with a MainDeviceVar')
        newDict=editDict(keys=['Value','Label','DataType'], newValues=[1,'Test MainVar 2',DTYPE_DIGITAL], Dictionary=MainDeviceVarDict)
        instance=MainDeviceVars(**newDict)
        instance.store2DB()
        now=timezone.now().replace(microsecond=0)
        from MainAPP.models import AutomationVariables
        AVAR=AutomationVariables.objects.get(Device='MainVars',Label=newDict['Label'])
        latest=AVAR.getLatestData(localized=True)
        DeleteLastRegisterFromDB(DB=self.DB,table=AVAR.Table)
        self.assertAlmostEqual(latest[AVAR.Tag]['timestamp'],now,datetime.timedelta(seconds=1))
        self.assertEqual(latest[AVAR.Tag]['value'],1)
        
        SignalToggleAVAR.send(sender=None,Device='MainVars',Tag=AVAR.Tag)
        
        latest=AVAR.getLatestData(localized=True)
        DeleteLastRegisterFromDB(DB=self.DB,table=AVAR.Table)
        self.assertEqual(latest[AVAR.Tag]['value'],0)
        
        print('    -> Tested with a MasterGPIO')
        instance=MasterGPIOs(**MasterGPIODict)
        instance.store2DB()
        now=timezone.now().replace(microsecond=0)
        from MainAPP.models import AutomationVariables
        AVAR=AutomationVariables.objects.get(Device='MainGPIOs',Label=MasterGPIODict['Label'])
        latest=AVAR.getLatestData(localized=True)
        DeleteLastRegisterFromDB(DB=self.DB,table=AVAR.Table)
        self.assertAlmostEqual(latest[AVAR.Tag]['timestamp'],now,datetime.timedelta(seconds=1))
        self.assertEqual(latest[AVAR.Tag]['value'],1)
        
        SignalToggleAVAR.send(sender=None,Device='MainGPIOs',Tag=AVAR.Tag)
        
        latest=AVAR.getLatestData(localized=True)
        DeleteLastRegisterFromDB(DB=self.DB,table=AVAR.Table)
        self.assertEqual(latest[AVAR.Tag]['value'],0)