from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache

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

class PENDING_DB(object):
    SQLcreateRegisterTable = ''' 
                                CREATE TABLE IF NOT EXISTS pending_jobs (
                                    date DATE,
                                    datagramID TEXT,
                                    dv_pk INTEGER,
                                    UNIQUE (date,datagramID,dv_pk)                    
                                ); '''  # the * will be replaced by the column names and types
    SQLinsertRegister = ''' INSERT INTO pending_jobs(date,dv_pk,datagramID) VALUES(?,?,?) '''
    SQLselectAllRegisters = ''' SELECT * FROM pending_jobs WHERE dv_pk=?'''
    SQLdeleteRegister = ''' DELETE FROM pending_jobs WHERE date=? AND datagramID=?'''
    
    @staticmethod
    def runOnInit():
    # CREATES THE PENDING JOBS DATABASE
        from .constants import POLLING_PENDING_DB
        from utils.BBDD import Database
        DB=Database(location=POLLING_PENDING_DB,DB_id='Init_pending')
        try:
            DB.executeTransactionWithCommit(SQLstatement=PENDING_DB.SQLcreateRegisterTable)
        except Exception as ex:
            Error='Error creating the pending requests DB: ' + str(ex)
            logger.error(Error)
            
    @staticmethod
    def add_pending_job(DV,datagramId,date):
        #logger.info("Adding pending requesto " + str(DV)+" " + str(datagramId)+" " + str(date))
        from .constants import POLLING_PENDING_DB
        from utils.BBDD import Database
        DB=Database(location=POLLING_PENDING_DB,DB_id=str(DV)+'_pending')
        #logger.info("Pending DB instantiated " + str(DB))
        try:
            DB.executeTransactionWithCommit(SQLstatement=PENDING_DB.SQLinsertRegister,arg=[date,DV.pk,datagramId])
            PublishEvent(Severity=3,Text=_("The datagram '" + datagramId + "' for the device " + str(DV) + " at " + str(date)+ " has been added to pending jobs"),
                         Code=str(DV)+'_pending'+str(date),Persistent=True)
        except Exception as ex:
            DV.SetError(error='Error adding a pending request: ' + str(ex))
            logger.error(DV.Error)
            
    @staticmethod
    def __retrieve_pending_jobs(DV):
        from .constants import POLLING_PENDING_DB
        from utils.BBDD import Database
        DB=Database(location=POLLING_PENDING_DB,DB_id=str(DV)+'_pending')
        try:
            reqs=DB.executeTransaction(SQLstatement=PENDING_DB.SQLselectAllRegisters,arg=[DV.pk,])
            logger.info('Pending requests: '+str(reqs))
        except Exception as ex:
            reqs=[]
            DV.SetError(error='Error reading the pending requests: ' + str(ex))
            logger.error(DV.Error)
        return reqs
    
    @staticmethod
    def __delete_pending_job(DV,datagramId,date):
        from .constants import POLLING_PENDING_DB
        from utils.BBDD import Database
        from .models import Devices
        DB=Database(location=POLLING_PENDING_DB,DB_id=str(DV)+'_pending')
        try:
            DV=Devices.objects.get(pk=DV.pk)
            DB.executeTransactionWithCommit(SQLstatement=PENDING_DB.SQLdeleteRegister,arg=[date,datagramId])
            PublishEvent(Severity=0,Text=_("The datagram '" + datagramId + "' for the device " + str(DV) + " at " + str(date)+ " has been removed from pending jobs"),
                         Code=str(DV)+'pending'+str(date),Persistent=True)
        except Exception as ex:
            DV.SetError(error='Error deleting a pending request: ' + str(ex))
            logger.error(DV.Error)
    
    @staticmethod
    def execute_pending_jobs(sender,DV):
        from .models import Devices
        jobs=PENDING_DB.__retrieve_pending_jobs(DV=DV)
        for job in jobs:
            date=job[0]
            datagramId=job[1]
            logger.info('Executing pending requests: '+str(date)+'-'+str(datagramId)+'-'+str(DV.pk))
            instance=sender(DV=DV)
            result=instance(date=date,datagramId = datagramId)
            if result['Error']=='':
                PENDING_DB.__delete_pending_job(DV=DV,datagramId=datagramId,date=date)
                
    
    
