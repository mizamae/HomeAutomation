# coding: utf-8
from itertools import chain
import datetime
from django.utils.translation import ugettext_lazy as _

from django.utils import timezone
import os
import sys
import json

import time
import datetime
import sqlite3

import redis
import redis_lock

import multiprocessing
from multiprocessing import Process, Queue, JoinableQueue, cpu_count

from HomeAutomation.constants import REGISTERS_DB_PATH

import logging
logger = logging.getLogger("project")

# DEBUG
DEBUGGING=False
# END
# MODULE CONSTANTS
TYPE_TEXT='TEXT'
TYPE_FLOAT='FLOAT'
TYPE_INTEGER='INTEGER'
TYPE_TIMESTAMP='TIMESTAMP'
#END

#from django.conf.settings import REDIS_PORT,REDIS_HOST
REDIS_HOST='localhost'
REDIS_PORT=6379
lock_table = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

class RegistersDBException(Exception):
    def __name__(self):
        return 'RegistersDBException'
    pass
        
class Database(object):
    def __init__(self,location=''):  
        if location != '':
            self.conn = sqlite3.connect(location,detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            
        else:
            self.conn= None
            print ("Incorrect argument, missing location: ", sys.exc_info()[1])            
    
    def getConn(self):
        return self.conn
    
    def _execute(self,SQLstatement,arg):
        ''' THIS FUNCTION IS REQUIERED TO AVOID INTEGRITY ERROR WHEN TEO GPIOs ARE CHANGED AT THE SAME TIME
        '''
        try:
            cur=self.conn.cursor()
            cur.execute(SQLstatement,arg)
            self.conn.commit()
            cur.close()
            return 'OK'
        except sqlite3.IntegrityError:
            cur.close()
            return None
                
    def executeTransactionWithCommit(self,SQLstatement,arg=[]):
        with redis_lock.Lock(lock_table, "commitRegisterDB",expire=10, auto_renewal=True):            
            name = multiprocessing.current_process().name
            if DEBUGGING: print('The process ' + name + ' has the lock.')
            if arg!=[]:
                while self._execute(SQLstatement=SQLstatement,arg=arg)==None:# the timestamp arg[0] is increased 1 sec to avoid integrity error
                    arg[0]+=datetime.timedelta(seconds=1)
            else:
                self._execute(SQLstatement=SQLstatement,arg=arg)
            if DEBUGGING:print('The process ' + name + ' executed: ' + SQLstatement)
            if DEBUGGING:print('The process ' + name + ' releases the lock.')
            return 0
        return -1
            
    def executeTransaction(self,SQLstatement,arg=[]):
        cur=self.conn.cursor()
        cur.execute(SQLstatement,arg)
        rows = cur.fetchall()
        cur.close()
        return rows
    
    def retrieve_DB_structure(self, fields):
        sql='SELECT %s FROM sqlite_master WHERE type="table"' % (fields) 
        cur = self.conn.cursor()
        cur.execute(sql)
        info = cur.fetchall()
        cur.close()
        return info
    
    def retrieve_cols_nametype(self,table):
        """
        Retrieve the names of columns in the table
        :param conn: Connection to the SQLite database
        :param table: table to retrieve columns from
        :return: datatypes of columns
        """
        cur = self.conn.cursor()
        sql='PRAGMA TABLE_INFO("%s")'.replace('%s',table)
        cur.execute(sql)      
        info = cur.fetchall()
        #print("\nColumn Info:\nID, Name, Type, NotNull, DefaultVal, PrimaryKey")
        names=[]
        types=[]
        for col in info:
            names.append(col[1])
            types.append(col[2])
        return names,types 
    
    def compact_table(self,table):
        if table.find('"')<0:
            table='"'+table+'"'
            
        sql='VACUUM ' + table
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            self.conn.commit() 
            cur.close()
            return 0
        except:
            text = str(_("Error in compact_table: ")) + str(sys.exc_info()[1]) 
            #PublishEvent(Severity=5,Text=text + 'SQL: ' + sql,Persistent=True)
            #logger.error("Unexpected error in compact_table: "+ str(sys.exc_info()[1]))
            return -1
    
    def checkTableColumns(self,table,desiredColumns):
        dbNames,dbTypes =self.retrieve_cols_nametype(table)  
        for name,datatype in zip(desiredColumns['names'],desiredColumns['datatypes']): 
            found=False
            equalType=False
            for dbName,dbType in zip(dbNames,dbTypes):
                if dbName==name:
                    found=True
                    if dbType==datatype:
                        equalType=True
                    else:
                        pass# here the type of the column should be changed but SQLITE does not support
            if found==False:
                sql='ALTER TABLE "' + table + '" ADD COLUMN "' + name + '" ' + datatype
                self.executeTransactionWithCommit(SQLstatement=sql, arg=[]) 
                logger.info('The column '+name+' have been added on table ' + table)
                
    def dropTable(self,table):
        table='"'+table+'"'
        sql='DROP TABLE IF EXISTS %s' % table
        return self.executeTransactionWithCommit(SQLstatement=sql,arg=[])
    
    def checkIfColumnExist(self,table,column):
        if self.checkIfTableExist(table):
            names,types =self.retrieve_cols_nametype(table)
            if column in names:
                return True
        return False
        
    def checkIfTableExist(self,table):
        table='"'+table+'"'
        sql="SELECT name FROM sqlite_master WHERE type='table' AND name="+table
        return self.executeTransaction(SQLstatement=sql,arg=[])!=[]

def getRegistersDBInstance(year=None):
    if year==None:
        DBPath=REGISTERS_DB_PATH.replace("_XYEARX_",str(timezone.now().year))
    else:
        DBPath=REGISTERS_DB_PATH.replace("_XYEARX_",str(year))
    DB=Database(location=DBPath)
    return DB
            
def compactRegistersDB(year=None):
    if year==None:
        DBPath=REGISTERS_DB_PATH.replace("_XYEARX_",str(timezone.now().year))
    else:
        DBPath=REGISTERS_DB_PATH.replace("_XYEARX_",str(year))
    DB=Database(location=DBPath)
    rows=DB.retrieve_DB_structure(fields='*')
    sizep = os.path.getsize(DBPath)
    for row in rows:
        table_name=row[1]
        DB.compact_table(table=table_name)
    size = os.path.getsize(DBPath)
    return {'initial_size':sizep,'final_size':size}
                
                        