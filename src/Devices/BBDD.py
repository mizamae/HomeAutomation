# coding: utf-8
from itertools import chain
import datetime

import os
import random  # # ojo!! esto hay que quitarlo en produccion
import sys
import json

import Devices.GlobalVars
import Devices.XML_parser
import Devices.models
#import RemoteDevices.models
#import LocalDevices.models
import Master_GPIOs.models
import HomeAutomation.models
import sqlite3 as dbapi
import xml.etree.ElementTree as ET

import logging
logger = logging.getLogger("project")

#sql_delete_table=''' DROP TABLE IF EXISTS %s '''
#SQLupdate_statement = ''' UPDATE ? SET priority = ?,begin_date = ?,end_date = ? WHERE id = ?''' 
#SQLinsertcol_statement = '''ALTER TABLE %s ADD COLUMN %s %s'''      
class Database(object):
    
    def __init__(self,location=''):  
        if location != '':
            self.__conn = dbapi.connect(location,detect_types=dbapi.PARSE_DECLTYPES)
        else:
            self.__conn= None
            print ("Incorrect argument, missing location:", sys.exc_info()[1])            
            
    def rename_table(self,sql):
        try:
            cur=self.__conn.cursor()
            cur.execute(sql)
            self.__conn.commit()
        except:
            print ("Unexpected error in rename_table:", sys.exc_info()[1])
            logger.error("Unexpected error in rename_table: "+ str(sys.exc_info()[1]))
            
    def create_table(self,SQLstatement):
        try:
            cur=self.__conn.cursor()
            cur.execute(SQLstatement)
            self.__conn.commit()
        except:
            print ("Unexpected error in Create_table:", sys.exc_info()[1])
            logger.error("Unexpected error in Create_table: "+ str(sys.exc_info()[1]))
    
    def delete_table(self,table):
        try:
            sql_delete_table="DROP TABLE IF EXISTS %s"
            cur=self.__conn.cursor()
            cur.execute(sql_delete_table % table)
            self.__conn.commit()
        except:
            logger.error("Unexpected error in Delete_table: "+ str(sys.exc_info()[1]))
    
    def insert_column(self,table,column,type):
        sql='ALTER TABLE "' + table + '" ADD COLUMN "' + column + '" ' + type
        try:
            cur = self.__conn.cursor()
            cur.execute(sql)
            self.__conn.commit()  
            return 0
        except:
            print ("Unexpected error in insert_column:", sys.exc_info()[1]) 
            logger.error("Unexpected error in insert_column: "+ str(sys.exc_info()[1]))
            return -1
            
    def retrieve_from_table(self,sql,single,values):
        """
        Query all rows in the table
        :param conn: the Connection object
        :param table: Table to retrieve from
        :return: the rows
        """
        try:
            cur = self.__conn.cursor()
            if values[0]!=None:
                cur.execute(sql,values) 
            else:
                cur.execute(sql) 
            if single:
                rows = cur.fetchone()
            else:
                rows = cur.fetchall()
            cur.close()
            return rows
        except: 
            logger.error("Unexpected error in retrieve_from_table: "+ str(sys.exc_info()[1]))
            return None
    
    def retrieve_all_from_table(self,sql):
        """
        Query all rows in the table
        :param conn: the Connection object
        :param table: Table to retrieve from
        :return: the rows
        """
        try:
            cur = self.__conn.cursor()
            cur.execute(sql) 
            rows = cur.fetchall()
            cur.close()
            return rows
        except:
            logger.error("Unexpected error in retrieve_all_from_table: "+ str(sys.exc_info()[1]))
            return None
        
    def retrieve_rows_number(self,table):
        """
        Retrieve the number of columns in the table
        :param conn: Connection to the SQLite database
        :param table: table to count rows from
        :return:
        """
        sql = "SELECT Count() FROM %s" % table
        cur = self.__conn.cursor()
        cur.execute(sql)
        numberOfRows  = cur.fetchone()[0]
        cur.close()
        return numberOfRows
    
    def update_field(self,SQL_statement,fieldupdate,fieldupdate_value,keyfield,keyfield_value):
        """
        update a row by id
        :param conn: Connection to the SQLite database
        :param SQL_statement: SQL insert statement
        :param row_values: values of the fields
        :param ident: id of the row
        :return: project id
        SQLupdateDecide_statement = ''' UPDATE devices SET %s=? WHERE %s=?'''
        """
        try:
            cur = self.__conn.cursor()
            sql=SQL_statement % (fieldupdate,keyfield)
            cur.execute(sql, (fieldupdate_value,keyfield_value))
            self.__conn.commit()
            cur.close()
        except:
            print ("Unexpected error in update_row:", sys.exc_info()[1])
            logger.error("Unexpected error in update_row: "+ str(sys.exc_info()[1]))
    
    def delete_all_from_table(self,table):
        """
        Delete all rows in the table
        :param conn: Connection to the SQLite database
        :param table: Table to delete from
        :return:
        """
        if table.find('"')<0:
            table='"'+table+'"'
            
        sql = 'DELETE FROM ?'
        cur = self.__conn.cursor()
        cur.execute(sql,table)
        self.__conn.commit()
        cur.close()  
   
    def retrieve_cols_number(self,table):
        """
        Retrieve the number of columns in the table
        :param conn: Connection to the SQLite database
        :param table: table to count columns from
        :return:
        """
        if table.find('"')<0:
            table='"'+table+'"'
        sql = "PRAGMA table_info(%s)".replace('%s',table)
        cur = self.__conn.cursor()
        cur.execute(sql)
        numberOfColumns = len(cur.fetchall())
        cur.close()
        return numberOfColumns 
    
    def retrieve_cols_nametype(self,table):
        """
        Retrieve the names of columns in the table
        :param conn: Connection to the SQLite database
        :param table: table to retrieve columns from
        :return: datatypes of columns
        """
        if table.find('"')<0:
            table='"'+table+'"'
        cur = self.__conn.cursor()
        sql='PRAGMA TABLE_INFO(%s)'.replace('%s',table)
        cur.execute(sql)      
        info = cur.fetchall()
        #print("\nColumn Info:\nID, Name, Type, NotNull, DefaultVal, PrimaryKey")
        names=[]
        types=[]
        for col in info:
            names.append(col[1])
            types.append(col[2])
        return names,types 
       
    def retrieve_DB_structure(self, fields):
        sql='SELECT %s FROM sqlite_master WHERE type="table"' % (fields) 
        cur = self.__conn.cursor()
        cur.execute(sql)
        info = cur.fetchall()
        return info
    
    def insert_row(self,SQL_statement,row_values):
        """
        Insert a new row
        :param conn: Connection to the SQLite database
        :param SQL_statement: SQL insert statement
        :param table: Table to insert to
        :param row_values: values of the fields
        :return: inserted row Id
        """
        try:
            cur = self.__conn.cursor()
            cur.execute(SQL_statement, row_values)
            self.__conn.commit()
            lastRow=cur.lastrowid  
            cur.close()
            return lastRow   
        except:
            print ("Unexpected error in insert_row:", sys.exc_info()[1]) 
            logger.error("Unexpected error in insert_row: "+ str(sys.exc_info()[1]))
            return -1
       
    def delete_row(self,table,field,value):
        """
        Delete a row by id
        :param table: table from which to delete
        :param ident: id of the row
        :return:
        """
        try:
            sql = 'DELETE FROM %s WHERE %s=?' % (table,field)
            cur = self.__conn.cursor()
            cur.execute(sql, (value,))
            self.__conn.commit()
            cur.close()
        except:
            print ("Unexpected error in delete_row:", sys.exc_info()[1])  
            logger.error("Unexpected error in delete_row: "+ str(sys.exc_info()[1]))
    
    def insert_column(self,table,column,type):
        if table.find('"')<0:
            table='"'+table+'"'
        if column.find('"')<0:
            column='"'+column+'"'
            
        sql='ALTER TABLE ' + table + ' ADD COLUMN ' + column + ' ' + type
        try:
            cur = self.__conn.cursor()
            cur.execute(sql)
            self.__conn.commit()  
            return 0
        except:
            print ("Unexpected error in insert_column:", sys.exc_info()[1]) 
            logger.error("Unexpected error in insert_column: "+ str(sys.exc_info()[1]))
            return -1
            
    def compact_table(self,table):
        sql="VACUUM " + table
        try:
            cur = self.__conn.cursor()
            cur.execute(sql)
            self.__conn.commit()  
            return 0
        except:
            print ("Unexpected error in compact_table:", sys.exc_info()[1]) 
            logger.error("Unexpected error in compact_table: "+ str(sys.exc_info()[1]))
            return -1
         
