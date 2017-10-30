from django.utils import timezone
import datetime
import logging
import random
import sys

import requests

import Devices.BBDD
import Devices.GlobalVars
import Devices.XML_parser
import RemoteDevices.models

import RemoteDevices.signals

import xml.etree.ElementTree as ET


logger = logging.getLogger("project")

# server='http://127.0.0.1'
# webpage='index.htm'

class HTTP_requests():
    def __init__(self,server,year=''):
        self.server=server
        self.AppDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH, year=year)
    
    def remap_server(self,server):
        self.server=server
                  
    def request_web(self,webpage):
        """
        Requests a webpage from a server
        :param server: 
        :param webpage:
        :return 0 if OK
        :call myHttp.web_request(webpage)
        """
        try:
            r = requests.get(self.server+'/'+webpage)
            if r.status_code==200:
                #print(r.text)
                return 0
            else:
                return r.status_code
        except:
            print ("Unexpected error in web_request:", sys.exc_info()[1]) 
            logger.error("Unexpected error in web_request:"+str(sys.exc_info()[1])) 
            return None
    
    def request_file(self,file,destination):
        """
        Requests a file from a server
        :param server: 
        :param file: name of the file
        :param destination: path to save the received file 
        :return: 0 if OK. Server error code if error
        :callback:      file='datalog.txt'
                        destination='d://'
                        myHttp.file_request(server, file,destination)
        """
        try:
            r = requests.get(self.server+'/'+file+'?t='+str(random.random()),stream=True)
            if r.status_code==200:
                #print(r.text)
                with open(destination+file, 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)
                return 0
            else:
                return r.status_code
        except:
            print ("Unexpected error in file_request:", sys.exc_info()[1]) 
            logger.error ("Unexpected error in file_request:"+ str(sys.exc_info()[1])) 
            return 2
            
    def request_orders(self,order,payload,timeout=1):
        """
        :callback       payload = {'key1': 'value1', 'key2': 'value2'}   
                        self.orders_request(server, 'orders', payload) 
        """
        try:
            r = requests.post(self.server+'/orders/'+order,params=payload,timeout=timeout)
            #print(r.url)
            if r.status_code==200:
                #print(r.text)
                return (200,r)
            else:
                return (r.status_code,None)
        except:
            print ("Unexpected error in orders_request:", sys.exc_info()[1]) 
            logger.error("Unexpected error in orders_request:"+ str(sys.exc_info()[1])) 
            return (100,None)
                
    def checkBit(self,number,position):
        mask=1<<position
        if (number & mask)!=0:
            return True
        else:
            return False  
    
    def request_confXML(self,xmlfile,timeout=1):
        """
        Requests a xml file from a server
        :param server: 
        :param xmlfile:
        :return: root to the xml. Server error code if error
        :callback:      xmlfile='angles.xml'
                        xmlroot=myHttp.xml_request(server, xmlfile)
        """
        try:
            r = requests.get(self.server+'/'+xmlfile+'?t='+str(random.random()),timeout=timeout)     
            if r.status_code==200:
                #print(r.text)
                root = ET.fromstring(r.text)                
                return (r.status_code,root)
            else:
                return (r.status_code,None)
        except:
            logger.error("Unexpected error in xml_data_request:"+ str(sys.exc_info()[1])) 
            return (100,None)
        
    def request_datagram(self,DeviceCode,DatagramId,timeout=1,writeToDB=True,retries=3):
        """
        Requests a xml file from a server
        :param DatagramId: DatagramId='angles.xml'
        :param deviceCode:
        :callback:      

        """
        temp=[]
        DV=RemoteDevices.models.DeviceModel.objects.get(DeviceCode=DeviceCode)
        deviceName=DV.DeviceName
        timestamp=timezone.now() #para hora con info UTC   
        try:
            logger.info('Request: '+self.server+'/'+DatagramId+'.xml?t='+str(random.random()))
            r = requests.get(self.server+'/'+DatagramId+'.xml?t='+str(random.random()),timeout=timeout)
            
            temp.append(r.status_code)
            #logger.info(r.text)
                    
            if r.status_code==200:
                
                root = ET.fromstring(r.text)
                xmlParser=Devices.XML_parser.XMLParser(xmlroot=root)
                result,datagram=xmlParser.parseDatagram()
                if result==0:
                    deviceCode=datagram[0]
                    #logger.info('The device responded:' + str(datagram))
                    if int(deviceCode)==DeviceCode:
                        del datagram[0:2]
                        if writeToDB:
                            self.AppDB.check_registersDB()
                            self.AppDB.insert_device_register(TimeStamp=timestamp, DeviceCode=deviceCode, DeviceName=deviceName, DatagramId=DatagramId, 
                                                              year=timestamp.year, values=datagram,NULL=False)
                            DV.LastUpdated=timestamp
                            DV.save(update_fields=["LastUpdated"])
                            RemoteDevices.signals.Device_datagram_reception.send(sender=None, timestamp=timestamp,DeviceName=deviceName,DatagramId=DatagramId,values=datagram)
                            return
                        else:
                            return datagram
                    else:
                        logger.warning('The device responded with a different code. Expecting DeviceCode=' + str(DeviceCode)+' and the code ' 
                              + str(deviceCode) +' was received')
                else:
                    RemoteDevices.signals.Device_datagram_format_error.send(sender=None, DeviceName=deviceName,DatagramId=DatagramId,values=datagram)
            else:
                RemoteDevices.signals.Device_datagram_exception.send(sender=None, DeviceName=deviceName,DatagramId=DatagramId,HTMLCode=r.status_code)
        except:
            
            if str(sys.exc_info()[0]).find('requests.exceptions.ConnectTimeout')>=0:
                RemoteDevices.signals.Device_datagram_timeout.send(sender=None, DeviceIP=self.server,DeviceName=deviceName,DatagramId=DatagramId)
            else:
                logger.error ("Unexpected error in request_datagram:" + str(sys.exc_info()[1]))
        if retries>0:
            retries-=1
            logger.info ('Retrying the Request: '+self.server+'/'+DatagramId)
            self.request_datagram(DeviceCode=DeviceCode,DatagramId=DatagramId,timeout=timeout,writeToDB=writeToDB,retries=retries)
        elif writeToDB:
            self.AppDB.insert_device_register(TimeStamp=timestamp, DeviceCode=DeviceCode, DeviceName=deviceName, DatagramId=DatagramId, 
                                                          year=timestamp.year, values=(None,),NULL=True)


def main():
    HTTPrequest=HTTP_requests(server='http://127.0.0.1')
    HTTPrequest.request_datagram(DeviceCode=1, DatagramId='powers')
            
if __name__ == '__main__':
    main()
                        
    