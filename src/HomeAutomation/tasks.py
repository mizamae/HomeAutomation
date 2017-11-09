import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler

import HomeAutomation.models
import Devices.GlobalVars
import Devices.BBDD

logger = logging.getLogger("project")

scheduler = BackgroundScheduler()                    

def compactRegistersDB():
    AppDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
    rows=AppDB.registersDB.retrieve_DB_structure(fields='*')
    import datetime
    now=datetime.datetime.now()
    size = os.path.getsize(Devices.GlobalVars.REGISTERS_DB_PATH.replace('_XYEARX_', str(now.year)))
    logger.info('The DB size was ' + str(size/1000) + ' kB') 
    for row in rows:
        table_name=row[1]
        logger.info('Compacting table '+ table_name+ ' on process ' + str(os.getpid()))
        AppDB.registersDB.compact_table(table=table_name)
    size = os.path.getsize(Devices.GlobalVars.REGISTERS_DB_PATH.replace('_XYEARX_', str(now.year)))
    logger.info('The DB size after compactation is ' + str(size/1000) + ' kB') 
    
def start_registersDBcompactingTask(): 
    '''COMPACTS THE REGISTER'S TABLE MONTHLY ON THE LAST DAY OF THE MONTH AT 00:00:00
    '''  
    logger.info(Devices.GlobalVars.BOOTING_MSG)
    logger.info('Registers DB compacting task is added to scheduler on the process '+ str(os.getpid())) 
    scheduler.add_job(func=compactRegistersDB,trigger='cron',id='registerDBcompact',day='last',hour=0,minute=0)
    try:
        scheduler.start()
    except:
        pass

def checkReportAvailability():
    from Devices.models import ReportModel,ReportItems
    import json
    logger.info('Checking reports availability...')
    reports=ReportModel.objects.all()
    logger.info('There are ' + str(len(reports)) + ' reports configured.')
    for report in reports:
        logger.info('Report ' + report.ReportTitle)
        logger.info('Triggered ' + str(report.checkTrigger()))
        if report.checkTrigger():
            ReportData,fromDate,toDate=report.getReport()
            reportTitle=report.ReportTitle           
            logger.info('Report: '+str(ReportData))            
            report=ReportModel.objects.get(ReportTitle=reportTitle)
            rp=ReportItems(Report=report,fromDate=fromDate,toDate=toDate,data=json.dumps(ReportData))
            rp.save()
            logger.info('Report '+ reportTitle +' generated successfully.')

def start_reportsGenerationTask():
    '''THIS TASK IS RUN EVERY DAY AT HOUR 0 AND CHECKS IF ANY REPORT TRIGGERING CONDITION IS MET.
    IN CASE SO, IT GENERATES THE REPORT.
    '''
    logger.info('Report generation task is added to scheduler on the process '+ str(os.getpid())) 
    scheduler.add_job(func=checkReportAvailability,trigger='cron',id='checkReportAvailability',hour=0)
    try:
        scheduler.start()
    except:
        pass

def HourlyTask():
    logger.info('Checking hourly tasks...')
    HomeAutomation.models.checkHourlySchedules()

def start_HourlyTask():
    '''THIS TASK IS RUN EVERY HOUR.
    '''
    logger.info('Hourly task is added to scheduler on the process '+ str(os.getpid())) 
    scheduler.add_job(func=HourlyTask,trigger='cron',id='HourlyTask',minute=0)
    try:
        scheduler.start()
    except:
        pass