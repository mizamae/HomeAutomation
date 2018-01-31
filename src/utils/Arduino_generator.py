import os

from django.conf import settings

import Devices.GlobalVars
from Devices.models import DeviceType,DatagramModel,getDatagramStructure,CommandModel
#import Devices.XML_parser
import logging
logger = logging.getLogger("project")

def create_arduino_code():
    #import xml.etree.ElementTree as ET
    
    #xmlroot = ET.parse(Devices.GlobalVars.XML_CONFFILE_PATH).getroot()
    #XMLParser=Devices.XML_parser.XMLParser(xmlroot=xmlroot)
    #deviceList,datagramList,maxLenData=XMLParser.parseConfFile() 
    deviceList=DeviceType.objects.all()
    logger.debug("Creating Arduino template for devices " + str(deviceList))
    deviceIndex=0
    files=[]
    for device in deviceList:
        deviceType=device.Code
        datagramList=DatagramModel.objects.filter(DeviceType=device)
        logger.debug("Creating Arduino template for devices " + str(deviceType))
        logger.debug("for the following datagrams " + str(datagramList))
        files.append(deviceType+'.ino')
        f = open(os.path.join(settings.MEDIA_ROOT,deviceType+'.ino'), 'w')
        #deviceType.append(device)    
        
        string_header='''

#include <ESP8266WiFi.h>
#include <EEPROM.h>


// MAC address from Ethernet shield sticker under board
//byte mac[] = { 0xDE, 0xAD, 0xBE, 0x41, 0x42, 0x21 }; // make sure you change these values so that no MAC collision exist in your network

const char* ssid = "diy4dot0";
const char* password = "putyourpasswhere";

#variables_to_declare#

WiFiServer server(80);  // create a server at port 80
WiFiClient client;
static uint8_t baseREQ=0,orderREQ=0,webREQ=0; 

struct XML_TAGS_BYTE // size 16 bytes
{
  const char _TAG_[5]; 
  const char _VALUE_TAG_;
  const char _cTAG_[6];   
}var_tag =  {
                {'<','V','A','R','>'},
                '$',
                {'<','/','V','A','R','>'} 
              };
              
struct XML_TAGS_FLOAT // size 20 bytes
{
  const char _TAG_[4]; 
  const char _VALUE_TAG_[7];
  const char _cTAG_[5];   
}var_tag_float =  {
                {'<','A','V','>'},
                {'$',',','$',',','$',',','$'},
                {'<','/','A','V','>'} 
              };

struct XML_RESPONSES_Conf
{
  const char  _HTML_RESPONSE_OK_[16];
  const char _BLANKLINE_ ;
  
  const char _XML_HEADER_[25];
  const char _XML_TAG_[3];
  const char _XML_DEVT_TAG_[6];
  const char _XML_DEVT_[6];
  const char _cXML_DEVT_TAG_[7];
  const char _XML_DEVC_TAG_[6];
  char _XML_DEVC_[1];
  const char _cXML_DEVC_TAG_[7];
  const char _cXML_TAG_[5];
}xml_response_Conf= {
                 {'H','T','T','P','/','1','.','1',' ','2','0','0',' ','O','K','\\n'},
                  '\\n',
                 {'<','?','x','m','l',' ','v','e','r','s','i','o','n',' ','=',' ','"','1','.','0','"',' ','?','>','\\n'},
                 {'<','X','>'},
                 {'<','D','E','V','T','>'},{DeviceType},{'<','/','D','E','V','T','>'},
                 {'<','D','E','V','C','>'},{'$'},{'<','/','D','E','V','C','>'},
                 {'<','/','X','>','\\n'}  
                };

const char *pXML_RESP_Conf    =    &xml_response_Conf._HTML_RESPONSE_OK_[0];
const int __SIZE_XML_RESPONSE_Conf__    =    sizeof(xml_response_Conf);


'''.replace('#MAC_ADDR#',str(20+deviceIndex))
        #f.write(string_header)
        string='''              
struct XML_RESPONSES_#datagramID# 
{
  const char  _HTML_RESPONSE_OK_[16];
  const char _BLANKLINE_ ;
  
  const char _XML_HEADER_[25];
  const char _XML_TAG_[3];
  const char _XML_DEV_TAG_[5];
  const char _XML_DEV_[1];
  const char _cXML_DEV_TAG_[6];
  const char _XML_DId_TAG_[5];
  const char _XML_DId_[1];
  const char _cXML_DId_TAG_[6];
  struct XML_TAGS_BYTE BYTE_DATA_TAGS[#numIntegerVariables#];
  struct XML_TAGS_FLOAT FLOAT_DATA_TAGS[#numFloatVariables#];
  const char _cXML_TAG_[5];
}xml_response_#datagramID# = {
                 {'H','T','T','P','/','1','.','1',' ','2','0','0',' ','O','K','\\n'},
                 '\\n',
                 {'<','?','x','m','l',' ','v','e','r','s','i','o','n',' ','=',' ','"','1','.','0','"',' ','?','>','\\n'},
                 {'<','X','>'},
                 {'<','D','E','V','>'},{#},{'<','/','D','E','V','>'},
                 {'<','D','I','d','>'},{'#datagramCode#'},{'<','/','D','I','d','>'},
                 {#IntegerVariablesTags#},{#FloatVariablesTags#},
                 {'<','/','X','>','\\n'}  
                };

const char *pXML_RESP_#datagramID# = &xml_response_#datagramID#._HTML_RESPONSE_OK_[0];
const int __SIZE_XML_RESPONSE_#datagramID#__ = sizeof(xml_response_#datagramID#);

'''
        string2='''
              if (StrContains(HTTP_req, "#datagramID#"))
              {
                *baseREQ = #datagramCode#;
                break;
              }
'''       
        string3='''
      var[#num#]=#vartag#;
        '''
        string4='''
         var[i+#num#]=*((byte*)&#vartag#+3-i);
'''  
        string5='''
    case #datagramCode#:   // request for "#datagramID#.xml"
      #integervariables#
      for (byte i=0;i<4;i++)
      {
         #floatvariables#
      }
      XML_response2(&var[0],__SIZE_XML_RESPONSE_#datagramID#__,*pXML_RESP_#datagramID#);
      delay(10);
      *baseREQ=0;
      break;        
''' 
        string_requests=''
        
        datagram_variables=[]
        declaring_variables=['uint8_t IPaddr[4];\n','uint8_t DeviceCode;\n','const String DeviceType="%s"; \n' % deviceType]
        tempString=''
        maxnumbytes=0
        for datagram in datagramList:
            string_int_variables=''
            string_float_variables=''
            row_values=[]
            row_values.append(deviceType)               # loads the device type
            #col_tags=[]
            #col_types=[]
            #DatagramId.append(datagram[0])
            datagramID=datagram.Identifier # Load the datagram identifier
            datagramCode=datagram.Code          # Load the datagram identifier Code            
            integer_string=''
            integer_number=0
            float_string=''
            float_number=0
            datagramStructure=getDatagramStructure(devicetype=deviceType,ID=datagramID)
            for var_tag,var_type in zip(datagramStructure['names'],datagramStructure['types']):
                if var_type=='integer':
                    integer_string=integer_string+',var_tag'
                    if (var_tag.find('$')>=0): # var_tag=STATUS_bits_Alarm0;Alarm1;Alarm2;Alarm3;Alarm4;Alarm5;Alarm6;Alarm7 
                                            #to remove the char ; from the name of the columns
                        tempname=var_tag.split('_')
                        name=tempname[0]
                        for component in tempname[1:]:
                            if '$' in component: # found the $ item meaning bit labels
                                break
                            name=name+'_'+component
                        var_name=name
                    else:
                        var_name=var_tag
                    if not (var_name in declaring_variables):
                        declaring_variables.append('byte ' + var_name.replace(' ','_') + ';\n')
                    string_int_variables+=string3.replace('#num#',str(integer_number)).replace('#vartag#',var_name)
                    integer_number+=1 
                elif var_type=='float':
                    float_string=float_string+',var_tag_float'
                    if not (var_tag in declaring_variables):
                        declaring_variables.append('float ' + var_tag.replace(' ','_') + ';\n')
                    string_float_variables+=string4.replace('#num#',str(integer_number+float_number*4)).replace('#vartag#',var_tag)
                    float_number+=1
            if len(integer_string)>0:
                integer_string=integer_string[1:]   # to remove the first comma     
            if len(float_string)>0:
                float_string=float_string[1:]   # to remove the first comma     
            datagram_variables.append(string5.replace('#datagramID#', datagramID).replace('#integervariables#',string_int_variables)
                        .replace('#floatvariables#',string_float_variables).replace('#datagramCode#',str(int(datagramCode)+2)))
            tempString=tempString+(string.replace('#datagramID#', datagramID).replace('#numIntegerVariables#', str(integer_number))
                                        .replace('#numFloatVariables#', str(float_number)).replace('#IntegerVariablesTags#',integer_string)
                                        .replace('#FloatVariablesTags#',float_string).replace('#datagramCode#',str(datagramCode)))
            numberofbytes=float_number*4+integer_number
            if numberofbytes>maxnumbytes:
                maxnumbytes=numberofbytes
