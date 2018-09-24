from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import json
import urllib
import pandas as pd
import numpy as np
import datetime
import pickle

import time
import os
from EventsAPP.consumers import PublishEvent

import logging
logger = logging.getLogger("project")

import Adafruit_DHT
import math

import environ
env = environ.Env()

from .constants import ENVIRON_FILE

if os.path.exists(ENVIRON_FILE):
    environ.Env.read_env(str(ENVIRON_FILE))

OWM_TOKEN = env('OWM_TOKEN')
ESIOS_TOKEN=env('ESIOS_TOKEN')

'''
A class with the name of each of the DeviceTypes defined for local connection need to be created.
The method to be called when polling the device must be called "read_sensor"
'''

from requests import Session
from json import dumps

IBERDROLA_USER = env('IBERDROLA_USER')
IBERDROLA_PASSW=env('IBERDROLA_PASSW')

class ResponseException(Exception):
    pass


class LoginException(Exception):
    pass


class SessionException(Exception):
    pass


class NoResponseException(Exception):
    pass


class SelectContractException(Exception):
    pass
    
class IBERDROLA:
    _MAX_RETRIES=3
    __loginurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/loginNew/login"
    __miconsumourl="https://www.iberdroladistribucionelectrica.com/consumidores/rest/consumoNew/obtenerDatosConsumo/fechaInicio/dateini/colectivo/USU/frecuencia/horas/acumular/false"
    __watthourmeterurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/escenarioNew/obtenerMedicionOnline/12"
    __icpstatusurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/rearmeICP/consultarEstado"
    __contractsurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/cto/listaCtos/"
    __contractdetailurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/detalleCto/detalle/"
    __contractselectionurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/cto/seleccion/"
    __headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0",
        'accept': "application/json; charset=utf-8",
        'content-type': "application/json; charset=utf-8",
        'cache-control': "no-cache"
    }

    def __init__(self,DV):
        """Iber class __init__ method."""
        self.__session = None
        self.sensor=DV
        self.Error=''
        user=IBERDROLA_USER
        password=IBERDROLA_PASSW
        try:
            self.login(user, password)
        except Exception as ex:
            if type(ex) is LoginException:
                self.Error='Login procedure failed'
            elif type(ex) is ResponseException:
                self.Error='Iberdrola server reported a failure in login'
        
    def login(self, user, password):
        """Create session with your credentials.
           Inicia la session con tus credenciales."""
        self.__session = Session()
        logindata = self.__logindata(user, password)
        response = self.__session.request("POST", self.__loginurl, data=logindata, headers=self.__headers)
        if response.status_code != 200:
            self.__session = None
            raise ResponseException
        jsonresponse = response.json()
        if jsonresponse["success"] != "true":
            self.__session = None
            raise LoginException

    def __logindata(self, user, password):
        logindata = [user, password, "", "Windows -", "PC", "Firefox 54.0", "", "0", "0", "0", "", "s"]
        return dumps(logindata)

    def __checksession(self):
        if not self.__session:
            raise SessionException

    def wattmeter(self):
        """Returns your current power consumption.
           Devuelve tu potencia actual."""
        self.__checksession()
        response = self.__session.request("GET", self.__watthourmeterurl, headers=self.__headers)
        if response.status_code != 200:
            raise ResponseException
        if not response.text or response.text=='{}':
            raise NoResponseException
        jsonresponse = response.json()
        return jsonresponse['valMagnitud']

    def icpstatus(self):
        """Returns the status of your ICP.
           Devuelve el estado de tu ICP."""
        self.__checksession()
        response = self.__session.request("POST", self.__icpstatusurl, headers=self.__headers)
        if response.status_code != 200:
            raise ResponseException
        if not response.text or response.text=='{}':
            raise NoResponseException
        jsonresponse = response.json()
        if jsonresponse["icp"] == "trueConectado":
            return True
        else:
            return False
    
    def miconsumodiario(self,date=None):
        '''    OJO, EL CONSUMO DIARIO SE ACTUALIZA SOBRE LAS 12 A.M. CON UN DIA DE RETRASO
        '''
        import datetime
        self.__checksession()
        if date==None:
            date=(datetime.datetime.now()+datetime.timedelta(days=-1)).replace(hour=0,minute=0,second=0,microsecond=0).strftime('%d-%m-%Y%H:%M:%S')
            timestamp=(datetime.datetime.now()+datetime.timedelta(days=-1)).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()
        else:
            timestamp=date.timestamp()
            date=date.replace(hour=0,minute=0,second=0,microsecond=0).strftime('%d-%m-%Y%H:%M:%S')
        response = self.__session.request("GET", self.__miconsumourl.replace('dateini',date), headers=self.__headers)
        
        if response.status_code != 200:
            raise ResponseException
        if not response.text or response.text=='{}':
            raise NoResponseException
        jsonresponse = response.json()
        try:
            datas=jsonresponse["y"]["data"][0]
        except:
            return None
        
        if datas!=[]:
            for i,data in enumerate(datas):
                if data==None:
                    datas[i]={}
                    datas[i]["valor"]=None
                    
                datas[i]["timestamp"]=datetime.datetime.utcfromtimestamp(timestamp)+datetime.timedelta(hours=i)
                
        else:
            datas=None
        return datas
        
    def contracts(self):
        self.__checksession()
        response = self.__session.request("GET", self.__contractsurl, headers=self.__headers)
        if response.status_code != 200:
            raise ResponseException
        if not response.text:
            raise NoResponseException
        jsonresponse = response.json()
        if jsonresponse["success"]:
            return jsonresponse["contratos"]

    def contract(self):
        self.__checksession()
        response = self.__session.request("GET", self.__contractdetailurl, headers=self.__headers)
        if response.status_code != 200:
            raise ResponseException
        if not response.text:
            raise NoResponseException
        return response.json()

    def contractselect(self, id):
        self.__checksession()
        response = self.__session.request("GET", self.__contractselectionurl + id, headers=self.__headers)
        if response.status_code != 200:
            raise ResponseException
        if not response.text:
            raise NoResponseException
        jsonresponse = response.json()
        if not jsonresponse["success"]:
            raise SelectContractException
    
    def initializeDB(self,fromdate,datagramId = 'dailyconsumption'):
        i=0
        while fromdate+datetime.timedelta(days=i)<datetime.datetime.now():
            date=fromdate+datetime.timedelta(days=i)
            self.__call__(date=date,datagramId = datagramId)
            i=i+1
            PublishEvent(Severity=0,Text='Initializing DB for '+str(self.sensor)+'. Obtained data for ' + str(date),
                         Code=self.sensor.getEventsCode()+'init',Persistent=True)
    
    def execute(self,order,params={}):
        if order=='initializeDB':
            code=self.sensor.getEventsCode()+'init'
            if not "fromdate" in params:
                text=_("Failed to execute order ")+order+_(" on device ")+str(self.sensor)+_(". The parameters passed ")+str(params) + _(" are not adequate.")
                return (100,"Wrong or not enough parameters passed")
            else:
                try:
                    fromdate=datetime.datetime(params['fromdate'])
                except:
                    return (100,"Wrong parameters passed. " + params['fromdate'] + " should be a datetime conversible string.")
                self.initializeDB(fromdate=fromdate,datagramId = 'dailyconsumption')
                return (200,None)
        
        PublishEvent(Severity=0,Text=text,
                         Code=code,Persistent=True)
    
    def __call__(self,date=None,datagramId = 'dailyconsumption'):
        Error=''
        null=False
        if datagramId =='dailyconsumption':
            retries=self._MAX_RETRIES
        elif datagramId=='instantpower':
            retries=1
            
        while retries>0:
            try:
                if datagramId =='dailyconsumption':
                    datas = self.miconsumodiario(date=date)
                    if datas!=None:
                        for data in datas:
                            timestamp=data['timestamp']
                            self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=[data['valor'],],NULL=null)
                            Error=''
                    else:
                        null=True
                        Error='Empty dataframe'
                elif datagramId=='instantpower':
                    data = self.wattmeter()
                    if data!=None:
                        timestamp=timezone.now().replace(second=0)
                        self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=[data,],NULL=null)
                        Error=''
                    else:
                        null=True
                        Error='Empty dataframe'
                if Error!='':
                    Error=Error+' - retrying'
                    retries=retries-1
                else:
                    retries=0
            except Exception as ex:
                retries=retries-1
                if type(ex) is NoResponseException:
                    Error='Empty dataframe received for ' + datagramId
                elif type(ex) is ResponseException:
                    Error='Iberdrola server reported a failure on a data request for ' + datagramId
                else:
                    Error='Unknown APIError: ' + str(ex)
                null=True
        
        if null==False:
            LastUpdated=timezone.now()
        else:
            LastUpdated=None

        return {'Error':Error,'LastUpdated':LastUpdated}
    
