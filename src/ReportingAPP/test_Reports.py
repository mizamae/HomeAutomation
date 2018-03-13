from .test_utils import *


print('########################################')
print('# TESTING OF Reports MODEL FUNCTIONS #')
print('########################################')

@tag('reports')
class ReportsTest(TestCase):
    def setUp(self):
        from utils.BBDD import getRegistersDBInstance
        self.DB=getRegistersDBInstance()
    
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
        instance=Reports(**ReportsDict)
        instance.store2DB()
        # checks that store2DB creates the corresponding table in the registers DB
        self.assertEqual(instance.pk,1)
    
    def test_preview(self):
        instance=Reports(**ReportsDict)
        instance.store2DB()
        ReportData,fromDate,toDate=instance.getReportData()
