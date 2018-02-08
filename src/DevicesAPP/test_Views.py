from .test_utils import *

print('####################################')
print('# TESTING OF Views MODEL FUNCTIONS #')
print('####################################') 

@tag('views')
class ViewsTests(TestCase):
    fixtures=['DevicesAPP.json',]
        
    def setUp(self):
        User = get_user_model()
        self.testuser=User.objects.create_user(name='testUser', email="testUser@test.com",password='12345')
        self.testSuperuser=User.objects.create_user(name='testSuperuser', email="testSuperuser@test.com",
                                                    password='12345',is_superuser=True)
 
        self.simpleClient=Client()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
            
        self.superClient=Client()
        logged_in = self.superClient.login(username='testSuperuser@test.com', password='12345')
            
        group_name = "Permissions"
        self.group = Group(name=group_name)
        self.group.save()
            
        self.remoteDVT=DeviceTypes.objects.get(pk=1)
        self.localDVT=DeviceTypes.objects.get(pk=2)
        self.memoryDVT=DeviceTypes.objects.get(pk=3)
        
    # CHECKING THE VIEWS
    def test_homepage(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/home'
        print('## TESTING THE ACCESS TO HOMEPAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 301) # permament redirect status
        self.assertTrue('Devices/home' in response.url) 
        print('    --> Test to reach as simple user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 301) # permament redirect status
        self.assertTrue('Devices/home' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="add_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 301) # found status
        
    def test_addDevices(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/add/devices/'
        print('## TESTING THE ACCESS TO Devices/add/devices PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="add_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
            
    def test_addDeviceTypes(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/add/devicetypes/'
        print('## TESTING THE ACCESS TO Devices/add/devicetypes PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="add_devicetypes")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
            
    def test_setcustomlabels(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/setcustomlabels/1/'
        print('## TESTING THE ACCESS TO setCustomLabels PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        
    def test_scanDevices(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/scan/devices/'
        print('## TESTING THE ACCESS TO Devices/scan PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url) 
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="scan_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        # POSTING WITHOUT A DEVICE
        response = self.simpleClient.post(url,**{'HTTP_USER_AGENT':TESTS_USER_AGENT})
        self.assertTrue(SCAN_DEVICENOFOUND in str(response.content))# NO DEVICE FOUND
        startApache()
        response = self.simpleClient.post(url,**{'HTTP_USER_AGENT':TESTS_USER_AGENT})# this needs to be modified to poll on a loopback IP instead of the real
        stopApache()
        self.assertTrue(SCAN_DEVICEFOUND in str(response.content))# DEVICE FOUND
            
    def test_viewAllDevices(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/view_all/devices/'
        print('## TESTING THE ACCESS TO Devices/view_all PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="view_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        
    def test_viewAllDevicetypes(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/view_all/devicetypes/'
        print('## TESTING THE ACCESS TO Devices/view_all PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="view_devicetypes")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
            
    def test_modifyDevices(self):
        print('## TESTING THE ACCESS TO Devices/modify/devices/ PAGE ##')
        print('    --> Test to reach as superuser')
        url='/'+APP_TEMPLATE_NAMESPACE+'/modify/devices/1/'
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="change_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        
    def test_modifyDevicetypes(self):
        print('## TESTING THE ACCESS TO Devices/modify/devicetypes/ PAGE ##')
        print('    --> Test to reach as superuser')
        url='/'+APP_TEMPLATE_NAMESPACE+'/modify/devicetypes/1/'
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="change_devicetypes")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
            
    def test_advancedDevicepage(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/advanceddevicepage/1/'
        print('## TESTING THE ACCESS TO Devices/advancedevicepage PAGE ##')
        print('    --> Test to reach as superuser')
        response = self.superClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        print('    --> Test to reach as unauthorized user')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 302) # redirection to login
        self.assertTrue('login' in response.url)
        print('    --> Test to reach as authorized user')
        permission=Permission.objects.get(codename="view_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
        response = self.simpleClient.get(url)
        self.assertEqual(response.status_code, 200) # found status
        
    def test_async_post(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/async_post/'
        print('--> Test to reach DevicesAPP async_post page')
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT,])
        instance=Devices(**newDict)
        instance.store2DB()
            
        file=join(ApacheHTTPpath, 'powers.xml')
        setupPowersXML(code=2,datagramId=0,status=8,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0')
        with open(file) as fp:
            text=''
            for line in fp:
                text+=line
            response=self.superClient.post(url, text,content_type="application/txt")
        resetPowersXML()
        latest=instance.getLatestData(localized=False)
        instance.deleteRegistersTables()
        self.assertEqual(response.status_code, 204) # found but nothing returned status
        self.assertEqual(latest['1']['1_1_1']['bit3'], 1)
            
    def test_addRemoteDeviceProcedure(self):
        url='/'+APP_TEMPLATE_NAMESPACE+'/add/devices/'
        print('## TESTING THE ADDITION OF A NEW REMOTE DEVICE ##')
        response = self.superClient.get(url)
        from .views import modelSplitter
        data=modelSplitter(model='devices')
        Header1='Adding a new ' +data['Header1']
        Model=data['Model']
        FormModel=data['FormModel']
        FormKwargs=data['FormKwargs']
        message=data['message']
        lastAction=data['lastAction']
            
        permission=Permission.objects.get(codename="add_devices")
        self.group.permissions.add(permission)
        self.testuser.groups.add(self.group)
        self.testuser.save()
        logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
            
        newDict=editDict(keys=['DVT',],newValues=[self.remoteDVT.pk,])
            
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance()
            
        for client in [self.superClient,self.simpleClient]:
            print('    --> Test as superuser' if client==self.superClient else '    --> Test as authorized user')
            form = DevicesForm(newDict, action=FormKwargs['action'])
            IO=newDict.pop('IO')    # you have to remove extra fields from the dictionary before passing it to the view
            response = client.post(form.helper.form_action,newDict)
            self.assertEqual(response.status_code, 200) # form submitted OK
            self.assertTrue(FORM_ISVALID_MSG in str(response.content)) # Device saved OK
            instance = Devices.objects.get(Name=newDict['Name'])# Device saved OK
            self.assertEqual(instance.DVT,self.remoteDVT)# Device saved OK
            self.assertTrue('setcustomlabels' in str(response.content))# link to page to set custom labels
            form = DevicesForm(instance=instance, action=data['lastAction'])
            response = client.get(form.helper.form_action,newDict)
            self.assertEqual(response.status_code, 200) # CustomLabelsForm page received OK
            self.assertTrue(instance.Name in str(response.content))# device name found in the page
            DV=Devices.objects.get(pk=instance.pk)
            DGs=Datagrams.objects.filter(DVT=instance.DVT)
            form=DatagramCustomLabelsForm(None,DV=DV,DGs=DGs)
            response = client.post(form.helper.form_action,form.initial)
            self.assertEqual(response.status_code, 200) # CustomLabelsForm submitted OK
            self.assertTrue(DV.Name in str(response.content)) 
            self.assertTrue(FORM_ISVALID_MSG in str(response.content)) 
            instance = Devices.objects.get(Name=newDict['Name'])# Device saved OK
            self.assertTrue(instance.CustomLabels!='')# Custom labels set OK
            instance.deleteRegistersTables()
            newDict=editDict(keys=['DVT','Name','Code','IP'],newValues=[self.remoteDVT.pk,'Test Device 3',3,'10.10.10.3'])
                
        def test_addDevicetype(self):
            global DevicetypeDict
            url='/'+APP_TEMPLATE_NAMESPACE+'/add/devicetypes/'
            print('## TESTING THE ADDITION OF A NEW DEVICE TYPE ##')
            response = self.superClient.get(url)
            from .views import modelSplitter
            data=modelSplitter(model='devicetypes')
            Header1='Adding a new ' +data['Header1']
            Model=data['Model']
            FormModel=data['FormModel']
            FormKwargs=data['FormKwargs']
            message=data['message']
            lastAction=data['lastAction']
                
            permission=Permission.objects.get(codename="add_devicetypes")
            self.group.permissions.add(permission)
            self.testuser.groups.add(self.group)
            self.testuser.save()
            logged_in = self.simpleClient.login(username='testUser@test.com', password='12345')
                
            newDict=DevicetypeDict
                
            from utils.BBDD import getRegistersDBInstance
            DB=getRegistersDBInstance()
                
            for client in [self.superClient,self.simpleClient]:
                print('    --> Test as superuser' if client==self.superClient else '    --> Test as authorized user')
                form = DevicetypeForm(newDict, action=FormKwargs['action'])
                response = client.post(form.helper.form_action,newDict)
                self.assertEqual(response.status_code, 200) # form submitted OK
                self.assertTrue(FORM_ISVALID_MSG in str(response.content)) # Devicetype saved OK
                instance = Devicetypes.objects.get(Code=newDict['Code'])# Devicetype saved OK
                self.assertEqual(instance.Description, newDict['Description']) # form submitted OK
                instance.delete()
 