class ESIOS(object):
    _MAX_RETRIES=3
    
    def __init__(self,DV):
        """
        Class constructor
        """
        self.sensor=DV
        # The token is unique: You should ask for yours to: Consultas Sios <consultasios@ree.es>
        
        self.token = ESIOS_TOKEN
        
        if self.token is None:
            logger.error('The token is unique: You should ask for yours to: Consultas Sios <consultasios@ree.es>')
            
        self.allowed_geo_id = [3, 8741]  # Espania y Peninsula
        
        # standard format of a date for a query        
        self.dateformat = '%Y-%m-%dT%H:%M:%S'
        
        # dictionary of available series
        
        self.__offer_indicators_list = list()
        self.__analysis_indicators_list = list()
        self.__indicators_name__ = dict()
        self.available_series = dict()
        self.available_series = self.get_indicators()

    def __get_headers__(self):
        """
        Prepares the CURL headers
        :return:
        """
        # Prepare the arguments of the call
        headers = dict()
        headers['Accept'] = 'application/json; application/vnd.esios-api-v1+json'
        headers['Content-Type'] = 'application/json'
        headers['Host'] = 'api.esios.ree.es'
        headers['Authorization'] = 'Token token=\"' + self.token + '\"'
        headers['Cookie'] = ''
        return headers
        
    def get_indicators(self):
        """
        Get the indicators and their name.
        The indicators are the indices assigned to the available data series
        :return:
        """
        fname = 'indicators.pickle'
        import os
        if os.path.exists(fname):
            # read the existing indicators file
            with open(fname, "rb") as input_file:
                all_indicators, self.__indicators_name__, self.__offer_indicators_list, self.__analysis_indicators_list = pickle.load(input_file)
        else:
            # create the indicators file querying the info to ESIOS
            """
            curl "https://api.esios.ree.es/offer_indicators" -X GET
            -H "Accept: application/json; application/vnd.esios-api-v1+json"
            -H "Content-Type: application/json"
            -H "Host: api.esios.ree.es"
            -H "Authorization: Token token=\"5c7f9ca844f598ab7b86bffcad08803f78e9fc5bf3036eef33b5888877a04e38\""
            -H "Cookie: "
            """
            all_indicators = dict()
            self.__indicators_name__ = dict()

            # This is how the URL is built
            url = 'https://api.esios.ree.es/offer_indicators'

            # Perform the call
            req = urllib.request.Request(url, headers=self.__get_headers__())
            with urllib.request.urlopen(req) as response:
                try:
                    json_data = response.read().decode('utf-8')
                except:
                    json_data = response.readall().decode('utf-8')

                result = json.loads(json_data)

            # fill the dictionary
            indicators = dict()
            self.__offer_indicators_list = list()
            for entry in result['indicators']:
                name = entry['name']
                id_ = entry['id']
                indicators[name] = id_
                self.__indicators_name__[id_] = name
                self.__offer_indicators_list.append([name, id_])

            all_indicators[u'indicadores de curvas de oferta'] = indicators

            """
            curl "https://api.esios.ree.es/indicators" -X GET
            -H "Accept: application/json; application/vnd.esios-api-v1+json"
            -H "Content-Type: application/json" -H "Host: api.esios.ree.es"
            -H "Authorization: Token token=\"5c7f9ca844f598ab7b86bffcad08803f78e9fc5bf3036eef33b5888877a04e38\""
            -H "Cookie: "
            """
            url = 'https://api.esios.ree.es/indicators'

            req = urllib.request.Request(url, headers=self.__get_headers__())
            with urllib.request.urlopen(req) as response:
                try:
                    json_data = response.read().decode('utf-8')
                except:
                    json_data = response.readall().decode('utf-8')
                result = json.loads(json_data)

            # continue filling the dictionary
            indicators = dict()
            self.__analysis_indicators_list = list()
            for entry in result['indicators']:
                name = entry['name']
                id_ = entry['id']
                indicators[name] = id_
                self.__indicators_name__[id_] = name
                self.__analysis_indicators_list.append([name, id_])

            all_indicators[u'indicadores de analisis '] = indicators

            # save the indictators
            with open(fname, "wb") as output_file:
                dta = [all_indicators, self.__indicators_name__, self.__offer_indicators_list, self.__analysis_indicators_list]
                pickle.dump(dta, output_file)
        
        return all_indicators
        
    def get_names(self, indicators_list):
        """
        Get a list of names of the given indicator indices
        :param indicators_list:
        :return:
        """
        names = list()
        for i in indicators_list:
            names.append(self.__indicators_name__[i])
        
        return np.array(names, dtype=np.object)
        
    def save_indicators_table(self, fname='indicadores.xlsx'):
        """
        Saves the list of indicators in an excel file for easy consultation
        :param fname:
        :return:
        """
        data = self.__offer_indicators_list + self.__analysis_indicators_list
        
        df = pd.DataFrame(data=data, columns=['Nombre', 'Indicador'])
        
        df.to_excel(fname)

    def __get_query_json__(self, indicator, start, end):
        """
        Get a JSON series
        :param indicator: series indicator
        :param start: Start date
        :param end: End date
        :return:
        """
        # This is how the URL is built

        #  https://www.esios.ree.es/es/analisis/1293?vis=2&start_date=21-06-2016T00%3A00&end_date=21-06-2016T23%3A50&compare_start_date=20-06-2016T00%3A00&groupby=minutes10&compare_indicators=545,544#JSON
        url = 'https://api.esios.ree.es/indicators/' + indicator + '?start_date=' + start + '&end_date=' + end

        # Perform the call
        req = urllib.request.Request(url, headers=self.__get_headers__())
        with urllib.request.urlopen(req) as response:
            try:
                json_data = response.read().decode('utf-8')
            except:
                json_data = response.readall().decode('utf-8')
            result = json.loads(json_data)
            
        return result

    def get_data(self, indicator, start, end):
        """

        :param indicator: Series indicator
        :param start: Start date
        :param end: End date
        :return:
        """
        # check types: Pass to string for the url
        if type(start) is datetime.datetime:
            start = start.strftime(self.dateformat)
        
        if type(end) is datetime.datetime:
            end = end.strftime(self.dateformat)
        
        if type(indicator) is int:
            indicator = str(indicator)
            
        # get the JSON data
        result = self.__get_query_json__(indicator, start, end)

        # transform the data
        d = result['indicator']['values']  # dictionary of values
        
        if len(d) > 0:
            hdr = list(d[0].keys())  # headers    
            data = np.empty((len(d), len(hdr)), dtype=np.object)
            
            for i in range(len(d)):  # iterate the data entries
                for j in range(len(hdr)):  # iterate the headers
                    h = hdr[j]
                    val = d[i][h]
                    data[i, j] = val
                    
            df = pd.DataFrame(data=data, columns=hdr)  # make the DataFrame
            
            df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])  # convert to datetime
            
            df = df.set_index('datetime_utc')  # Set the index column
            
            del df.index.name  # to avoid the index name bullshit
            
            return df
        else:
            return None
    
    def get_multiple_series(self, indicators, start, end):
        """
        Get multiple series data
        :param indicators: List of indicators
        :param start: Start date
        :param end: End date
        :return:
        """
        df = None
        df_list = list()
        names = list()
        for i in range(len(indicators)):

            name = self.__indicators_name__[indicators[i]]
            names.append(name)
            print('Parsing ' + name)
            if i == 0:
                # Assign the first indicator
                df = self.get_data(indicators[i], start, end)
                if df is not None:
                    df = df[df['geo_id'].isin(self.allowed_geo_id)]  # select by geography
                    df.rename(columns={'value': name}, inplace=True)
                df_list.append(df)
            else:
                # merge the newer indicators
                df_new = self.get_data(indicators[i], start, end)
                if df_new is not None:
                    df_new = df_new[df_new['geo_id'].isin(self.allowed_geo_id)]  # select by geography
                    df_new.rename(columns={'value': name}, inplace=True)
                    df = df.join(df_new[name])
                df_list.append(df_new)
        
        return df, df_list, names

    def initializeDB(self,fromdate,datagramId = 'energy_cost'):
        self.__call__(date=fromdate,datagramId = datagramId)
        print('Obtained data from ' + str(fromdate) + ' to tomorrow')
            
    def __call__(self,datagramId = 'energy_cost',date=None):
        Error=''
        if datagramId =='energy_cost':
            # gets the hourly cost for the energy for the next day
            retries=self._MAX_RETRIES
            indicators_ = [10229, 10230, 10231]
            names = self.get_names(indicators_)
            if date==None:
                start_=timezone.now().replace(hour=23,minute=59,second=59)
                end_=(start_+datetime.timedelta(days=1)).replace(hour=23,minute=59,second=59)
            else:
                start_=date.replace(hour=23,minute=59,second=59)
                end_=(timezone.now()+datetime.timedelta(days=1)).replace(hour=23,minute=59,second=59)
            
            while retries>0:
                try:
                    dfmul, df_list, names = self.get_multiple_series(indicators_, start_, end_)
                    if dfmul is not None:
                        null=False
                        Error=''
                        df = dfmul[names]/1000
                        for timestamp,values in zip(df.index,df.values):
                            values=list(values)
                            timestamp=timestamp.to_pydatetime()
                            self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=values,NULL=null)
                    else:
                        null=True
                        Error='Empty dataframe'
                    
                    if Error!='':
                        Error=Error+' - retrying'
                        retries=retries-1
                    else:
                        retries=0
                except:
                    retries=retries-1
                    Error='APIError'
                    null=True
        
        if null==False:
            LastUpdated=timezone.now()
        else:
            LastUpdated=None
            timestamp=timezone.now()
            values=(None,None,None)
            self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=values,NULL=null)
        
        return {'Error':Error,'LastUpdated':LastUpdated}
        

