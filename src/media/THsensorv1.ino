
#include <Ethernet.h>        
#include <EEPROM.h>

// MAC address from Ethernet shield sticker under board
byte mac[] = { 0xDE, 0xAD, 0xBE, 0x41, 0x42, 0x21 }; // make sure you change these values so that no MAC collision exist in your network

uint8_t IPaddr[4];
uint8_t DeviceCode;
const String DeviceType="THsensorv1"; 
byte STATUS_bits;
float T_centdeg;
float RH_percent;


EthernetServer server(80);  // create a server at port 80
EthernetClient client;
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
  const char _XML_HEADER_[25];
  const char _XML_TAG_[3];
  const char _XML_DEVT_TAG_[6];
  String _XML_DEVT_;
  const char _cXML_DEVT_TAG_[7];
  const char _XML_DEVC_TAG_[6];
  char _XML_DEVC_[1];
  const char _cXML_DEVC_TAG_[7];
  const char _XML_DEVIP_TAG_[7];
  char _XML_DEVIP_[4];
  const char _cXML_DEVIP_TAG_[8];
  const char _cXML_TAG_[5];
}xml_response_Conf= {
                 {'<','?','x','m','l',' ','v','e','r','s','i','o','n',' ','=',' ','"','1','.','0','"',' ','?','>','\n'},
                 {'<','X','>'},
                 {'<','D','E','V','T','>'},{DeviceType},{'<','/','D','E','V','T','>'},
                 {'<','D','E','V','C','>'},{DeviceCode},{'<','/','D','E','V','C','>'},
                 {'<','D','E','V','I','P','>'},{IPaddr},{'<','/','D','E','V','I','P','>'},
                 {'<','/','X','>','\n'}  
                };

const char *pXML_RESP_Conf    =    &xml_response_Conf._XML_HEADER_[0];
const int __SIZE_XML_RESPONSE_Conf__    =    sizeof(xml_response_Conf);


              
struct XML_RESPONSES_data 
{
//  const char  _HTML_RESPONSE_OK_[16];
//  const char _KEEP_ALIVE_[30];
//  const char _HTML_CONN_ALIVE_[23];
//  const char _XML_CONTENT_TYPE_[30];
//  const char _BLANKLINE_ ;
  const char _XML_HEADER_[25];
  const char _XML_TAG_[3];
  const char _XML_DEV_TAG_[5];
  const char _XML_DEV_[1];
  const char _cXML_DEV_TAG_[6];
  const char _XML_DId_TAG_[5];
  const char _XML_DId_[1];
  const char _cXML_DId_TAG_[6];
  struct XML_TAGS_BYTE BYTE_DATA_TAGS[1];
  struct XML_TAGS_FLOAT FLOAT_DATA_TAGS[2];
  const char _cXML_TAG_[5];
}xml_response_data = {
//                 {'H','T','T','P','/','1','.','1',' ','2','0','0',' ','O','K','\n'},
//                 {'K','e','e','p','-','A','l','i','v','e',':',' ','t','i','m','e','o','u','t','=','5',',',' ','m','a','x','=','9','9','\n'},
//                 {'C','o','n','n','e','c','t','i','o','n',':',' ','K','e','e','p','-','A','l','i','v','e','\n'},
//                 {'C','o','n','t','e','n','t','-','T','y','p','e',':',' ','a','p','p','l','i','c','a','t','i','o','n','/','x','m','l','\n'},
//                 '\n',
                 {'<','?','x','m','l',' ','v','e','r','s','i','o','n',' ','=',' ','"','1','.','0','"',' ','?','>','\n'},
                 {'<','X','>'},
                 {'<','D','E','V','>'},{DeviceCode},{'<','/','D','E','V','>'},
                 {'<','D','I','d','>'},{0},{'<','/','D','I','d','>'},
                 {var_tag},{var_tag_float,var_tag_float},
                 {'<','/','X','>','\n'}  
                };

const char *pXML_RESP_data = &xml_response_data._XML_HEADER_[0];
const int __SIZE_XML_RESPONSE_data__ = sizeof(xml_response_data);


