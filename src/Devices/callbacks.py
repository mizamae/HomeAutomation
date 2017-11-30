import RPi.GPIO as GPIO
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import Devices.BBDD
import Devices.GlobalVars
#from Devices.signals import Device_datagram_reception,Device_datagram_exception
import time
import os
from Events.consumers import PublishEvent

import logging
logger = logging.getLogger("project")

import Adafruit_DHT
'''
A class with the name of each of the DeviceTypes defined for local connection need to be created.
The method to be called when polling the device must be called "read_sensor"
'''
class OpenWeatherMap(object):

    _MAX_RETRIES=3
            
    def __init__(self,DV):
        import pyowm
        self._owm = pyowm.OWM('a85b0fd83aa7cf883f15ed7fc0bab4d9')  # You MUST provide a valid API key
        self.sensor=DV
        try:
            self.place=DV.device2beacon
        except:
            self.place=None
    
    def query_sensor(self,**kwargs):
        pass
        
    def read_sensor(self,**kwargs):
        #logger.error('Callback for the device ' + self.sensor.DeviceName)
        if self.place!=None:
            
            datagram=kwargs['datagram']
            #logger.error('Datagram: ' + datagram)
            error=''
            if datagram=='observation':
                retries=self._MAX_RETRIES
                while retries>0:
                    try:
                        observation = self._owm.weather_at_coords(lat=self.place.Latitude, lon=self.place.Longitude)
                        w = observation.get_weather()
                        timestamp=w.get_reference_time(timeformat='date')
                        dewpoint=w.get_dewpoint()                   # Returns the dew point as a float
                        clouds=w.get_clouds()                       # Returns the cloud coverage percentage as an int
                        wind=w.get_wind()
                        if 'speed' in wind:
                            windspeed=wind['speed']                           # {'speed': 4.6, 'deg': 330}
                        else:
                            windspeed=None
                        if 'deg' in wind:
                            windorigin=wind['deg']                           # {'speed': 4.6, 'deg': 330}
                        else:
                            windorigin=None
                        humidity=w.get_humidity()                   # 87
                        temperature=w.get_temperature('celsius')['temp']    # {'temp_max': 10.5, 'temp': 9.7, 'temp_min': 9.0}
                        rain=w.get_rain()                           # {'3h': 0} 
                        if '3h' in rain:
                            rain=rain['3h']
                        else:
                            rain=0
                        clouds=w.get_clouds()
                        values=(temperature,humidity,windspeed,rain,clouds)
                        retries=0
                        null=False
                        if error!='':
                            error=error+' - retried OK'
                    except:
                        retries=retries-1
                        error='APIError'
                        values=(None,None,None,None,None)
                        null=True
                
            elif datagram=='forecast':
                forecast = self._owm.three_hours_forecast_at_coords(lat=self.place.Latitude, lon=self.place.Longitude)
                fcs = forecast.get_forecast()
                print('Forecasts for the next 12 H')
                for i,fc in enumerate(fcs):
                    print(fc.get_reference_time('date'),fc.get_status())
                timestamp=timezone.now() #para hora con info UTC 
                values=(None,)
            
            #logger.error('Values: ' + str(values))
            registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                       configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
            try:
                registerDB.insert_device_register(TimeStamp=timestamp,DeviceCode=None,DeviceName=self.sensor.DeviceName,DatagramId=datagram,year='',values=values,NULL=null)
            except:
                error='DB Error'
            if null==False:
                self.sensor.LastUpdated=timezone.now()
                PublishEvent(Severity=0,Text=self.sensor.DeviceName+str(_(' updated OK')),Persistent=True)
            self.sensor.Error=error
            if error!='':
                PublishEvent(Severity=3,Text=self.sensor.DeviceName+' '+error,Persistent=True)
            self.sensor.save()
        else:
            PublishEvent(Severity=5,Text=str(_('The device ')) + self.sensor.DeviceName + str(_(' does not have any Beacon associated.')),Persistent=True)
        
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
        self._maxDT=0.2*self.sensor.Sampletime/60 # maximum delta T allowed 0.2�C per minute

    def initial_calibration(self):
        ''' THIS CODE TRIES TO INITIALIZE THE VARIABLE self._lastTemp WITH A GOOD VALUE OF TEMPERATURE
        '''
        logger.info('Calibrating sensor ' + str(self.sensor.DeviceName))
        humidity=0
        temperature=0
        samplesT=0
        x=0
        retries=0
        while (x < 1):
            
            h, t = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
            if t==None:
                t=self._maxT
            if h==None:
                h=self._maxH
                
            logger.info('Sample ' + str(x+1) + ' yielded ' + str(t) + 'degC and ' + str(h) + '%')
            if (t < self._maxT and t > self._minT) and (h < self._maxH and h > self._minH):
                temperature=temperature+t
                samplesT+=1
            else:
                x=x-1
            
            x=x+1
            time.sleep(5)   # waiting 2 sec between measurements to release DHT sensor
            
        if samplesT>0:
            self._lastTemp=round(temperature/samplesT,3)
            logger.info('Finished calibrating sensor ' + str(self.sensor.DeviceName) + ' with temperature= ' + str(self._lastTemp) + ' obtained with '+ str(samplesT) + ' valid samples')
        else:
            self._lastTemp=None
            logger.error('Calibration of sensor ' + str(self.sensor.DeviceName) + ' failed')
            
    def read_sensor(self,**kwargs):
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
        #Device_datagram_reception.send(sender=None, Device=self.sensor,values=reading)
        self._lastTemp=temperature
        
    def query_sensor(self,**kwargs):
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
    _numberMeasures=1
    _MAX_RETRIES=3
    _CalnumberMeasures=10
    
    def __init__(self,DHTsensor):
        self.type = Adafruit_DHT.DHT22
        self.sensor=DHTsensor
        self._maxDT=0.2*self.sensor.Sampletime/60 # maximum delta T allowed 0.2�C per minute
    
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
    
    def initial_calibration(self):
        ''' THIS CODE TRIES TO INITIALIZE THE VARIABLE self._lastTemp WITH A GOOD VALUE OF TEMPERATURE
        '''
        logger.info('Calibrating sensor ' + str(self.sensor.DeviceName))
        humidity=0
        temperature=0
        samplesT=0
        x=0
        retries=0
        while (x < 1):
            
            h, t = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
            if t==None:
                t=self._maxT
            if h==None:
                h=self._maxH
                
            PublishEvent(Severity=0,Text='Sample ' + str(x+1) + ' yielded ' + str(t) + 'degC and ' + str(h) + '%',Persistent=False)
            
            if (t < self._maxT and t > self._minT) and (h < self._maxH and h > self._minH):
                temperature=temperature+t
                samplesT+=1
            else:
                x=x-1
            
            x=x+1
            time.sleep(5)   # waiting 2 sec between measurements to release DHT sensor
            
        if samplesT>0:
            self._lastTemp=round(temperature/samplesT,3)
            logger.info('Finished calibrating sensor ' + str(self.sensor.DeviceName) + ' with temperature= ' + str(self._lastTemp) + ' obtained with '+ str(samplesT) + ' valid samples')
        else:
            self._lastTemp=None
            logger.error('Calibration of sensor ' + str(self.sensor.DeviceName) + ' failed')
        
                                
    def read_sensor(self,**kwargs):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        humidity=0
        temperature=0
        retries=0
        x=0
        error=''
        while (x < self._numberMeasures):
            h, t = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
            if t==None:
                t=self._maxT
            if h==None:
                h=self._maxH
            
            if self._lastTemp!=None: 
                if abs(self._lastTemp-t)>self._maxDT:
                    logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' exceded maxDT!! Last Temperature: ' + str(self._lastTemp) + ' and current is : '+ str(t))
                    error+=' - maxDT'
                    t = self._maxT
                
            if (t < self._maxT and t > self._minT):
                temperature=temperature+t
            else:
                logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' out of bounds!! Temperature: ' + str(t))
                error+=' - maxminT'
                
            if (h < self._maxH and h > self._minH):
                humidity=humidity+h
            else:
                logger.warning('Measure from ' + str(self.sensor.DeviceName) + ' out of bounds!! Humidity: '+ str(h))
                error+=' - maxminH'
            
            if (t < self._maxT and t > self._minT) and (h < self._maxH and h > self._minH):
                break
            else:
                retries+=1
                x=-1
                
            if retries>=self._MAX_RETRIES:
                logger.error('Maximum number of retries reached!!!')
                error+=' - maxRetries'
                break
            x=x+1
            time.sleep(5)   # waiting 2 sec between measurements to release DHT sensor
        
        if retries>=self._MAX_RETRIES:
            if temperature>0:
                temperature=round(temperature/self._numberMeasures,3)
            else:
                temperature=None
            if humidity>0:
                humidity=round(humidity/self._numberMeasures,3)
            else:
                humidity=None
            dewpoint=None
            hi=None
            null=True
        else:
            temperature=round(temperature/self._numberMeasures,3)
            humidity=round(humidity/self._numberMeasures,3)
            dewpoint=round((humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112,3)
            hi=round(self.computeHeatIndex(temperature=temperature, percentHumidity=humidity),3)
            null=False
            
        registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                   configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')

        registerDB.insert_device_register(TimeStamp=timestamp,DeviceCode=None,DeviceName=self.sensor.DeviceName,DatagramId='data',year='',values=(temperature,humidity,dewpoint,hi),NULL=null)
        
        reading={
            'timestamp':timestamp,
            'temperature':temperature,
            'humidity':humidity,
            'heat index':hi,
        }
        self.sensor.LastUpdated=timestamp
        if error!='':
            PublishEvent(Severity=3,Text=self.sensor.DeviceName+' '+error,Persistent=True)
        self.sensor.Error=error
        self.sensor.save()
        self._lastTemp=temperature
        
    def query_sensor(self,**kwargs):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        humidity, temperature = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
        if temperature==None:
            temperature=self._maxT
        if humidity==None:
            humidity=self._maxH
        if (temperature < self._maxT and temperature > self._minT) and (humidity < self._maxH and humidity > self._minH):
            dewpoint=(humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112
            hi=self.computeHeatIndex(temperature=temperature, percentHumidity=humidity)
        else:
            dewpoint=0
        return (round(humidity,3), round(temperature,3), round(dewpoint,3))