class OpenWeatherMap(object):

    _MAX_RETRIES=3
            
    def __init__(self,DV):
        import pyowm
        self._owm = pyowm.OWM(OWM_TOKEN)  # You MUST provide a valid API key
        self.sensor=DV
        try:
            self.place=DV.device2beacon
        except:
            self.place=None
    
    def query_sensor(self,**kwargs):
        pass
        
    def __call__(self,datagramId = 'observation'):
        #logger.error('Callback for the device ' + self.sensor.Name)
        if self.place!=None:
            
            # try:
                # datagram = kwargs['datagram']
            # except:
                # datagram = 'observation'
            #logger.error('Datagram: ' + datagram)
            Error=''
            #datagramId='forecast'
            if datagramId =='observation':
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
                        if Error!='':
                            Error=Error+' - retried OK'
                    except:
                        retries=retries-1
                        Error='APIError'
                        values=(None,None,None,None,None)
                        null=True
            elif datagramId =='forecast':
                fc = self._owm.three_hours_forecast_at_coords(lat=self.place.Latitude, lon=self.place.Longitude)
                f = fc.get_forecast()
                print('Forecasts for the next 12 H')
                for i,w in enumerate(f):
                    timestamp=w.get_reference_time(timeformat='date')
                    clouds=w.get_clouds()                       # Returns the cloud coverage percentage as an int
                    temperature=w.get_temperature('celsius')['temp']
                    wind=w.get_wind()
                    if 'speed' in wind:
                        windspeed=wind['speed']                           # {'speed': 4.6, 'deg': 330}
                    else:
                        windspeed=None
                    rain=w.get_rain()                           # {'3h': 0} 
                    if '3h' in rain:
                        rain=rain['3h']
                    else:
                        rain=0
                    values=(temperature,windspeed,rain,clouds)
                    self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=values,NULL=False)
                    print(w.get_reference_time('date'),w.get_status())
            
            if null==False:
                LastUpdated=timezone.now()
            else:
                LastUpdated=None
                timestamp=timezone.now()
            self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=values,NULL=null)
            return {'Error':Error,'LastUpdated':LastUpdated}
        else:
            PublishEvent(Severity=5,Text=str(_('The device ')) + self.sensor.Name + str(_(' does not have any Beacon associated.')),
                         Code=self.sensor.getEventsCode()+'100',Persistent=True)
            Error=str(_('The device ')) + self.sensor.Name + str(_(' does not have any Beacon associated.'))
            return {'Error':Error,'LastUpdated':None}
        