#             f.write(string.replace('#datagramID#', datagramID).replace('#numIntegerVariables#', str(integer_number))
#                         .replace('#numFloatVariables#', str(float_number)).replace('#IntegerVariablesTags#',integer_string)
#                         .replace('#FloatVariablesTags#',float_string).replace('#datagramCode#',datagramCode))
            string_requests+=string2.replace('#datagramID#', datagramID).replace('#datagramCode#',str(int(datagramCode)+2))
        deviceIndex+=1
        
        temp=''
        for variableTodeclare in declaring_variables:
            temp=temp+variableTodeclare
        
        f.write(string_header.replace('#variables_to_declare#',temp))
        f.write(tempString)
        f.write('''
// EEPROM structure
const uint8_t _EEPROMaddrDEVICECODE_      = 0;     // address for the deviceCode in EEPROM
const uint8_t _EEPROMaddrIP_B0_           = 1;     // address for the LSB of IP address in EEPROM
const uint8_t _EEPROMaddrIP_B1_           = 2;     // address for the 2nd Byte of IP address in EEPROM
const uint8_t _EEPROMaddrIP_B2_           = 3;     // address for the 3rd Byte of IP address in EEPROM
const uint8_t _EEPROMaddrIP_B3_           = 4;     // address for the MSB of IP address in EEPROM


// CONFIG BUTON
const byte _CONF_BTN_                    = 2;        // pin to initiate config procedure

static bool configured_device=false;
''')
        
            
        f.write('''void setup()
{
    Serial.begin(115200);
    
    EEPROM.begin(512);
    DeviceCode = EEPROM.read(_EEPROMaddrDEVICECODE_);
    Serial.print("DeviceCode in EEPROM: ");
    Serial.println(DeviceCode);
//    DeviceCode=255;
    
    if ((DeviceCode==255)||(DeviceCode==254)||!digitalRead(_CONF_BTN_)) // the device has not been configured. This is so in Arduino devices where EEPROM defaults to 255. In ESP8266 flash is randomly defaulted!!!
    {
        DeviceCode=254;
        IPaddr[0]=254;
        IPaddr[1]=10;
        IPaddr[2]=10;
        IPaddr[3]=10;
        Serial.println("Unconfigured device");
        configured_device=false;
    }else
    {
        IPaddr[0]=EEPROM.read(_EEPROMaddrIP_B0_);
        IPaddr[1]=EEPROM.read(_EEPROMaddrIP_B1_);
        IPaddr[2]=EEPROM.read(_EEPROMaddrIP_B2_);
        IPaddr[3]=EEPROM.read(_EEPROMaddrIP_B3_);
        Serial.print("Configured device with IP: ");
        Serial.print(IPaddr[3]); 
        Serial.print(".");
        Serial.print(IPaddr[2]); 
        Serial.print(".");
        Serial.print(IPaddr[1]); 
        Serial.print(".");
        Serial.println(IPaddr[0]);    
        configured_device=true;
    }
    
    IPAddress ip(IPaddr[3], IPaddr[2], IPaddr[1], IPaddr[0]);   // IP address, may need to change depending on network
    IPAddress gateway(IPaddr[3], IPaddr[2], IPaddr[1], 1);      // set gateway to match your network
    IPAddress subnet(255, 255, 255, 0);                         // set subnet mask to match your network
    
    WiFi.config(ip, gateway, subnet);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
   
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    
    Serial.println("");
    Serial.println("WiFi connected");
     
    // Start the server
    server.begin();
    Serial.println("Server started");
   
    // Print the IP address
    Serial.print("Use this URL to connect: ");
    Serial.print("http://");
    Serial.print(WiFi.localIP());
    Serial.println("/");
    
    Serial.print("MAC: ");
    Serial.println(WiFi.macAddress());
    
}

void loop()
{
    delay(10);    
    client = server.available();  // try to get client
    
    if (client)  // got client?
    {
        while((!client.available()) && (timeout<3)){
            delay(1);
            timeout++;
        }
        processREQWIFI(&baseREQ,&orderREQ,&webREQ);
    
        if (baseREQ||orderREQ||webREQ)
        {
            responseREQ(&baseREQ,&orderREQ,&webREQ);
        }
        client.stop(); // close the connection
    }else
    {
        delay(50);
    } 
    
    
}

'''.replace('#deviceType#', deviceType))    
        string_orders='''
                        if (StrContains(HTTP_req, "#order_cmd#"))
                        {
                            *orderREQ;
                            break;
                        }
                        '''
        stringcaseOrders='''
    case #num_order#: // orders_label 
    
        *orderREQ=0;
        break;  
    '''
        stringOrders=''
        stringCaseOrders=''
        #orders=XMLParser.getOrdersConfFile(deviceType=deviceType)
        orders=CommandModel.objects.filter(DeviceType=deviceType)
        num_order=1
        for order in orders:
            stringOrders+=string_orders.replace('#order_cmd#',order.Identifier).replace('*orderREQ','*orderREQ='+str(10+num_order))
            stringCaseOrders+=stringcaseOrders.replace('orders_label','Execution for ' + order.HumanTag).replace('#num_order#',str(10+num_order))
            num_order+=1
            
        string='''
void processREQWIFI(byte *baseREQ,byte *orderREQ,byte *webREQ)
{
    // HTML BUFFER CONFIGURATION
    #define REQ_BUF_SZ   60
    char HTTP_req[REQ_BUF_SZ] = { 0 }; // buffered HTTP request stored as null terminated string
    unsigned int req_index = 0;              // index into HTTP_req buffer

    unsigned long time_ini = millis();
    boolean buffer_overflow = false;
    boolean currentLineIsBlank = true;

    while (client.connected()) {
        if (client.available()) {   // client data available to read
            char c = client.read(); // read 1 byte (character) from client
            // limit the size of the stored received HTTP request
            // buffer first part of HTTP request in HTTP_req array (string)
            // leave last element in array as 0 to null terminate string (REQ_BUF_SZ - 1)
            if (req_index < (REQ_BUF_SZ - 2)) {
                HTTP_req[req_index] = c;          // save HTTP request character
                req_index++;
            }
            else 
            { 
                buffer_overflow=true;
            }
            // last line of client request is blank and ends with \n
            // respond to client only after last line received
            if ((c == '\\n' && currentLineIsBlank)|| buffer_overflow) // this is to avoid getting stuck if no proper message is received
            {
              if (StrContains(HTTP_req, "orders"))
              {
                        if (StrContains(&request[0], "SetConf"))// repeat this conditional for the different orders to be received             
                        {// request="POST /orders/SetConf.htm?DEVC=2 HTTP/1.1"
                            *orderREQ = 10;
                            uint8_t index=0;
                            while (request[index]!='='){index++;}
                            Serial.print("Found = at position ");
                            Serial.println(index);
                            index++;
                            uint8_t code[3];
                            uint8_t i=0;
                            while (request[index]!=' ')
                            {
                              code[i]=request[index]-48; // to obtain the number from the ascii char
                              index++;
                              i++;
                            }
                            if (i==1){DeviceCode=code[0];}
                            if (i==2){DeviceCode=code[0]*10+code[1];}
                            if (i==3){DeviceCode=code[0]*100+code[1]*10+code[2];}
                        }
                        #orders_for_device#
              } 
              
              if (StrContains(HTTP_req, "Conf.xml"))
              {
                *baseREQ = 1;
                break;
              }
              #stringRequests#
              break;
            }
            // every line of text received from the client ends with \r\n
            if (c == '\\n') {
                // last character on line of received text
                // starting new line with next character read
                currentLineIsBlank = true;
            } 
            else if (c != '\\r') {
                // a text character was received from client
                currentLineIsBlank = false;
            }
          } // end if (client.available())
    } // end while (client.connected())
}     
'''.replace('#orders_for_device#',stringOrders)
        f.write(string.replace('#stringRequests#',string_requests))
        
        string='''
void responseREQ(byte *baseREQ,byte *orderREQ,byte *webREQ)
{
    byte var[#maxnumbytes#];
    switch (*orderREQ)
    {
    case 10: // orders from the controller to setup the new configuration

        *orderREQ=0;
        EEPROM.write(_EEPROMaddrIP_B0_,DeviceCode);
        EEPROM.write(_EEPROMaddrIP_B1_,10);
        EEPROM.write(_EEPROMaddrIP_B2_,10);
        EEPROM.write(_EEPROMaddrIP_B3_,10);
        EEPROM.write(_EEPROMaddrDEVICECODE_,DeviceCode);
        EEPROM.end();
        Serial.print("DeviceCode to be set at ");
        Serial.println(DeviceCode);
        byte kk;
        XML_response2(&kk,__SIZE_RESPONSE_OK__,pRESP_OK); // sends the status of all switches
        break;    
    #stringCaseOrders#
    }
    switch (*baseREQ)
    {
    case 1: // request of the configuration "Conf.xml"
      byte kk;
      XML_response2(&kk,__SIZE_XML_RESPONSE_Conf__,pXML_RESP_Conf); // sends the status of all switches
      delay(10);
      *baseREQ=0;
      break; 
        #datagramsResponses#
    }
}
        
'''.replace('#maxnumbytes#',str(maxnumbytes)).replace('#stringCaseOrders#',stringCaseOrders)
        string2='''
        
        '''
        for data in datagram_variables:
            string2+=data
        f.write(string.replace('#datagramsResponses#',string2))           
        
        
        f.write('''
byte XML_response2(byte *data, const int num_bytes, const char *pRESP)
{
    uint8_t d = 0;
    String frame="";
    for (int i = 0; i<num_bytes; i++)
    {
        if (*(pRESP + i) == '$') // data to be inserted
        {
            frame += String((*(data + d)));
            d++;
        }
        else if (*(pRESP + i) == '#') // DeviceCode to be inserted
        {
            frame+=String(DeviceCode);
        }
        else  // literal characters from XML structure
        {
            frame+=(*(pRESP + i));
        }
    }
    client.print(frame);
}


// sets every element of str to 0 (clears array)
void StrClear(char *str, char length)
{
    for (int i = 0; i < length; i++) {
        str[i] = 0;
    }
}

// searches for the string sfind in the string str
// returns 1 if sfind is found in str
// returns 0 if sfind is not found in str
byte StrContains(char *str, char *sfind)
{
    char found = 0;
    char index = 0;
    char lenstr, lensfind;

    lenstr = strlen(str);
    lensfind = strlen(sfind);
    
    while (index < lenstr) 
    {
        if (str[index] == sfind[found]) 
        {
            found++;
            if (lensfind == found) 
            {
                return 1;
            }
        }
        else 
        {
            found = 0;
        }
        index++;
    }

    return 0;
}        
''')
        f.close()
    #fin creando las plantillas Arduino
    return files
    

if __name__ == '__main__':
    create_arduino_code()