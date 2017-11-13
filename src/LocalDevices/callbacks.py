import RPi.GPIO as GPIO
from django.utils import timezone
import Devices.BBDD
from LocalDevices.signals import Devices_datagram_reception,Devices_datagram_exception
import time
import os

import logging
logger = logging.getLogger("project")

import Adafruit_DHT
'''
A class with the name of each of the DeviceTypes defined for local connection need to be created.
The method to be called when polling the device must be called "read_sensor"
'''
class DHT11(object):
    """
    Tools for working with DHT temperature/humidity sensor.
    """
    _maxT=60
    _minT=-20
    _maxH=100
    _minH=0
    _lastTemp=None
    
    def __init__(self,DHTsensor):
        self.type = Adafruit_DHT.DHT11
        self.sensor=DHTsensor
        self._maxDT=0.2*self.sensor.Sampletime/60 # maximum delta T allowed 0.2ºC per minute

    def read_sensor(self):
        """
        Read temperature and humidity from DHT sensor.
        """
        
        timestamp=timezone.now() #para hora con info UTC 
        humidity=0
        temperature=0
        for x in range(0, 3):
            h, t = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
            if self._lastTemp!=None and abs(self._lastTemp-t)>self._maxDT:
                logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' exceded maxDT!! Last Temperature: ' + str(self._lastTemp) + ' and current is : '+ str(t))
                t=self._lastTemp
                
            if (t < self._maxT and t > self._minT):
                temperature=temperature+t
            else:
                logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' out of bounds!! Temperature: ' + str(t))
            if (h < self._maxH and h > self._minH):
                humidity=humidity+h
            else:
                logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' out of bounds!! Humidity: '+ str(h))
                
            time.sleep(5)   # waiting 2 sec between measurements to release DHT sensor
            
        temperature=temperature/3
        humidity=humidity/3
        dewpoint=(humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112
        
        registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                   configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')

        registerDB.insert_device_register(TimeStamp=timestamp,DeviceCode=None,DeviceName=self.sensor.DeviceName,DatagramId='data',year='',values=(temperature,humidity,dewpoint))
        
        reading={
            'timestamp':timestamp,
            'temperature':temperature,
            'humidity':humidity,
        }
        Devices_datagram_reception.send(sender=None, Device=self.sensor,values=reading)
        self._lastTemp=temperature
        
    def query_sensor(self):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        humidity, temperature = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
        dewpoint=(humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112
        return (humidity, temperature,dewpoint)
 
class DHT22(object):
    """
    Tools for working with DHT temperature/humidity sensor.
    """
    _maxT=60
    _minT=-20
    _maxH=100
    _minH=0
    _lastTemp=None
    _numberMeasures=3
    
    def __init__(self,DHTsensor):
        self.type = Adafruit_DHT.DHT22
        self.sensor=DHTsensor
        self._maxDT=0.2*self.sensor.Sampletime/60 # maximum delta T allowed 0.2ºC per minute
    
    def convertCtoF(self,c):
      return c*1.8+32

    def convertFtoC(self,f):
      return (f-32)*0.55555

    def computeHeatIndex(self,temperature, percentHumidity):
    # Using both Rothfusz and Steadman's equations
    # http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml

        temperature = self.convertCtoF(temperature);

        hi = 0.5 * (temperature + 61.0 + ((temperature - 68.0) * 1.2) + (percentHumidity * 0.094));

        if (hi > 79):
            hi = (-42.379 +2.04901523 * temperature +10.14333127 * percentHumidity -0.22475541 * temperature*percentHumidity -0.00683783 * temperature**2 + 
                -0.05481717 * percentHumidity**2 +0.00122874 * temperature**2 * percentHumidity +0.00085282 * temperature*percentHumidity**2 + 
                -0.00000199 * temperature**2 * percentHumidity**2)

        if((percentHumidity < 13) and (temperature >= 80.0) and (temperature <= 112.0)):
            hi -= ((13.0 - percentHumidity) * 0.25) * sqrt((17.0 - fabs(temperature - 95.0)) * 0.05882);
        elif((percentHumidity > 85.0) and (temperature >= 80.0) and (temperature <= 87.0)):
            hi += ((percentHumidity - 85.0) * 0.1) * ((87.0 - temperature) * 0.2);
            
        return self.convertFtoC(hi)
  
    def read_sensor(self):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        humidity=0
        temperature=0
        for x in range(0, self._numberMeasures):
            h, t = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
            if t==None:
                t=self._maxT
            if h==None:
                h=self._maxH
            
            if self._lastTemp!=None: 
                if abs(self._lastTemp-t)>self._maxDT:
                    logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' exceded maxDT!! Last Temperature: ' + str(self._lastTemp) + ' and current is : '+ str(t))
                    t=self._lastTemp
                
            if (t < self._maxT and t > self._minT):
                temperature=temperature+t
            else:
                logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' out of bounds!! Temperature: ' + str(t))
                
            if (h < self._maxH and h > self._minH):
                humidity=humidity+h
            else:
                logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' out of bounds!! Humidity: '+ str(h))
                
            time.sleep(5)   # waiting 2 sec between measurements to release DHT sensor
            
        temperature=round(temperature/self._numberMeasures,3)
        humidity=round(humidity/self._numberMeasures,3)
        dewpoint=round((humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112,3)
        hi=round(self.computeHeatIndex(temperature=temperature, percentHumidity=humidity),3)
        registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                   configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')

        registerDB.insert_device_register(TimeStamp=timestamp,DeviceCode=None,DeviceName=self.sensor.DeviceName,DatagramId='data',year='',values=(temperature,humidity,dewpoint,hi))
        
        reading={
            'timestamp':timestamp,
            'temperature':temperature,
            'humidity':humidity,
            'heat index':hi,
        }
        Devices_datagram_reception.send(sender=None, Device=self.sensor,values=reading)
        self._lastTemp=temperature
        
    def query_sensor(self):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        humidity, temperature = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
        if temperature==None:
            temperature=0
        if humidity==None:
            humidity=0
        if (temperature < self._maxT and temperature > self._minT) and (humidity < self._maxH and humidity > self._minH):
            dewpoint=(humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112
            hi=self.computeHeatIndex(temperature=temperature, percentHumidity=humidity)
        else:
            humidity=0
            temperature=0
            dewpoint=0
        return (round(humidity,3), round(temperature,3), round(dewpoint,3))