class RegistersDatabase(Database):  
    """
    DATABASE THAT STORES THE INFORMATION ABOUT THE REGISTERS. EACH YEAR A NEW DB IS CREATED.
    :FORM: 
    :TABLES: This DB will have one table per device and datagram. This is, tableName = DeviceName+"_"+DatagramId
        Each table will have the fields according to the datagram as configured in 'configuration.xml'
            :field1: timestamp
            :field2: first field in the datagram
            ...
    """
    
    SQL_createRegister_table = ''' 
                                CREATE TABLE IF NOT EXISTS ? (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    *
                                    UNIQUE (timestamp)                    
                                ); 
                                '''  # the * will be replaced by the column names and types
    SQLinsertRegister_statement = ''' INSERT INTO %s(*) VALUES($) '''   # the * will be replaced by the column names and the $ by the values     
    
    SQL_createEvents_table = ''' 
                                CREATE TABLE IF NOT EXISTS events (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    Sender text NOT NULL,
                                    DeviceName text NOT NULL,
                                    EventType text NOT NULL,
                                    Value integer
                                ); 
                              '''
    SQLinsertEvents_statement = ''' INSERT INTO events(timestamp,Sender,DeviceName,EventType,Value) VALUES(?,?,?,?,?) '''
    SQL_createIOs_table = ''' 
                                CREATE TABLE IF NOT EXISTS $ (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    *
                                    UNIQUE (timestamp)                    
                                ); 
                                '''  # the * will be replaced by the column names and $ by inputs or outputs
    SQLinsertIOs_statement = ''' INSERT INTO %s(*) VALUES(?) ''' # the * will be replaced by the column names and the ? by the values 
    SQL_createMainVARs_table = ''' 
                                CREATE TABLE IF NOT EXISTS $ (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    *
                                    UNIQUE (timestamp)                    
                                ); 
                                '''  # the * will be replaced by the column names and $ by inputs or outputs
    SQLinsertMainVARs_statement = ''' INSERT INTO %s(*) VALUES(?) ''' # the * will be replaced by the column names and the ? by the values 
                                 
    SQL_createTracks_table = ''' 
                                CREATE TABLE IF NOT EXISTS tracks (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    User text NOT NULL,
                                    Latitude float NOT NULL,
                                    Longitude float NOT NULL,
                                    Accuracy float NOT NULL,
                                    UNIQUE (timestamp,User)                    
                                ); 
                                '''
    SQLinsertTrack_statement = ''' INSERT INTO tracks (timestamp,User,Latitude,Longitude,Accuracy) VALUES(?,?,?,?,?) ''' # the ? will be replaced by the values
    
    def __init__(self,location):
        super().__init__(location=location) # to execute the parent's constructor
       
    def create_datagram_table(self,DV,DG):
        """
        Creates the table corresponding to the Device DV and Datagram DG
        """
        TableName=str(DV.pk)+'_'+str(DG.pk)
        datagram=DG.getStructure()
        names=datagram['names']
        datatypes=datagram['datatypes']        
        logger.info('Creating "'+TableName+'" table with:')
        logger.info('   - DeviceType='+str(DV.Type))
        logger.info('   - fieldNames'+str(names)) 
        logger.info('   - fieldTypes'+str(datatypes))  
        fieldNames=names
        fieldTypes=datatypes
        try:
            if len(fieldNames)!=len(fieldTypes):
                logger.error('The length of the lists of names and types does not match in create_datagram_table')
                raise ValueError('The length of the lists of names and types does not match')
            else:
                temp_string=''
                for i in range(0,len(fieldNames)):
                    temp_string+='"'+fieldNames[i] + '" ' + fieldTypes[i] + ','
                sql=self.SQL_createRegister_table.replace('*',temp_string).replace('?','"'+TableName+'"')
                logger.info('SQL: ' + sql)
                super().create_table(SQLstatement=sql)                              
            logger.info('Succeded in creating the table "'+TableName+'"') 
        except:
            print ("Unexpected error in create_datagram_table:", sys.exc_info()[1])
            logger.error ("Unexpected error in create_datagram_table:"+ str(sys.exc_info()[1]))
            
    def create_tracks_table(self):
        """
        Creates the table corresponding to the position tracking
        """
        try:
            sql=self.SQL_createTracks_table
            super().create_table(SQLstatement=sql)                              
        except:
            print ("Unexpected error in create_tracks_table:", sys.exc_info()[1])
            logger.error ("Unexpected error in create_tracks_table:"+ str(sys.exc_info()[1]))
            
    def create_events_table(self):
        """
        Creates the table corresponding to the events
        """
        try:
            sql=self.SQL_createEvents_table
            super().create_table(SQLstatement=sql)                              
        except:
            print ("Unexpected error in create_events_table:", sys.exc_info()[1])
            logger.error ("Unexpected error in create_events_table:"+ str(sys.exc_info()[1]))
            
    def create_ios_table(self,IOs,table_name):
        """
        Creates the table corresponding to the Digital IOs of the Main unit
        :param IOs: is a vector of strings with the names of the IOs
        :param table_name: should be 'inputs' or 'outputs' 
        """
        if table_name.find('"')<0:
            table_name='"'+table_name+'"'
            
        try:
            if len(IOs)>0: 
                temp_string=''
                fieldType='integer'
                for IO in IOs:
                    temp_string+='"'+str(IO) + '" ' + fieldType + ','
                sql=self.SQL_createIOs_table.replace('*',temp_string).replace('$',table_name)
                logger.info('SQL: ' + sql)
                super().create_table(SQLstatement=sql)
            else:
                logger.info('Table '+table_name+' was not created because no IOs were defined.')
        except:
            print ("Unexpected error in create_ios_table:", sys.exc_info()[1])
            logger.error ("Unexpected error in create_ios_table:"+ str(sys.exc_info()[1]))
            
    def create_mainVars_table(self,VARs,table_name='"MainVariables"'):
        """
        Creates the table corresponding to the variables defined in the Main unit
        :param IOs: is a vector of strings with the names of the IOs
        :param table_name: should be 'inputs' or 'outputs' 
        """
        if table_name.find('"')<0:
            table_name='"'+table_name+'"'
            
        try:
            if len(VARs)>0: 
                temp_string=''
                fieldType='float'
                for VAR in VARs:
                    temp_string+='"'+str(VAR) + '" ' + fieldType + ','
                sql=self.SQL_createIOs_table.replace('*',temp_string).replace('$',table_name)
                logger.info('SQL: ' + sql)
                super().create_table(SQLstatement=sql)
            else:
                logger.info('Table '+table_name+' was not created because no Vars were defined.')
        except:
            print ("Unexpected error in create_mainVars_table:", sys.exc_info()[1])
            logger.error ("Unexpected error in create_mainVars_table:"+ str(sys.exc_info()[1]))
    
