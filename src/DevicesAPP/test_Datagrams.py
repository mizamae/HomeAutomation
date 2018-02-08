from .test_utils import *
print('############################################')
print('# TESTING OF DatagramItems MODEL FUNCTIONS #')
print('############################################')

@tag('datagrams')
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
@tag('datagrams')
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
            self.assertEqual(type,DTYPE_FLOAT)
            
        DG=Datagrams.objects.get(Identifier='powers')
        types=DG.getDBTypes()
        self.assertEqual(types[0],'datetime')
        self.assertEqual(types[1],DTYPE_DIGITAL)
        for type in types[2:]:
            self.assertEqual(type,DTYPE_FLOAT)
        
    def test_getInfoFromItemName(self):        
        print('## TESTING THE OPERATION OF THE getInfoFromItemName METHOD ##')
        with self.assertRaises(DevicesAppException):
            Datagrams.getInfoFromItemName('22_2_1')
            Datagrams.getInfoFromItemName('22_2_1_56')
        info=Datagrams.getInfoFromItemName('1_1_1')
        ITM=DatagramItems.objects.get(pk=1)
        self.assertEqual(info['type'],ITM.DataType)
            
 