IBERDROLA_USER = env('IBERDROLA_USER')
IBERDROLA_PASSW=env('IBERDROLA_PASSW')

    
class IBERDROLA:
    _MAX_RETRIES=3
                           
    __loginurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/loginNew/login"
    __miconsumourl="https://www.iberdroladistribucionelectrica.com/consumidores/rest/consumoNew/obtenerDatosConsumo/fechaInicio/dateini/colectivo/USU/frecuencia/horas/acumular/false"
    __watthourmeterurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/escenarioNew/obtenerMedicionOnline/12"
    __icpstatusurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/rearmeICP/consultarEstado"
    __contractsurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/cto/listaCtos/"
    __contractdetailurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/detalleCto/detalle/"
    __contractselectionurl = "https://www.iberdroladistribucionelectrica.com/consumidores/rest/cto/seleccion/"
    __useragents=["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
                  "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
                  "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
                  "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.21 (KHTML, like Gecko) Mwendo/1.1.5 Safari/537.21",
                  "Mozilla/5.0 (Linux; Android 4.4.2; XMP-6250 Build/HAWK) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Safari/537.36 ADAPI/2.0 (UUID:9e7df0ed-2a5c-4a19-bec7-2cc54800f99d) RK3188-ADAPI/1.2.84.533 (MODEL:XMP-6250)",
                  "Mozilla/5.0 (Linux; Android 6.0.1; CPH1607 Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36",
                  "Mozilla/5.0 (iPad; CPU OS 9_3_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13F69 Safari/601.1",
                  "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
                  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
                  "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0",
                  ]
    __headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0",
        'accept': "application/json; charset=utf-8",
        'content-type': "application/json; charset=utf-8",
        'cache-control': "no-cache"
    }
    
    _session=None
    _disabled=False
    _login_thread=None
    _loggedin=False
    Error=''
    
    class _ResponseException(Exception):
        pass
        
    class _LoginException(Exception):
        pass
    
    class _SessionException(Exception):
        pass
    
    class _NoResponseException(Exception):
        pass
    
    class _EnableException(Exception):
        pass
    
    class _DBException(Exception):
        pass

    def __init__(self,DV):
        self.sensor=DV
        IBERDROLA.Error=''
        IBERDROLA.init_login_thread()
    
    @staticmethod
    def runOnInit(DV):
        IBERDROLA.init_login_thread()
        
        if IBERDROLA._loggedin:
            PENDING_DB.execute_pending_jobs(sender=IBERDROLA,DV=DV)
        
    @staticmethod
    def init_login_thread():
        user=IBERDROLA_USER
        password=IBERDROLA_PASSW
        if not IBERDROLA._disabled:
            try:
                from utils.asynchronous_tasks import BackgroundTimer
                IBERDROLA._login_thread=BackgroundTimer(callable=None,threadName='iberdrola_login',interval=1,callablekwargs={},
                                repeat=True,triggered=False,lifeSpan=8*60*60,onThreadInit=IBERDROLA.login,
                                onInitkwargs={'user':user,'password':password})
                from time import sleep
                i=0
                while IBERDROLA._loggedin==False and i<10:
                    sleep(1)    # to allow to initialize the thread properly
                    i=i+1
                if not IBERDROLA._loggedin:
                    raise IBERDROLA._LoginException
            except Exception as ex:
                logger.error('IBERDROLA: Login failed : ' + str(ex))
                IBERDROLA.kill_login_thread()
                if type(ex) is IBERDROLA._LoginException:
                    IBERDROLA.Error='Login procedure failed'
                elif type(ex) is IBERDROLA._ResponseException:
                    IBERDROLA.Error='Iberdrola server reported a failure in login'
    
    @staticmethod
    def kill_login_thread():
        if IBERDROLA._login_thread!=None:
            IBERDROLA._login_thread.kill()
        IBERDROLA._login_thread=None
        IBERDROLA._session =None
        IBERDROLA._loggedin=False
        IBERDROLA.enable()
        logger.error('IBERDROLA: Killed the thread')
        
    @staticmethod
    def disable(auto_enable=False):
        """ Sets an internal flag that inhibits the queries """
        IBERDROLA._disabled=True
        logger.error('IBERDROLA: Disabled')
        if auto_enable:
            from utils.asynchronous_tasks import BackgroundTimer
            enable_thread=BackgroundTimer(callable=IBERDROLA.enable,threadName='iberdrola_enable',interval=1*60*60,callablekwargs={},
                                repeat=False,triggered=False,lifeSpan=None,onThreadInit=None,onInitkwargs={})
    
    @staticmethod
    def enable():
        """ Resets an internal flag that inhibits the queries """
        IBERDROLA._disabled=False
        
    @staticmethod
    def setUserAgent():
        """ Sets a randomly chosen user-agent to minimize bot trace """
        from random import randint
        agent=randint(0, len(IBERDROLA.__useragents)-1)
        IBERDROLA.__headers['User-Agent']=IBERDROLA.__useragents[agent]
        logger.error('IBERDROLA: User-Agent= ' + str(IBERDROLA.__headers['User-Agent']))
    
    @staticmethod
    def login(user, password):
        """Create session with your credentials.
           Inicia la session con tus credenciales."""
        logger.error('IBERDROLA: Enters login')
        IBERDROLA._session = Session()
        #IBERDROLA.setUserAgent()
        logindata = IBERDROLA.__logindata(user, password)
        try:
            response = IBERDROLA._session.request("POST", IBERDROLA.__loginurl, data=logindata, headers=IBERDROLA.__headers)
        except Exception as ex:
            IBERDROLA.kill_login_thread()
            IBERDROLA.Error='Error in log in request: ' + str(ex)
            logger.error('IBERDROLA: Login error: ' + IBERDROLA.Error)
            return
            
        if response.status_code != 200:
            logger.error('IBERDROLA: Login failure, status code!=200. Code ' + str(response.status_code))
            raise IBERDROLA._ResponseException
        jsonresponse = response.json()
        if not "success" in jsonresponse or "captcha" in jsonresponse: # captcha is raised!!
            logger.error('IBERDROLA: Login failure, jsonresponse error. JSON: ' + str(jsonresponse))
            IBERDROLA.kill_login_thread()
            IBERDROLA.disable(auto_enable=True)
            raise IBERDROLA._LoginException
        if jsonresponse["success"] != "true":
            logger.error('IBERDROLA: Login failure, not success')
            IBERDROLA.kill_login_thread()
            raise IBERDROLA._LoginException
        IBERDROLA._loggedin=True
        logger.info('Logged in to Iberdrola')

    @staticmethod
    def __logindata(user, password):
        logindata = [user, password, "", "Windows -", "PC", "Firefox 54.0", "", "0", "0", "0", "", "s"]
        return dumps(logindata)
            

    def add_pending_request(self,datagramId,date):
        #logger.info("Adding pending requesto " + str(self.sensor)+" " + str(datagramId)+" " + str(date))
        PENDING_DB.add_pending_job(DV=self.sensor,datagramId=datagramId,date=date)
        
    
    def execute_pending_jobs(self):
        PENDING_DB.execute_pending_jobs(sender=IBERDROLA,DV=self.sensor)
        
    def __checkconnection(self):
        # try:
            # self.contract()
        # except Exception as exc:
            # IBERDROLA.kill_login_thread()
            # IBERDROLA.init_login_thread()
        self.__checksession()
        
    def __checksession(self):
        #logger.error('IBERDROLA: enters check session. Disabled: ' + str(self._disabled)+'. Session: ' + str(self._session)+'. Loggedin: ' + str(self._loggedin))
        if self._disabled:
            raise IBERDROLA._EnableException
        
        if not self._session:
            raise IBERDROLA._SessionException

    def wattmeter(self):
        """Returns your current power consumption.
           Devuelve tu potencia actual."""
        
        from random import randint
        from time import sleep
        #logger.error('IBERDROLA: Enters wattmeter')
        sleep(randint(0,10))
        self.__checkconnection()
        response = self._session.request("GET", self.__watthourmeterurl, headers=self.__headers)
        if response.status_code != 200:
            logger.error('IBERDROLA: Error status_code for wattmeter. Code: ' + str(response.status_code))
            raise IBERDROLA._ResponseException
        if not response.text or response.text=='{}':
            raise IBERDROLA._NoResponseException
        jsonresponse = response.json()
        #logger.error('IBERDROLA: responded ' + str(jsonresponse))
        return jsonresponse['valMagnitud']

    def icpstatus(self):
        """Returns the status of your ICP.
           Devuelve el estado de tu ICP."""
        self.__checkconnection()
        response = self._session.request("POST", self.__icpstatusurl, headers=self.__headers)
        if response.status_code != 200:
            raise IBERDROLA._ResponseException
        if not response.text or response.text=='{}':
            raise IBERDROLA._NoResponseException
        jsonresponse = response.json()
        if jsonresponse["icp"] == "trueConectado":
            return True
        else:
            return False
    
    def miconsumodiario(self,date):
        '''    OJO, EL CONSUMO DIARIO SE ACTUALIZA SOBRE LAS 12 A.M. CON UN DIA DE RETRASO
        '''
        import datetime
        logger.error('IBERDROLA: Enters miconsumodiario')
        self.__checkconnection()
        
        if type(date) is datetime.datetime:
            date=date.replace(hour=0,minute=0,second=0,microsecond=0)
        elif type(date) is datetime.date:
            date=datetime.datetime(day=date.day,month=date.month,year=date.year)
        else:
            logger.error('IBERDROLA: Error date. Date: ' + str(date))
            raise IBERDROLA._ResponseException
        timestamp=date.timestamp()
        date=date.strftime('%d-%m-%Y%H:%M:%S')
        
        response = self._session.request("GET", self.__miconsumourl.replace('dateini',date), headers=self.__headers)
        
        if response.status_code != 200:
            logger.error('IBERDROLA: Error status_code for miconsumodiario. Code: ' + str(response.status_code))
            raise IBERDROLA._ResponseException
        if not response.text or response.text=='{}':
            raise IBERDROLA._NoResponseException
        jsonresponse = response.json()
        logger.error('IBERDROLA: Data received: ' + str(jsonresponse))
        try:
            datas=jsonresponse["y"]["data"][0]
        except:
            return None
        
        if datas!=[]:
            mean=0
            sum=0
            valid_data=0
            for i,data in enumerate(datas):
                if data==None:
                    datas[i]={}
                    datas[i]["valor"]=None
                else:
                    sum=sum+float(datas[i]["valor"])
                    valid_data=valid_data+1
                    
                datas[i]["timestamp"]=datetime.datetime.utcfromtimestamp(timestamp)+datetime.timedelta(hours=i+1)
                datas[i]["mean"]=None
                datas[i]["sum"]=None
            if valid_data>0:
                mean=sum/valid_data
            else:
                mean=None
                sum=None
            datas[0]["mean"]=round(mean,1)
            datas[0]["sum"]=round(sum,1)
            datas[i]["mean"]=round(mean,1)
            datas[i]["sum"]=round(sum,1)
        else:
            datas=None
        return datas
        
    def contracts(self):
        self.__checksession()
        response = self._session.request("GET", self.__contractsurl, headers=self.__headers)
        if response.status_code != 200:
            raise IBERDROLA._ResponseException
        if not response.text or response.text=='{}':
            raise IBERDROLA._NoResponseException
        jsonresponse = response.json()
        if jsonresponse["success"]:
            return jsonresponse["contratos"]

    def contract(self):
        self.__checksession()
        response = self._session.request("GET", self.__contractdetailurl, headers=self.__headers)
        if response.status_code != 200:
            raise IBERDROLA._ResponseException
        if not response.text or response.text=='{}':
            raise IBERDROLA._NoResponseException
        return response.json()

    def contractselect(self, id):
        self.__checksession()
        response = self.__session.request("GET", self.__contractselectionurl + id, headers=self.__headers)
        if response.status_code != 200:
            raise IBERDROLA._ResponseException
        if not response.text or response.text=='{}':
            raise IBERDROLA._NoResponseException
        jsonresponse = response.json()
        if not jsonresponse["success"]:
            raise Exception
    
    def initializeDB(self,fromdate,datagramId = 'dailyconsumption'):
        i=0
        while fromdate+datetime.timedelta(days=i)<datetime.datetime.now().replace(hour=0)-datetime.timedelta(days=1):
            date=fromdate+datetime.timedelta(days=i)
            returned=self.__call__(date=date,datagramId = datagramId)
            i=i+1
            if returned['Error']=='':
                texto='Initializing data for '+str(self.sensor)+'. Obtained data for ' + str(date)
            else:
                texto='Error getting data for '+str(self.sensor)+'. Error ' + returned['Error']
            PublishEvent(Severity=0,Text=texto,
                             Code=self.sensor.getEventsCode()+'init',Persistent=True)
    
    def getSingleDay(self,date,datagramId = 'dailyconsumption'):
        returned =self.__call__(date=date,datagramId = datagramId)
        if returned['Error']=='':
            texto='Got single day data for '+str(self.sensor)+'. Obtained data for ' + str(date)
        else:
            texto='Error getting data for '+str(self.sensor)+'. Error ' + returned['Error']
        PublishEvent(Severity=0,Text=texto,
                         Code=self.sensor.getEventsCode()+'singleDay',Persistent=True)
    
    def execute(self,order,params={}):
        if order=='initializeDB':
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
        elif order=='singleDay':
            if not "date" in params:
                text=_("Failed to execute order ")+order+_(" on device ")+str(self.sensor)+_(". The parameters passed ")+str(params) + _(" are not adequate.")
                return (100,"Wrong or not enough parameters passed")
            else:
                try:
                    date=datetime.datetime(params['date'])
                except:
                    return (100,"Wrong parameters passed. " + params['date'] + " should be a datetime conversible string.")
                self.getSingleDay(date=date,datagramId = 'dailyconsumption')
                return (200,None)
    
    def __call__(self,date=None,datagramId = 'dailyconsumption'):
        from time import sleep
        null=False
        if datagramId =='dailyconsumption':
            retries=self._MAX_RETRIES
            add2pending=True
        elif datagramId=='instantpower':
            retries=1
            add2pending=False
        if type(date) is datetime.datetime:
            date=date.date()
        while retries>0:
            try:
                if datagramId =='dailyconsumption':
                    if date==None:
                        date=(datetime.datetime.now()+datetime.timedelta(days=-1)).date()
                    datas = self.miconsumodiario(date=date)
                    if datas!=None:
                        values=[]
                        for data in datas:
                            values.append([data['timestamp'],data['valor'],data['mean'],data['sum']])
                        #logger.info('Values: ' + str(values))
                        returned=self.sensor.insertManyRegisters(DatagramId=datagramId,year=data['timestamp'].year,values=values,NULL=False)
                        logger.info('Insert many registers returned code : ' + str(returned))
                        if returned==None or returned!=0:
                            raise IBERDROLA._DBException
                        IBERDROLA.Error=''
                    else:
                        null=True
                        IBERDROLA.Error='Empty dataframe'
                elif datagramId=='instantpower':
                    data = self.wattmeter()
                    if data!=None:
                        timestamp=timezone.now().replace(second=0)
                        returned=self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=[data,],NULL=null)
                        if returned==None or returned!=0:
                            raise IBERDROLA._DBException
                        IBERDROLA.Error=''
                    else:
                        null=True
                        IBERDROLA.Error='Empty dataframe'
                if IBERDROLA.Error!='': 
                    if retries>1:
                        IBERDROLA.Error=IBERDROLA.Error+' - retrying'
                        sleep(5)    # to avoid too frequent sucessive requests
                    else:
                        IBERDROLA.Error='Error: Finished retrying'
                    retries=retries-1 
                    
                else:
                    retries=0
            except Exception as ex:
                if type(ex) is IBERDROLA._NoResponseException:
                    IBERDROLA.Error='Empty dataframe received for ' + datagramId
                elif type(ex) is IBERDROLA._ResponseException:
                    IBERDROLA.Error='Iberdrola server reported a failure on a data request for ' + datagramId
                elif type(ex) is IBERDROLA._SessionException:
                    IBERDROLA.Error='Login failure'
                elif type(ex) is IBERDROLA._EnableException:
                    IBERDROLA.Error='Iberdrola is not enabled'
                elif type(ex) is IBERDROLA._DBException:
                    IBERDROLA.Error='DB raised and error'
                else:
                    IBERDROLA.Error='Unknown APIError: ' + str(ex)
                logger.error(IBERDROLA.Error)
                retries=0
                null=True
        
        if null==False:
            LastUpdated=timezone.now()
        else:
            LastUpdated=None
            if add2pending and date!=None:
                try:
                    self.add_pending_request(datagramId=datagramId, date=date)
                except:
                    logger.error("Failed but could not be added to pending_jobs with date: " + str(date) + " and datagramID: " + str(datagramId))

        return {'Error':IBERDROLA.Error,'LastUpdated':LastUpdated}
    
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
    
    @staticmethod
    def runOnInit(DV):
        PENDING_DB.execute_pending_jobs(sender=ESIOS,DV=DV)
    
    def add_pending_request(self,datagramId,date):
        PENDING_DB.add_pending_jobs(DV=self.sensor,datagramId=datagramId,date=date)
    
    def execute_pending_jobs(self):
        PENDING_DB.execute_pending_jobs(sender=ESIOS,DV=self.sensor)
        
                
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
        #logger.info("URL: " + url)
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
            logger.info('Parsing ' + name)
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
        #logger.info('Type date: '+str(type(date)))
        #logger.info('DatagramId: '+str(datagramId))
        if datagramId =='energy_cost':
            # gets the hourly cost for the energy for the next day
            retries=self._MAX_RETRIES
            indicators_ = [10229, 10230, 10231]
            names = self.get_names(indicators_)
            if type(date) is datetime.datetime:
                start_=date.replace(hour=23,minute=59,second=59)
            elif type(date) is datetime.date:
                start_=datetime.datetime(day=date.day,month=date.month,year=date.year).replace(hour=23,minute=59,second=59)
            elif date==None:
                start_=timezone.now().replace(hour=23,minute=59,second=59)
            
            #logger.info('start_ '+str(start_))
            end_=(start_+datetime.timedelta(days=1)).replace(hour=23,minute=59,second=59)
            #logger.info('end_ '+str(end_))
            while retries>0:
                try:
                    dfmul, df_list, names = self.get_multiple_series(indicators_, start_, end_)
                    #logger.info("returned: " + str(dfmul))
                    if dfmul is not None:
                        null=False
                        Error=''
                        #logger.info("returned: " + str(dfmul[names]))
                        df = dfmul[names]/1000
                        values=[]
                        for timestamp,row in zip(df.index,df.values):
                            temp=list(row)
                            temp.insert(0,timestamp.to_pydatetime())
                            values.append(temp)
                        #logger.info("returned values: " + str(values))
                        self.sensor.insertManyRegisters(DatagramId=datagramId,year=timestamp.year,values=values,NULL=False)

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
                    Error='APIError:' + str(ex)
                    null=True
        
        if null==False:
            LastUpdated=timezone.now()
        else:
            LastUpdated=None
            try:
                self.add_pending_request(datagramId=datagramId,date=start_.date())
            except:
                pass
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
    _thread=None
    _accumulators={}
    
    def __init__(self,DV):
        self.type = Adafruit_DHT.DHT22
        self.sensor=DV
        self._maxDT=0.2*self.sensor.Sampletime/60 # maximum delta T allowed 0.2degC per minute
        
    
    @staticmethod
    def runOnInit(DV):
        cache.set('DHT22_accumulators['+str(DV.IO.Pin)+']', {'T':[],'H':[],'n':0}, None)
        DHT22.init_thread(DV=DV)
        
    @classmethod
    def init_thread(cls,DV):
        try:
            instance=cls(DV=DV)
            from utils.asynchronous_tasks import BackgroundTimer
            instance._thread=BackgroundTimer(callable=instance.read,threadName=str(instance.sensor)+'_thread',interval=instance.sensor.RTsampletime,
                            callablekwargs={'type':instance.type,'pin':instance.sensor.IO.Pin},
                            repeat=True,triggered=False,lifeSpan=None,onThreadInit=None,
                            onInitkwargs={})
        except Exception as ex:
            logger.error(str(instance.sensor)+': thread failed : ' + str(ex))
    
    def kill_thread(self):
        if self._thread!=None:
            self._thread.kill()
        self._thread=None
        logger.error(str(self.sensor)+': Killed the thread')
        
        
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
        
    @staticmethod
    def read(type,pin):
        try:
            h, t = Adafruit_DHT.read_retry(type, pin)
        except Exception as exc:
            logger.error('Exception on DHT read ' + str(exc))
            return
                
        if t != None and h != None:
            if (t > DHT22._maxT or t < DHT22._minT):
                t=None
                h=None
            else:
                DHT22._accumulators=cache.get('DHT22_accumulators['+str(pin)+']')
                DHT22._accumulators['n']=DHT22._accumulators['n']+1
                DHT22._accumulators['T'].append(t)
                DHT22._accumulators['H'].append(h)
                cache.set('DHT22_accumulators['+str(pin)+']', DHT22._accumulators, timeout=None)
    
    def resetAccumulator(self):
        cache.set('DHT22_accumulators['+str(self.sensor.IO.Pin)+']', {'T':[],'H':[],'n':0}, timeout=None)
    
    def getAccumulatedValues(self):
        from utils.dataMangling import remove_outlier
        import pandas as pd
        _accumulators=cache.get('DHT22_accumulators['+str(self.sensor.IO.Pin)+']')
        #logger.info('Accumulated values T: '+str(_accumulators['T']) )
        if _accumulators is not None and len(_accumulators['T'])>0:
            df = pd.DataFrame({'T':_accumulators['T'],'H':_accumulators['H']})
            df=remove_outlier(df_in=df, col_name='T')
            T=df['T'].mean(skipna =True)
            H=df['H'].mean(skipna =True)
            #logger.info('Accumulated values T: '+str(df['T']) )
        else:
            H=None
            T = None
            logger.error('No accumulated values!!')
        
        return T,H
    
    def __call__(self,datagramId = 'data'):
        """
        Read temperature and humidity from DHT sensor.
        """
        DHT22.init_thread(DV=self.sensor)   # this relaunches the reading thread in case it died
        timestamp=timezone.now() #para hora con info UTC 
        humidity=0
        temperature=0
        retries=0
        x=0
        Error=''

        t,h=self.getAccumulatedValues()
        self.resetAccumulator()
        
        
        if t != None:
            if t>=self._maxT:
                t=self._maxT
            if h>=self._maxH:
                h=self._maxH
            if self._lastTemp!=None: 
                if abs(self._lastTemp-t)>self._maxDT:
                    logger.warning('Measure from ' + str(self.sensor.Name) + ' exceded maxDT!! Last Temperature: ' + str(self._lastTemp) + ' and current is : '+ str(t))
                    Error+=' - maxDT'
                    t = self._maxT
                
            if (t < self._maxT and t > self._minT):
                pass
            else:
                logger.warning('Measure from ' + str(self.sensor.Name) + ' out of bounds!! Temperature: ' + str(t))
                Error+=' - maxminT'
                
            if (h < self._maxH and h > self._minH):
                pass
            else:
                logger.warning('Measure from ' + str(self.sensor.Name) + ' out of bounds!! Humidity: '+ str(h))
                Error+=' - maxminH'
        
            t=round(t,3)
            h=round(h,3)
            dewpoint=round((h/100)**(1/8)*(112+0.9*t)+0.1*t-112,3)
            hi=round(self.computeHeatIndex(temperature=t, percentHumidity=h),3)
            null=False
            self._lastTemp=t
        else:
            dewpoint=None
            hi=None
            null=True
            Error=str(self.sensor)+' - No valid measure has been obtained'
        self.sensor.insertRegister(TimeStamp=timestamp,DatagramId=datagramId,year=timestamp.year,values=(t,h,dewpoint,hi),NULL=null)
        
        reading={
            'timestamp':timestamp,
            'temperature':t,
            'humidity':h,
            'heat index':hi,
        }
        if null==False:
            LastUpdated=timestamp
        else:
            LastUpdated=None
        
        return {'Error':Error,'LastUpdated':LastUpdated}

                
        
    def query_sensor(self,**kwargs):
        """
        Read temperature and humidity from DHT sensor.
        """
        timestamp=timezone.now() #para hora con info UTC 
        t,h=self.getAccumulatedValues()
        if t==None:
            t=self._maxT
        if h==None:
            h=self._maxH
        if (t < self._maxT and t > self._minT) and (h < self._maxH and h > self._minH):
            dewpoint=(h/100)**(1/8)*(112+0.9*t)+0.1*t-112
        else:
            dewpoint=0
        return (round(h,3), round(t,3), round(dewpoint,3))