class DHT11(object):
    """
    Tools for working with DHT temperature/humidity sensor.
    """
    _maxT=60
    _minT=-20
    _maxH=100
    _minH=0
    _lastTemp=None
    
    def __init__(self,DV):
        self.type = Adafruit_DHT.DHT11
        self.sensor=DV
        self._maxDT=0.2*self.sensor.Sampletime/60 # maximum delta T allowed 0.2degC per minute

    def initial_calibration(self):
        ''' THIS CODE TRIES TO INITIALIZE THE VARIABLE self._lastTemp WITH A GOOD VALUE OF TEMPERATURE
        '''
        logger.info('Calibrating sensor ' + str(self.sensor.Name))
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
            logger.info('Finished calibrating sensor ' + str(self.sensor.Name) + ' with temperature= ' + str(self._lastTemp) + ' obtained with '+ str(samplesT) + ' valid samples')
        else:
            self._lastTemp=None
            logger.error('Calibration of sensor ' + str(self.sensor.Name) + ' failed')
            
    def __call__(self,datagramId='data'):
        """
        Read temperature and humidity from DHT sensor.
        """
        
        timestamp=timezone.now() #para hora con info UTC 
        humidity=0
        temperature=0
        for x in range(0, 3):
            h, t = Adafruit_DHT.read_retry(self.type, self.sensor.IO.pin)
            if self._lastTemp!=None and abs(self._lastTemp-t)>self._maxDT:
                logger.warning('Measure from ' + str(self.sensor.Name) + ' exceded maxDT!! Last Temperature: ' + str(self._lastTemp) + ' and current is : '+ str(t))
                t=self._lastTemp
                
            if (t < self._maxT and t > self._minT):
                temperature=temperature+t
            else:
                logger.warning('Measure from ' + str(self.sensor.Name) + ' out of bounds!! Temperature: ' + str(t))
            if (h < self._maxH and h > self._minH):
                humidity=humidity+h
            else:
                logger.warning('Measure from ' + str(self.sensor.Name) + ' out of bounds!! Humidity: '+ str(h))
                
            time.sleep(5)   # waiting 2 sec between measurements to release DHT sensor
            
        temperature=temperature/3
        humidity=humidity/3
        dewpoint=(humidity/100)**(1/8)*(112+0.9*temperature)+0.1*temperature-112
        
        self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=(temperature,humidity,dewpoint),NULL=False)
        
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
    
    def __init__(self,DV):
        self.type = Adafruit_DHT.DHT22
        self.sensor=DV
        self._maxDT=0.2*self.sensor.Sampletime/60 # maximum delta T allowed 0.2degC per minute
    
    @staticmethod
    def convertCtoF(c):
      return c*1.8+32
    
    @staticmethod
    def convertFtoC(f):
      return (f-32)*0.55555

    @classmethod
    def computeHeatIndex(cls,temperature, percentHumidity):
    # Using both Rothfusz and Steadman's equations
    # http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml

        temperature = cls.convertCtoF(temperature);

        hi = 0.5 * (temperature + 61.0 + ((temperature - 68.0) * 1.2) + (percentHumidity * 0.094));

        if (hi > 79):
            hi = (-42.379 +2.04901523 * temperature +10.14333127 * percentHumidity -0.22475541 * temperature*percentHumidity -0.00683783 * temperature**2 + 
                -0.05481717 * percentHumidity**2 +0.00122874 * temperature**2 * percentHumidity +0.00085282 * temperature*percentHumidity**2 + 
                -0.00000199 * temperature**2 * percentHumidity**2)

        if((percentHumidity < 13) and (temperature >= 80.0) and (temperature <= 112.0)):
            hi -= ((13.0 - percentHumidity) * 0.25) * math.sqrt((17.0 - math.fabs(temperature - 95.0)) * 0.05882);
        elif((percentHumidity > 85.0) and (temperature >= 80.0) and (temperature <= 87.0)):
            hi += ((percentHumidity - 85.0) * 0.1) * ((87.0 - temperature) * 0.2);
            
        return cls.convertFtoC(hi)
    
    def initial_calibration(self):
        ''' THIS CODE TRIES TO INITIALIZE THE VARIABLE self._lastTemp WITH A GOOD VALUE OF TEMPERATURE
        '''
        logger.info('Calibrating sensor ' + str(self.sensor.Name))
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
                
            PublishEvent(Severity=0,Text='Sample ' + str(x+1) + ' yielded ' + str(t) + 'degC and ' + str(h) + '%',
                         Code=self.sensor.getEventsCode()+'100',Persistent=False)
            
            if (t < self._maxT and t > self._minT) and (h < self._maxH and h > self._minH):
                temperature=temperature+t
                samplesT+=1
            else:
                x=x-1
            
            x=x+1
            time.sleep(2)   # waiting 2 sec between measurements to release DHT sensor
            
        if samplesT>0:
            self._lastTemp=round(temperature/samplesT,3)
            logger.info('Finished calibrating sensor ' + str(self.sensor.Name) + ' with temperature= ' + str(self._lastTemp) + ' obtained with '+ str(samplesT) + ' valid samples')
        else:
            self._lastTemp=None
            logger.error('Calibration of sensor ' + str(self.sensor.Name) + ' failed')
        
                                
    def __call__(self,datagramId = 'data'):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        humidity=0
        temperature=0
        retries=0
        x=0
        Error=''
        while (x < self._numberMeasures):
            h, t = Adafruit_DHT.read_retry(self.type, self.sensor.IO.Pin)
            if t==None:
                t=self._maxT
            if h==None:
                h=self._maxH
            
            if self._lastTemp!=None: 
                if abs(self._lastTemp-t)>self._maxDT:
                    logger.warning('Measure from ' + str(self.sensor.Name) + ' exceded maxDT!! Last Temperature: ' + str(self._lastTemp) + ' and current is : '+ str(t))
                    Error+=' - maxDT'
                    t = self._maxT
                
            if (t < self._maxT and t > self._minT):
                temperature=temperature+t
            else:
                logger.warning('Measure from ' + str(self.sensor.Name) + ' out of bounds!! Temperature: ' + str(t))
                Error+=' - maxminT'
                
            if (h < self._maxH and h > self._minH):
                humidity=humidity+h
            else:
                logger.warning('Measure from ' + str(self.sensor.Name) + ' out of bounds!! Humidity: '+ str(h))
                Error+=' - maxminH'
            
            if (t < self._maxT and t > self._minT) and (h < self._maxH and h > self._minH):
                break
            else:
                retries+=1
                x=-1
                
            if retries>=self._MAX_RETRIES:
                logger.error('Maximum number of retries reached!!!')
                Error+=' - maxRetries'
                break
            x=x+1
            
            if (x < self._numberMeasures):
                time.sleep(2)   # waiting 2 sec between measurements to release DHT sensor
        
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
        
        self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=(temperature,humidity,dewpoint,hi),NULL=False)
        
        reading={
            'timestamp':timestamp,
            'temperature':temperature,
            'humidity':humidity,
            'heat index':hi,
        }
        if null==False:
            LastUpdated=timestamp
        else:
            LastUpdated=None
        
        self._lastTemp=temperature
        return {'Error':Error,'LastUpdated':LastUpdated}

                
        
    def query_sensor(self,**kwargs):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        humidity, temperature = Adafruit_DHT.read_retry(self.type, self.sensor.IO.Pin)
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