// EEPROM structure
const uint8_t _EEPROMaddrDEVICECODE_      = 0;     // address for the deviceCode in EEPROM
const uint8_t _EEPROMaddrIP_B0_           = 1;     // address for the LSB of IP address in EEPROM
const uint8_t _EEPROMaddrIP_B1_           = 2;     // address for the 2nd Byte of IP address in EEPROM
const uint8_t _EEPROMaddrIP_B2_           = 3;     // address for the 3rd Byte of IP address in EEPROM
const uint8_t _EEPROMaddrIP_B3_           = 4;     // address for the MSB of IP address in EEPROM


// CONFIG BUTON
const byte _CONF_BTN_                    = 2;        // pin to initiate config procedure
void setup()
{
    DeviceCode = EEPROM.read(_EEPROMaddrDEVICECODE_);
    IPaddr[0]=EEPROM.read(_EEPROMaddrIP_B0_);
    IPaddr[1]=EEPROM.read(_EEPROMaddrIP_B1_);
    IPaddr[2]=EEPROM.read(_EEPROMaddrIP_B2_);
    IPaddr[3]=EEPROM.read(_EEPROMaddrIP_B3_);
    
    if ((DeviceCode==255)||(DeviceCode==0)||!digitalRead(_CONF_BTN_)) // the device has not been configured
    {
        DeviceCode=0;
        IPaddr[0]=0;
        IPaddr[1]=10;
        IPaddr[2]=10;
        IPaddr[3]=10;
        
    }
    IPAddress ip(IPaddr[3], IPaddr[2], IPaddr[1], IPaddr[0]); // IP address, may need to change depending on network
    
    Ethernet.begin(mac, ip);  // initialize Ethernet device
    server.begin();           // start to listen for clients
    
}

void loop()
{
    delay(10);    
    client = server.available();  // try to get client
    
    if (client)  // got client?
    {
        processREQWIFI(&baseREQ,&orderREQ,&webREQ);
    
        if (baseREQ||orderREQ||webREQ)
        {
            responseREQ(&baseREQ,&orderREQ,&webREQ);
        }
    } 
    
    client.stop(); // close the connection
}


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
            // last line of client request is blank and ends with 

            // respond to client only after last line received
            if ((c == '\n' && currentLineIsBlank)|| buffer_overflow) // this is to avoid getting stuck if no proper message is received
            {
              if (StrContains(HTTP_req, "orders"))
              {
                        if (StrContains(HTTP_req, "SetConf"))// repeat this conditional for the different orders to be received             
                        {
                            *orderREQ = 10;
                            break;
                        }
                        
              } 
              
              if (StrContains(HTTP_req, "Conf.xml"))
              {
                *baseREQ = 1;
                break;
              }
              
              if (StrContains(HTTP_req, "data"))
              {
                *baseREQ = 2;
                break;
              }

              break;
            }
            // every line of text received from the client ends with 

            if (c == '\n') {
                // last character on line of received text
                // starting new line with next character read
                currentLineIsBlank = true;
            } 
            else if (c != '\r') {
                // a text character was received from client
                currentLineIsBlank = false;
            }
          } // end if (client.available())
    } // end while (client.connected())
}     

void responseREQ(byte *baseREQ,byte *orderREQ,byte *webREQ)
{
    byte var[9];
    switch (*orderREQ)
    {
    case 10: // orders from the controller to setup the new configuration

        *orderREQ=0;
        break;  
    
    }
    switch (*baseREQ)
    {
    case 1: // request of the configuration "Conf.xml"
      byte kk;
      XML_response2(&kk,__SIZE_XML_RESPONSE_Conf__,pXML_RESP_Conf); // sends the status of all switches
      delay(10);
      *baseREQ=0;
      break; 
        
        
        
    case 2:   // request for "data.xml"
      
      var[0]=STATUS_bits;
        
      for (byte i=0;i<4;i++)
      {
         
         var[i+1]=*((byte*)&T_centdeg+3-i);

         var[i+5]=*((byte*)&RH_percent+3-i);

      }
      XML_response2(&var[0],__SIZE_XML_RESPONSE_data__,*pXML_RESP_data);
      delay(10);
      *baseREQ=0;
      break;        

    }
}
        

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
