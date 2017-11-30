# coding: utf-8
import sys
import unittest


class XMLParser(object):
    def __init__(self,xmlroot):
        self._xmlroot=xmlroot
       
    def parseConfFile(self):
        """
        Generates the list of devices with the corresponding dataframe structure
        :callback           xmlroot = ET.parse(XMLconfFile).getroot()
                            deviceList=parseConfFile(xmlroot)
        """
#        try:
        deviceList=[]
        datagramList=[]
        maxLenData=0
        read_DEVICE_TYPES=[]
        read_DEVICE_DCODES=[]
        for device in self._xmlroot.findall('DEVICE_DATA'):
            DEVICE_TYPE=device.find('DEVICE_TYPE').text
            if DEVICE_TYPE==None:                           # checks if DEVICE_TYPE tag exists
                raise XMLException('The tag <DEVICE_TYPE>DeviceType</DEVICE_TYPE> has not been found.')
            else:
                if DEVICE_TYPE in read_DEVICE_TYPES:        # checks if duplicated DEVICE_TYPE tags exist
                    raise XMLException('The DEVICE_TYPE '+DEVICE_TYPE+' is repeated.' )
                read_DEVICE_TYPES.append(DEVICE_TYPE)
                
            data=[]
            DEVICE_DCODE=device.get('dcode')
            if DEVICE_DCODE==None:                           # checks if DEVICE_DCODE attribute exists
                raise XMLException('The attribute <DEVICE_DATA dcode > has not been found for the device ' +DEVICE_TYPE)
            else:
                if DEVICE_DCODE in read_DEVICE_DCODES:      # checks if duplicated DEVICE_DCODE attributes exist
                    raise XMLException('The DEVICE_DCODE '+DEVICE_DCODE+' is repeated.' )
                read_DEVICE_DCODES.append(DEVICE_DCODE)
                
            deviceList.append((DEVICE_TYPE,DEVICE_DCODE))
            
            read_DEVICE_DATAGRAM_REQUESTS=[]
            read_DEVICE_DATAGRAM_DCODES=[]
            
            for datagram in device.findall('DATAGRAM'):
                numData=0
                thisdatagram=[]
                REQUEST=datagram.get('request')
                if REQUEST==None:                           # checks if REQUEST attribute exists
                    raise XMLException('The attribute <DATAGRAM request > has not been found.')
                else:
                    if REQUEST in read_DEVICE_DATAGRAM_REQUESTS:        # checks if duplicated REQUEST tags exist for a device
                        raise XMLException('The attribute request '+REQUEST+' is repeated for the device type '+ DEVICE_TYPE)
                read_DEVICE_DATAGRAM_REQUESTS.append(REQUEST)
                thisdatagram.append(REQUEST)
                DATAGRAM_DCODE=datagram.get('dcode')
                if DATAGRAM_DCODE==None:                           # checks if DATAGRAM_DCODE attribute exists
                    raise XMLException('The attribute <DATAGRAM dcode > has not been found.')
                else:
                    if DATAGRAM_DCODE in read_DEVICE_DATAGRAM_DCODES:        # checks if duplicated DATAGRAM_DCODE tags exist for a device
                        raise XMLException('The attribute <DATAGRAM dcode= '+DATAGRAM_DCODE+'> is repeated for the device type '+ DEVICE_TYPE)
                    try:
                        int(DATAGRAM_DCODE)
                    except ValueError:
                        raise XMLException('The attribute <DATAGRAM dcode > needs to be a string castable to an int in datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                    if not int(DATAGRAM_DCODE) in range(0,255):
                        raise XMLException('The attribute <DATAGRAM dcode > needs to be in the range between 0-255. This fails in the datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                read_DEVICE_DATAGRAM_DCODES.append(DATAGRAM_DCODE)
                thisdatagram.append(DATAGRAM_DCODE)
                DATAGRAM_SAMPLE=datagram.get('sample')
                if DATAGRAM_SAMPLE==None:                           # checks if DATAGRAM_SAMPLE attribute exists
                    raise XMLException('The attribute <DATAGRAM sample > has not been found. This fails in the datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                else:
                    try:
                        int(DATAGRAM_SAMPLE)
                    except ValueError:
                        raise XMLException('The attribute <DATAGRAM sample > needs to be a string castable to an int. This fails in the datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                thisdatagram.append(DATAGRAM_SAMPLE)
                for dato in datagram.findall('DATA'):
                    DATO_LABEL=dato.get('label')
                    if DATO_LABEL==None:                           # checks if DATO_LABEL attribute exists
                        raise XMLException('The attribute <DATA label > is needed. This fails in the datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                    DATO_UNITS=dato.get('units')
                    if DATO_UNITS==None:                           # checks if DATO_UNITS attribute exists
                        raise XMLException('The attribute <DATA units > is needed. This fails in the datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                    DATO_TYPE=dato.get('type')
                    if DATO_TYPE==None:                           # checks if DATO_TYPE attribute exists
                        raise XMLException('The attribute <DATA type > is needed. This fails in the datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                    else:
                        if not DATO_TYPE in ('integer','float'):
                            raise XMLException('The attribute <DATA type > needs to be integer or float. This fails in the datagram '+REQUEST+' of the device type '+DEVICE_TYPE)
                    if DATO_UNITS=='bits':
                        bitText=[]
                        for bit in dato.findall('BIT'):
                            #bitPos=bit.get('pos')
                            bitText.append(bit.get('label'))
                        thisdatagram.append((DATO_LABEL+'_'+DATO_UNITS+'_'+'$'.join(bitText),DATO_TYPE))
                    else:
                        thisdatagram.append((DATO_LABEL+'_'+DATO_UNITS,DATO_TYPE))
                    #    numData+=8
                    #else:             
                    numData+=1
                data.append(thisdatagram)
                if numData>maxLenData:
                    maxLenData=numData
            datagramList.append(data)   
            ##print(deviceList)
        return (deviceList,datagramList,maxLenData)   
    
    def getMasterGPIOConfFile(self):
        MasterGPIOs=self._xmlroot.find('MASTER_IO').findall('GPIO')
        GPIOs_data=[]
        for GPIO in MasterGPIOs:
            GPIO_data={}
            GPIO_data['number']=GPIO.get('number')
            GPIO_data['label']=GPIO.get('label')
            GPIO_data['direction']=GPIO.get('direction')
            if GPIO_data['direction']!='OUT' and GPIO_data['direction']!='IN' and GPIO_data['direction']!='SENS':
                raise XMLException('The attribute <GPIO direction > needs to be "OUT" for outputs or "IN" for inputs or "SENS" for sensors. This fails in the GPIO '+GPIO_data['number'])
            if GPIO_data['direction']!='SENS':
                GPIO_data['default']=GPIO.get('default')
            else:
                GPIO_data['default']=0
            GPIOs_data.append(GPIO_data)
        return GPIOs_data
    
    def getOrdersConfFile(self,deviceType):
        commands=[]
        for device in self._xmlroot.findall('DEVICE_DATA'):
            DEVICE_TYPE=device.find('DEVICE_TYPE').text
            if DEVICE_TYPE==deviceType:                           # checks if DEVICE_TYPE == desired deviceType
                orders=device.find('ORDERS')
                orders_dict={}
                orders_dict['deviceType']=DEVICE_TYPE
                if orders is not None:
                    for order in orders.findall('CMD'):
                        ORDER_CMD=order.get('order')
                        ORDER_LABEL=order.get('label')
                        ORDER_PIN=order.get('pin')
                        if ORDER_PIN is None or ORDER_PIN=='':
                            ORDER_PIN=''
                            ORDER_VALUE=''
                        else:
                            ORDER_VALUE=order.get('value')
                            if ORDER_VALUE is None or ORDER_VALUE=='':
                                raise XMLException('The attribute <CMD value> needs to be defined if attribute <CMD pin> is defined.')
                        commands.append({'cmd':ORDER_CMD,'label':ORDER_LABEL,'pin':ORDER_PIN,'value':ORDER_VALUE})
                
        return commands
    
    def getDeviceTypesConfFile(self):
        deviceTypes=[]
        for device in self._xmlroot.findall('DEVICE_DATA'):
            DEVICE_TYPE=device.find('DEVICE_TYPE').text
            deviceTypes.append(DEVICE_TYPE)
                
        return deviceTypes
    
    def getDatagramsStructureForDeviceType(self,deviceType):
        datagramList=[]
        for device in self._xmlroot.findall('DEVICE_DATA'):
            DEVICE_TYPE=device.find('DEVICE_TYPE').text
            if DEVICE_TYPE==deviceType:                           # checks if DEVICE_TYPE == desired deviceType
                datagrams=device.findall('DATAGRAM')
                for datagram in datagrams:
                    names=[]
                    types=[]
                    datagramID=datagram.get('request')
                    sampleTime=datagram.get('sample')
                    variables=datagram.findall('DATA')
                    for variable in variables:
                        LABEL=variable.get('label')
                        TYPE=variable.get('type')
                        UNITS=variable.get('units')
                        if UNITS=='bits':
                            bits=variable.findall('BIT')
                            bitText=[]
                            for bit in bits:
                                bitText.append(bit.get('label'))
                            names.append(LABEL+'_'+UNITS+'_'+'$'.join(bitText))
                        else:
                            names.append(LABEL+'_'+UNITS)
                        types.append(TYPE)
                    datagramList.append({'ID':datagramID,'names':names,'types':types,'sample':sampleTime})
                break
        return datagramList
    
    def getSingleDatagramStructureForDeviceType(self,deviceType,datagramID):
        datagramList={}
        for device in self._xmlroot.findall('DEVICE_DATA'):
            DEVICE_TYPE=device.find('DEVICE_TYPE').text
            if DEVICE_TYPE==deviceType:                           # checks if DEVICE_TYPE == desired deviceType
                datagrams=device.findall('DATAGRAM')
                for datagram in datagrams:
                    names=[]
                    types=[]
                    datagramId=datagram.get('request')
                    if datagramId==datagramID:
                        sampleTime=datagram.get('sample')
                        variables=datagram.findall('DATA')
                        for variable in variables:
                            LABEL=variable.get('label')
                            TYPE=variable.get('type')
                            UNITS=variable.get('units')
                            names.append(LABEL+'_'+UNITS)
                            types.append(TYPE)
                        datagramList={'ID':datagramID,'names':names,'types':types,'sample':sampleTime}
                        break
                break
        return datagramList
    
    def parseDeviceConfFile(self):
        """
        EXTRACTS THE INFORMATION FROM THE CONFIGURATION FILE SENT BY THE SLAVES
        """
        
        node=self._xmlroot.find('DEVT')
        if node==None:
            raise XMLException('The device responded with an improper Conf.xml file, deviceType tag <DEVT> could not be found: ' + str(self._xmlroot.text))
        DEVICE_TYPE=node.text
        node=self._xmlroot.find('DEVC')
        if node==None:
            raise XMLException('The device responded with an improper Conf.xml file, deviceCode tag <DEVC> could not be found: ' + str(self._xmlroot.text))
        DEVICE_CODE=node.text
        # node=self._xmlroot.find('DEVIP')
        # if node==None:
            # raise XMLException('The device responded with an improper Conf.xml file, deviceIP tag <DEVIP> could not be found: ' + str(self._xmlroot.text))
        # DEVICE_IP=node.text.replace(',','.')
        DEVICE_IP=""
        return (DEVICE_TYPE,DEVICE_CODE,DEVICE_IP)   
    
    def Bytes2Float32(self,binnumber):
        
        if (binnumber & 1<<31)>0:
            sign=-1
        else:
            sign=1
        exponent=((binnumber>>23)    &    0xFF)-127
        significand=(binnumber&~(-1<<23));
        if    (exponent    ==    128):
            if significand:
                return    None #sign*float('NaN')  
            else:
                return    None #sign*float('inf')     
        elif    (exponent    ==    -127):
            if    (significand==0):    
                return    sign    *    0.0
        else:
            significand=(significand|(1<<23))/(1<<23);
        return sign*significand*2**exponent
    
    def parseDatagram(self):
        """
        :callback            datagram=myHttp.buildDatagram(xmlroot)
        :return datagram with structure (DeviceCode,DatagramId,data0,data1...dataN)
        """
        datagram=[]
        result=2
        for child in self._xmlroot:
            if child.tag=='VAR':
                integerValue=int(child.text)
                datagram.append(integerValue)
                #for i in range(0,8):
                    #print('Position ' + str(i) + ':',self.checkBit(integerValue, i))
            elif child.tag=='AV':
                floatValueBytes=[int(i) for i in child.text.split(',')]
                floatValueBin=(floatValueBytes[0]<<24)|(floatValueBytes[1]<<16)|(floatValueBytes[2]<<8)|(floatValueBytes[3])
                floatValue=self.Bytes2Float32(floatValueBin)
                datagram.append(floatValue)
            elif child.tag=='DEV':  # 
                datagram.insert(0,child.text)
                result-=1
            elif child.tag=='DId':
                datagram.insert(1,child.text)
                result-=1            
        return (result,datagram)      

class XMLException(Exception):
    def __name__(self):
        return 'XMLException'
    pass

class XMLParserTest(unittest.TestCase):
    def setUp(self):
        print("Setting up the xml file")
        self.XMLConfFile="""<?xml version = "1.0" ?>
                            <X>
                            <MASTER_IO>
                                <GPIO number='7' label='GPIO4' direction='OUT' default='0'></GPIO>
                                <GPIO number='11' label='GPIO17' direction='OUT' default='0'></GPIO>
                            </MASTER_IO>
                            *
                            </X>
                        """
        self.DEVICEDATA1="""<DEVICE_DATA dcode='1'>
                                <DEVICE_TYPE>GAPQv1</DEVICE_TYPE>
                                <ORDERS>
                                    <CMD order='D1_ON' label='Activate digital pin 1' pin='1' value='1'></CMD>
                                    <CMD order='D1_OFF' label='Deactivate digital pin 1' pin='1' value='0'></CMD>
                                    <CMD order='LOG=1' label='Start logging' pin='' value=''></CMD>
                                </ORDERS>
                                <DATAGRAM request='powers' dcode='0' sample='60'>
                                    <DATA label='STATUS' type='integer' units='bits'>
                                        <BIT pos='0' label='Lights circuit tripped'></BIT>
                                        <BIT pos='1' label='General plugs circuit tripped'></BIT>
                                        <BIT pos='2' label='Fridge plug circuit tripped'></BIT>
                                        <BIT pos='3' label='Oven plug circuit tripped'></BIT>
                                        <BIT pos='4' label='Washing machine plug circuit tripped'></BIT>
                                        <BIT pos='5' label='Differential tripped'></BIT>
                                        <BIT pos='6' label='Internal alarm'></BIT>
                                        <BIT pos='7' label='spare'></BIT>
                                    </DATA>
                                    <DATA label='P' type='float' units='kW'></DATA>
                                    <DATA label='Q' type='float' units='kVAr'></DATA>
                                    <DATA label='S' type='float' units='kVAs'></DATA>
                                    <DATA label='PF' type='float' units='percent'></DATA>
                                </DATAGRAM>
                                <DATAGRAM request='instant' dcode='1' sample='60'>
                                    <DATA label='Vrms' type='float' units='V'></DATA>
                                    <DATA label='Irms' type='float' units='A'></DATA>
                                    <DATA label='f' type='float' units='Hz'></DATA>
                                </DATAGRAM>
                            </DEVICE_DATA>
                            """
        self.DEVICEDATA2="""<DEVICE_DATA dcode='2'>
                                <DEVICE_TYPE>THsensorv1</DEVICE_TYPE>
                                <DATAGRAM request='data' dcode='0' sample='600'>
                                    <DATA label='T' type='float' units='centdeg'></DATA>
                                    <DATA label='RH' type='float' units='percent'></DATA>
                                    <DATA label='DewPoint' type='float' units='centdeg'></DATA>
                                </DATAGRAM>
                            </DEVICE_DATA>
                            """
        self.XMLDeviceConfFile="""<?xml version = "1.0" ?>
                                <X>
                                    <DEVT>GAPQv1</DEVT>        <!-- DEVICE TYPE THsensorv2 GAPQv1 -->
                                    <DEVC>0</DEVC>            <!-- DEVICE CODE -->
                                    <DEVIP>0,0,0,0</DEVIP>    <!-- DEVICE IP -->
                                </X> 
                            """
#    TESTS FOR THE FUNCTION parseConfFile
    def test1(self):
        """
        CHECKS THAT THE FUNCTION parseConfFile RETURNS APPROPRIATE VARIABLES WHEN OK
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1))
        parser=XMLParser(root)
        deviceList,datagramList,maxLenData=parser.parseConfFile()
        self.assertEqual(deviceList,[('GAPQv1','1')])
        """
        deviceList should gather the attributes [(<DEVICE_TYPE>,<DEVICE_DATA dcode>)] in a list of tuples
        """
        self.assertEqual(datagramList,[[['powers','0','60',('STATUS_bits_Lights circuit tripped$General plugs circuit tripped$Fridge plug circuit tripped$Oven plug circuit tripped$Washing machine plug circuit tripped$Differential tripped$Internal alarm$spare','integer'),('P_kW', 'float'),('Q_kVAr', 'float'),('S_kVAs', 'float'),('PF_percent', 'float')],
                                       ['instant','1','60',('Vrms_V', 'float'),('Irms_A', 'float'),('f_Hz', 'float')]]])
        """
        datagramList should gather the attributes [<DATAGRAM request>,<DATAGRAM dcode>,<DATAGRAM sample>,(Data0 label,Data0 type)...(DataN label, DataN type)]
        Data0 label = (<DATA label>+'_'+<DATA units>+'_'+<BIT label>+'$'+<BIT label>...,<DATA type>) if <DATA units>=='bits'
        Data0 label = (<DATA label>+'_'+<DATA units>) if <DATA units>!='bits'
        """
        self.assertEqual(maxLenData,5)
    
    def test2(self):
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN THE TAG <DEVICE_TYPE> IS EMPTY OR NOT PRESENT
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 2.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace('GAPQv1','')))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN TWO IDENTICAL TAGS <DEVICE_TYPE> ARE FOUND
        """
        print("Start of the test 2.2")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1+self.DEVICEDATA1))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
    
    def test3(self):
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN MISSING THE ATTRIBUTE <DEVICE_DATA dcode>
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 3.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("DEVICE_DATA dcode='1'",'DEVICE_DATA')))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN TWO IDENTICAL ATTRIBUTES <DEVICE_DATA dcode> ARE FOUND
        """
        print("Start of the test 3.2")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1+self.DEVICEDATA1.replace('GAPQv1','THsensorv1')))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
    
    def test4(self):
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN MISSING THE ATTRIBUTE <DATAGRAM request>
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 4.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("DATAGRAM request='powers'",'DATAGRAM')))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN TWO IDENTICAL ATTRIBUTES <DEVICE_DATA dcode> ARE FOUND
        """
        print("Start of the test 4.2")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("DATAGRAM request='powers'","DATAGRAM request='instant'")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
        
    def test5(self):
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN MISSING THE ATTRIBUTE <DATAGRAM dcode>
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 5.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("<DATAGRAM request='instant' dcode='1'","<DATAGRAM request='instant'")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN TWO IDENTICAL ATTRIBUTES <DATAGRAM dcode> ARE FOUND
        """
        print("Start of the test 5.2")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("<DATAGRAM request='instant' dcode='1'","<DATAGRAM request='instant' dcode='0'")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN THE ATTRIBUTE <DATAGRAM dcode> IS OUTSIDE THE RANGE BETWEEN 0-255
        """
        print("Start of the test 5.3")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("<DATAGRAM request='instant' dcode='1'","<DATAGRAM request='instant' dcode='-1'")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)
        
    def test6(self):
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN MISSING THE ATTRIBUTE <DATAGRAM sample>
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 6.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("<DATAGRAM request='instant' dcode='1' sample='60'>","<DATAGRAM request='instant' dcode='1'>")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)    
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN THE ATTRIBUTE <DATAGRAM sample> IS NOT CASTABLE TO AN INT
        """
        print("Start of the test 6.2")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("<DATAGRAM request='instant' dcode='1' sample='60'>","<DATAGRAM request='instant' dcode='1' sample='F'>")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)  
    
    def test7(self):
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN MISSING THE ATTRIBUTE <DATA type> 
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 7.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("<DATA label='P' type='float' units='kW'></DATA>","<DATA label='P' units='kW'></DATA>")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)    
        """
        CHECKS THAT THE FUNCTION parseConfFile RAISES ERROR WHEN THE ATTRIBUTE <DATA type> is not one of the available types ('integer' or 'float')
        """
        print("Start of the test 7.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("<DATA label='P' type='float' units='kW'></DATA>","<DATA label='P' type='xx' units='kW'></DATA>")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseConfFile)    
        
        
#    TESTS FOR THE FUNCTION parseDeviceConfFile
    def test8(self):
        """
        CHECKS THAT THE FUNCTION parseDeviceConfFile RETURNS APPROPRIATE VARIABLES WHEN OK
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 8.1")
        root = ET.fromstring(self.XMLDeviceConfFile)
        parser=XMLParser(root)
        DEVICE_TYPE,DEVICE_CODE,DEVICE_IP=parser.parseDeviceConfFile()
        self.assertEqual(DEVICE_TYPE,'GAPQv1')
        self.assertEqual(DEVICE_CODE,'0')
        self.assertEqual(DEVICE_IP,'0.0.0.0')
        """
        CHECKS THAT THE FUNCTION parseDeviceConfFile RAISES AN ERROR WHEN IMPROPER Conf.xml FILE IS RECEIVED
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 8.2")
        root = ET.fromstring(self.XMLDeviceConfFile.replace('DEVT','D'))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.parseDeviceConfFile)  
        
#    TESTS FOR THE FUNCTION getOrdersConfFile
    def test9(self):
        """
        CHECKS THAT THE FUNCTION getOrdersConfFile RETURNS APPROPRIATE VARIABLES WHEN OK
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 8.1")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1))
        parser=XMLParser(root)
        commands=parser.getOrdersConfFile(deviceType='GAPQv1')
        self.assertEqual(commands,[{'cmd': 'D1_ON', 'label': 'Activate digital pin 1','pin':'1','value':'1'},
                                   {'cmd': 'D1_OFF', 'label': 'Deactivate digital pin 1','pin':'1','value':'0'},
                                   {'cmd': 'LOG=1', 'label': 'Start logging','pin':'','value':''}
                                   ])
        """
        CHECKS THAT THE FUNCTION getOrdersConfFile RETURNS APPROPRIATE VARIABLES WHEN DEVICE HAS NO ORDERS DEFINED
        """
        print("Start of the test 8.2")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA2))
        parser=XMLParser(root)
        commands=parser.getOrdersConfFile(deviceType='THsensorv1')
        self.assertEqual(commands,[])
        """
        CHECKS THAT THE FUNCTION getOrdersConfFile RETURNS EXCEPTION DEVICE HAS ATTRIBUTE pin DEFINED BUT NO value
        """
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1.replace("value='0'","value=''")))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.getOrdersConfFile,'GAPQv1') 
        
#    TESTS FOR THE FUNCTION getOrdersConfFile
    def test10(self):
        """
        CHECKS THAT THE FUNCTION getMasterGPIOConfFile RETURNS APPROPRIATE VARIABLES WHEN OK
        """
        import xml.etree.ElementTree as ET
        print("Start of the test 10")
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1))
        parser=XMLParser(root)
        commands=parser.getMasterGPIOConfFile()
        self.assertEqual(commands,[{'number': '7', 'label': 'GPIO4','direction':'OUT','default':'0'},
                                   {'number': '11', 'label': 'GPIO17','direction':'OUT','default':'0'},
                                   ])
        """
        CHECKS THAT THE FUNCTION getMasterGPIOConfFile RETURNS EXCEPTION WHEN INCORRECT DIRECTION DEFINED
        """
        root = ET.fromstring(self.XMLConfFile.replace('*',self.DEVICEDATA1).replace("label='GPIO4' direction='OUT'","label='GPIO4' direction='OUTPUT'"))
        parser=XMLParser(root)
        self.assertRaises(XMLException,parser.getMasterGPIOConfFile) 
        
if __name__ == '__main__':
    unittest.main()
                        