def editDict(keys,newValues,Dictionary):
    import copy
    newDict= copy.deepcopy(Dictionary)
    for key,newValue in zip(keys,newValues):
        if not key in newDict:
            raise ValueError('The key ' + key+ ' is not in dictionary DeviceDict')
        newDict[key]=newValue
    return newDict


def startApache():
    global P1
    import subprocess,time
    P1=subprocess.Popen(r'c:\xampp\apache_start.bat')
    time.sleep(2)

def stopApache():
    global P2
    import subprocess,time
    P2=subprocess.Popen(r'c:\xampp\apache_stop.bat')
    time.sleep(2)

def setupPowersXML(code,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0'):
    import shutil
    file=join(ApacheHTTPpath, 'powers.xml')
    shutil.copy(src=join(ApacheHTTPpath, 'powers_generic.xml'), dst=file)
    
    import fileinput

    with fileinput.FileInput(files=file, inplace=True) as file:
        for line in file:
            print(line.replace('#code#', str(code))
                  .replace('#dId#', str(datagramId))
                  .replace('#status#', str(status))
                  .replace('#p#', str(p))
                  .replace('#q#', str(q))
                  .replace('#s#', str(s))
                  , end='')
         
def resetPowersXML():
    file=join(ApacheHTTPpath, 'powers.xml')
    import os
    try:
        os.remove(path=file)
    except:
        pass
    
def InsertRegister2DB(DB,table,tags,values):
    SQLInsert=''' INSERT INTO "%s"(*) VALUES(?)'''
    cols=''
    vals=''
    for tag in tags:
        cols+='"'+tag+'",'
        vals+='?,'
    cols=cols[:-1]
    vals=vals[:-1]
    sql=SQLInsert.replace('%s',table).replace('*',cols).replace('?',vals)
    DB.executeTransactionWithCommit(SQLstatement=sql,arg=values)
    return sql