class DIY4dot0_Databases(object):
    EVENT_TYPES={
        'INPUT_CHANGE':'INPUT_CHANGE',
        'OUTPUT_CHANGE':'OUTPUT_CHANGE',
        'MAX_VALUE':'MAX_VALUE',
        'MIN_VALUE':'MIN_VALUE',
        'VAR_CHANGE':'VAR_CHANGE'
    }
    def __init__(self,devicesDBPath,registerDBPath,configXMLPath,year=''):
        
        if year=='':
            import datetime
            now=datetime.datetime.now()
            self.registersDB=RegistersDatabase(location=registerDBPath.replace('_XYEARX_', str(now.year)))
        else:
            self.registersDB=RegistersDatabase(location=registerDBPath.replace('_XYEARX_', str(year)))
        self.configXMLPath=configXMLPath
        if self.registersDB is None:
            print('The registers DB cannot be created at location: ' + registerDBPath)  
            raise RuntimeError('The registers DB cannot be created at location: ' + registerDBPath)                
                           
    def check_columns_registersDB(self,table,datagramStructure):
        if table.find('"')<0:
            table='"'+table+'"'
        dbNames,dbTypes =self.registersDB.retrieve_cols_nametype(table)  
        #logger.info('The columns on the table "'+table+'" have been checked.')      
        for datagramName,datagramType in zip(datagramStructure['names'],datagramStructure['datatypes']):
            vector=datagramName.split('_')
            datagramName=vector[0]
            #logger.info('   - '+datagramName) 
            for component in vector[1:]:
                if '$' in component: # found the $ item meaning bit labels
                    break
                datagramName=datagramName+'_'+component
            datagramName=datagramName
            #logger.info('   - '+datagramName)  
            found=False
            equalType=False
            for dbName,dbType in zip(dbNames,dbTypes):
                if dbName==datagramName:
                    found=True
                    if dbType==datagramType:
                        equalType=True
                    else:
                        pass# here the type of the column should be changed but SQLITE does not support
            if found==False:
                inserted=self.registersDB.insert_column(table=table,column=datagramName,type=datagramType)  
                logger.info('The column '+datagramName+' have been added on table ' + table)
        
    def check_IOsTables(self):
        rows=self.registersDB.retrieve_DB_structure(fields='*')   #('table', 'devices', 'devices', 4, "CREATE TABLE devices...)       
        table_to_find='events'
        found=False
        for row in rows:
            if (row[1]==table_to_find):   # there is a table named devices
                found=True
                break
        if found is not True:
            self.registersDB.create_events_table()
            logger.info('The table '+table_to_find+' was not created.') 
        
        table_to_find='tracks'
        found=False
        for row in rows:
            if (row[1]==table_to_find):   # there is a table named devices
                found=True
                break
        if found is not True:
            self.registersDB.create_tracks_table()
            logger.info('The table '+table_to_find+' was not created.') 
        
        IOs=Master_GPIOs.models.IOmodel.objects.all()
        inputs={}
        inputs['names']=[]
        inputs['types']=[]
        inputs['datatypes']=[]
        outputs={}
        outputs['names']=[]
        outputs['types']=[]
        outputs['datatypes']=[]
        for IO in IOs:
            if IO.direction=='OUT':
                outputs['names'].append(str(IO.pin))
                outputs['datatypes'].append('integer')
            elif IO.direction=='IN':
                inputs['names'].append(str(IO.pin))
                inputs['datatypes'].append('integer')
                
        if len(inputs['names'])>0:
            table_to_find='inputs'
            found=False
            for row in rows:
                if (row[1]==table_to_find):   # there is a table named inputs
                    found=True
                    break
            if found is not True:
                self.registersDB.create_ios_table(IOs=inputs['names'],table_name='inputs')
                logger.info('The table '+table_to_find+' was not created.') 
            else:
                self.check_columns_registersDB(table='inputs',datagramStructure=inputs)
        
        if len(outputs['names'])>0:
            table_to_find='outputs'
            found=False
            for row in rows:
                if (row[1]==table_to_find):   # there is a table named outputs
                    found=True
                    break
            if found is not True:
                self.registersDB.create_ios_table(IOs=outputs['names'],table_name='outputs')
                logger.info('The table '+table_to_find+' was not created.') 
            else:
                self.check_columns_registersDB(table='outputs',datagramStructure=outputs)
                
        VARs=HomeAutomation.models.MainDeviceVarModel.objects.all()
        vars={}
        vars['names']=[]
        vars['types']=[]
        vars['datatypes']=[]
        
        for VAR in VARs:
            vars['names'].append(str(VAR.pk))
            vars['datatypes'].append('float')
                
        if len(vars['names'])>0:
            table_to_find='MainVariables'
            found=False
            for row in rows:
                if (row[1]==table_to_find):   # there is a table named inputs
                    found=True
                    break
            if found is not True:
                self.registersDB.create_mainVars_table(VARs=vars['names'])
                logger.info('The table '+table_to_find+' was not created.') 
            else:
                self.check_columns_registersDB(table=table_to_find,datagramStructure=vars)
                
    def check_registersDB(self):
        
        rows=self.registersDB.retrieve_DB_structure(fields='*')   #('table', 'devices', 'devices', 4, "CREATE TABLE devices...)
        
        required_registers_tables=[]
            
        DVs=Devices.models.DeviceModel.objects.all()
        if len(DVs)>0:
            for DV in DVs:
                DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
                for DG in DGs:
                    found=False
                    table_to_find=str(DV.pk)+'_'+str(DG.pk)
                    for row in rows:
                        if (row[1]==table_to_find):   # found the table in the DB
                            found=True
                            self.check_columns_registersDB(table=table_to_find,datagramStructure=DG.getStructure())
                            break
                    if found is not True:
                        required_registers_tables.append((DV,DG)) 
                        logger.info('The table '+table_to_find+' was not created.') 
        else:
            logger.info('There are no registered devices')
            
        for table in required_registers_tables:
            self.registersDB.create_datagram_table(DV=table[0],DG=table[1])
            
    def create_DeviceRegistersTables(self,DV):
        """
        CREATES ALL REGISTERS TABLE:
        DeviceName_DatagramId
        """
        #datagramList=Devices.models.getDatagramStructure(devicetype=DeviceType)
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
        for DG in DGs:
            self.registersDB.create_datagram_table(DV=DV,DG=DG)
   
    def insert_VARs_register(self,TimeStamp):

        try:
            VARs=HomeAutomation.models.MainDeviceVarModel.objects.all()
            values=[TimeStamp]
            valuesHolder='?,'
            columns='timestamp,'
            for VAR in VARs:
                values.append(VAR.Value)
                columns+='"'+str(VAR.pk)+'",'
                valuesHolder+='?,'
            columns=columns[:-1]
            valuesHolder=valuesHolder[:-1]
            table='MainVariables'
                
            sql=self.registersDB.SQLinsertMainVARs_statement.replace('%s',table).replace('*',columns).replace('?',valuesHolder)
            #''' INSERT INTO %s(*) VALUES($) ''' # the * will be replaced by the column names and the $ by the values 
            #logger.info('SQL: ' + sql)
            self.registersDB.insert_row(SQL_statement=sql, row_values=values)
        except:
            logger.error("Unexpected error in insert_MainVariables_register:" + str(sys.exc_info()[1]))
            
    def insert_IOs_register(self,TimeStamp,direction):
        ''' direction == 'IN' for inputs
        '''
        try:
            IOs=Master_GPIOs.models.IOmodel.objects.filter(direction=direction)
            values=[TimeStamp]
            valuesHolder='?,'
            columns='timestamp,'
            for IO in IOs:
                values.append(IO.value)
                columns+='"'+str(IO.pin)+'",'
                valuesHolder+='?,'
            columns=columns[:-1]
            valuesHolder=valuesHolder[:-1]
            if direction=='IN':
                table='inputs'
            elif direction=='OUT':
                table='outputs'
            else:
                raise ValueError('The value of parameter "direction" can only be "IN" for inputs or "OUT" for outputs')
                
            sql=self.registersDB.SQLinsertIOs_statement.replace('%s',table).replace('*',columns).replace('?',valuesHolder)
            #''' INSERT INTO %s(*) VALUES($) ''' # the * will be replaced by the column names and the $ by the values 
            #logger.info('SQL: ' + sql)
            self.registersDB.insert_row(SQL_statement=sql, row_values=values)
        except:
            logger.error("Unexpected error in insert_IOs_register:" + str(sys.exc_info()[1]))
        
    def insert_device_register(self,TimeStamp,DeviceCode,DeviceName,DatagramId,year,values,NULL=False):
        """
        INSERTS A REGISTER IN THE registersDB INTO THE APPROPIATE TABLE.
        """
        try:                              
     
            try:
                DV=Devices.models.DeviceModel.objects.get(DeviceName=DeviceName)
            except Devices.models.DeviceModel.DoesNotExist:
                logger.error('Error! The device with name '+DeviceName+' does not exist in the database')
                return
                    
            DG = Devices.models.DatagramModel.objects.get(DeviceType=DV.Type,Identifier=DatagramId)
            datagram=DG.getStructure()
            
            names=datagram['names']
            types=datagram['datatypes']
            sql=self.registersDB.SQLinsertRegister_statement
            #SQLinsertRegister_statement = ''' INSERT INTO %s(*) VALUES($) '''   # the * will be replaced by the column names and the $ by the values  
            temp_string1='?,'
            temp_string2='timestamp,' 
            for i in range(0,len(names)):
                if (names[i].find('$')>=0): # names[i]=STATUS_bits_Alarm0;Alarm1;Alarm2;Alarm3;Alarm4;Alarm5;Alarm6;Alarm7 
                                            #to remove the char ; from the name of the columns
                    tempname=names[i].split('_')
                    name=tempname[0]
                    for component in tempname[1:]:
                        if '$' in component: # found the $ item meaning bit labels
                            break
                        name=name+'_'+component
                    name=name
                else:
                    name=names[i]
                    
                if i<len(names)-1:
                    temp_string1+= '?,'
                    temp_string2+='"'+name+'"'+ ','
                else:
                    temp_string1+='?'
                    temp_string2+='"'+name+'"'
            roundvalues=[TimeStamp,]
            if NULL==False:
                for i in range(0,len(values)):  
                    roundvalues.append(round(values[i],3))
            else:
                logger.info('Inserted NULL values on device ' + DeviceName)  
                for i in range(0,len(names)):  
                    roundvalues.append(None)
                
            sql=sql.replace('*',temp_string2)        
            sql=sql.replace('$',temp_string1).replace('%s','"'+str(DV.pk)+'_'+str(datagram['pk'])+'"')
            #logger.info('SQL insert= '+sql)                
            self.registersDB.insert_row(SQL_statement=sql, row_values=roundvalues)
        except:
            logger.error("Unexpected error in insert_device_register:" + str(sys.exc_info()[1]))
                                                       
    def insert_event(self,TimeStamp,Sender,DeviceName,EventType,value):
        """
        INSERTS AN EVENT IN THE registersDB INTO THE events TABLE.
        """
        try:                              
            self.check_IOsTables()
            self.registersDB.insert_row(SQL_statement=self.registersDB.SQLinsertEvents_statement, row_values=(TimeStamp,Sender,DeviceName,EventType,value))
        except:
            print ("Unexpected error in insert_event:", sys.exc_info()[1])
            logger.error("Unexpected error in insert_event:" + str(sys.exc_info()[1]))
    
    def insert_track(self,TimeStamp,User,Latitude,Longitude):
        """
        INSERTS AN EVENT IN THE registersDB INTO THE events TABLE.
        """
        try:                              
            self.check_IOsTables()
            #SQLinsertTrack_statement = ''' INSERT INTO tracks (timestamp,User,Latitude,Longitud) VALUES(?) ''' # the ? will be replaced by the values
            self.registersDB.insert_row(SQL_statement=self.registersDB.SQLinsertTrack_statement, row_values=(TimeStamp,User,Latitude,Longitude))
        except:
            print ("Unexpected error in insert_track:", sys.exc_info()[1])
            logger.error("Unexpected error in insert_track:" + str(sys.exc_info()[1]))
            
    def rename_DeviceRegister_tables(self,OldDeviceName,NewDeviceName):
        tables=self.registersDB.retrieve_DB_structure(fields='*')   #('table', 'devices', 'devices', 4, "CREATE TABLE devices...)
        OldDeviceName=OldDeviceName
        NewDeviceName=NewDeviceName
        for table in tables:
            if (table[1].find(OldDeviceName)>=0):
                newName=table[1].replace(OldDeviceName,NewDeviceName)
                sql='ALTER TABLE "'+ table[1] +'" RENAME TO "'+ newName+'"'
                self.registersDB.rename_table(sql=sql)
                
    def delete_DeviceRegister_tables(self,DeviceName):
        tables=self.registersDB.retrieve_DB_structure(fields='*')   #('table', 'devices', 'devices', 4, "CREATE TABLE devices...)
        DeviceName=DeviceName
        for table in tables:
            if (table[1].find(DeviceName)>=0):
                self.registersDB.delete_table(table=table[1])
        
def main():
    applicationDBs=DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
    applicationDBs.check_devicesDB()
    applicationDBs.check_registersDB()
    
    #applicationDBs.create_basic_devices_tables()
    applicationDBs.devicesDB.insert_new_device(DeviceName='Name', DeviceType='GAPQv1', DeviceIP='10.10.10.1', DeviceCode=1)
    applicationDBs.devicesDB.update_field(SQL_statement=applicationDBs.devicesDB.SQLupdateDevice_statement, fieldupdate='DeviceName', fieldupdate_value='Nombre', keyfield='DeviceCode', keyfield_value=1)
    
    #applicationDBs.create_all_registers_tables()
    now=datetime.datetime.now()
    applicationDBs.insert_device_register(TimeStamp=now,DeviceCode=1,DeviceName='Nombre',DatagramId='async',year=2017,values=(10,))
    applicationDBs.insert_device_register(TimeStamp=now,DeviceCode=1,DeviceName='Nombre',DatagramId='instant',year=2017,values=(220,5,50))
    applicationDBs.insert_device_register(TimeStamp=now,DeviceCode=1,DeviceName='Nombre',DatagramId='powers',year=2017,values=(0,5.33,0.25,5.55,0.99))
            
if __name__ == '__main__':
    main()
                        