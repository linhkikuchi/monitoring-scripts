#!/usr/bin/env python
"""
check_heartbeat.py - Check the status of the heartbeat system. Reports an error if
too much time has elapsed since the last heartbeat insert, store or report event.

This program looks for a configuration file named heartbeat.cfg in the current directory.

usage: check_heartbeat.py [options]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config=CONFIG
                        Load the named configuration file. This configuration
                        file defines the hostname, username and password for
                        the database to query for heartbeat data. Defaults to
                        heartbeat.cfg in the current directory.
  -i INSERTAGE, --insert-age=INSERTAGE
                        The maximum amount of time (in seconds) that can
                        elapse between heartbeat insert events before an error
                        is returned. Defaults to 600 seconds or ten minutes.
  -s STOREAGE, --store-age=STOREAGE
                        The maximum amount of time (in seconds) that can
                        elapse between heartbeat store events before an error
                        is returned. Defaults to 1800 seconds or 30 minutes.
  -r REPORTAGE, --report-age=REPORTAGE
                        The maximum amount of time (in seconds) that can
                        elapse between heartbeat report events before an error
                        is returned. Defaults to 1800 seconds or 30 minutes.

A sample configuration file looks like this:

## Configuration file for the Heartbeat Nagios check.

[Database]
host=apeshop
dbname=ape_heartbeat
dbuser=user
password=xxx

[EventAges]
## these times are in seconds
insert_age=600
store_age=1800
report_age=1800
                        
"""

import sys,syslog,time,os
import MySQLdb, ConfigParser
from optparse import OptionParser

def log(level,msg):
    syslog.syslog(level,msg)
    sys.stdout.write("%s\n" % (msg))

class HeartbeatEvent:
    def __init__(self):
        self.id=0
        self.client_id=0
        self.site_id=0
        self.token=""
        self.logtype=""
        self.insert_time=""
        self.store_time=""
        self.store_server=""
        self.current_status=0
        self.report_time_ux=0
        self.store_time_ux=0

    def from_query_result(self,row):
        if row is None:
            return
        self.id=row[0]
        self.client_id=row[1]
        self.site_id=row[2]
        self.logtype=row[3]
        self.token=row[4]
        self.insert_time=row[5]
        self.insert_server=row[6]
        self.store_time=row[7]
        self.store_server=row[8]
        self.current_status=row[9]
        self.insert_time_ux = row[10]
        self.store_time_ux=row[11]

class HeartbeatReportEvent:
    def __init__(self):
        self.heartbeat_record_id=0
        self.report_id=0
        self.report_server=0
        self.report_time_ux=0


    def from_query_result(self,row):
        self.heartbeat_record_id=row[0]
        self.report_id=row[1]
        self.report_server=row[2]
        self.report_time=row[3]
        self.report_time_ux=row[4]
        
class HeartbeatDB:
    def __init__(self,host,user,pw,dbname):
        self.host=host
        self.user=user
        self.pw=pw
        self.dbname=dbname
        self.dbconn=None

    def connect(self):
        self.dbconn=MySQLdb.connect(host=self.host,user=self.user,
                                    passwd=self.pw,db=self.dbname)

    def sql_query(self,sql,params=None):
        cursor=self.dbconn.cursor()
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,params)
            
        return cursor.fetchall()

    def set_time_zone_gmt(self):
        self.sql_query("SET time_zone = UTC")
        
    def get_events_within_time_period(self,minutes):
        toret=[]
        MySQLdb.paramstyle='qmark'
        
        sql = "select *,unix_timestamp(insert_time) as ux from heartbeat_records where timestampdiff(minute,insert_time,now()) < ? order by insert_time"
        rows = self.sql_query(sql,(minutes,))
        for row in rows:
            hb = HeartbeatEvent()
            hb.from_query_result(row)
            toret.append(hb)

        return toret

    def get_last_insert_event(self):
        toret=[]
        
        sql = "select *,unix_timestamp(insert_time) as ux,unix_timestamp(store_time) as uxs from heartbeat_records where insert_time = (select max(insert_time) from heartbeat_records)"
        rows = self.sql_query(sql)
        for row in rows:
            hb = HeartbeatEvent()
            hb.from_query_result(row)
            toret.append(hb)

        return toret

    def get_last_store_event(self):
        toret=[]
        
        sql = "select *,unix_timestamp(insert_time) as ux,unix_timestamp(store_time) as uxs from heartbeat_records where store_time = (select max(store_time) from heartbeat_records)"
        rows = self.sql_query(sql)
        for row in rows:
            hb = HeartbeatEvent()
            hb.from_query_result(row)
            toret.append(hb)

        return toret

    def get_last_report_event(self):
        toret=[]
        
        sql = "select *,unix_timestamp(report_time) as ux from heartbeat_report_records where report_time = (select max(report_time) from heartbeat_report_records)"
        rows = self.sql_query(sql)
        for row in rows:
            hbr = HeartbeatReportEvent()
            hbr.from_query_result(row)
            toret.append(hbr)

        return toret

class HeartbeatConfig:
    def __init__(self):
        self.dbhost=''
        self.dbname=''
        self.dbuser=''
        self.password=''
        self.insert_age=60*10
        self.store_age=60*30
        self.report_age=60*30

    def from_config_object(self,config_object):
        if config_object.has_option('Database','host'):
            self.dbhost=config_object.get('Database','host')
        if config_object.has_option('Database','dbname'):
            self.dbname = config_object.get('Database','dbname')
        if config_object.has_option('Database','dbuser'):
            self.dbuser = config_object.get('Database','dbuser')
        if config_object.has_option('Database','password'):
            self.password = config_object.get('Database','password')
            
        if config_object.has_option('EventAges','store_time'):
            self.store_time = config_object.getint('EventAges','store_age')
        if config_object.has_option('EventAges','insert_time'):
            self.insert_time = config_object.getint('EventAges','insert_age')
        if config_object.has_option('EventAges','report_time'):
            self.report_time = config_object.getint('EventAges','report_age')
        

## Load the heartbeat configuration file.
            
def load_configuration_file(cfg_file):
    config = ConfigParser.RawConfigParser()
    config.read(cfg_file)

    cfg_obj = HeartbeatConfig()
    cfg_obj.from_config_object(config)
    return cfg_obj
    
## turn a number of seconds into a string of the form: n days, n hours, n minutes...        
def elapsed(secs):
    intervals=[(60*60*24,'days'),(60*60,'hours'),(60,'minutes'),(1,'seconds')]
    remainder=secs
    toret=[]
    i=0
    while remainder > 0 and i < len(intervals):
        ti = int(remainder/intervals[i][0])
        remainder = remainder % intervals[i][0]
        toret.append((ti,intervals[i][1]))
        i=i+1

    return toret

def elapsed_to_string(elapsed_list):
    return ', '.join(
        map(lambda x: '%d %s' % (x[0],x[1]),
            filter(lambda x:x[0] > 0,
                   elapsed_list)))

def main(cfg_object):
    db = HeartbeatDB(cfg_object.dbhost,cfg_object.dbuser,cfg_object.password,cfg_object.dbname)
    try:
        db.connect()

        ## The Ape servers have their time zones set to UTC, so all
        ## heartbeat times are UTC. By default, monitor2 is NZST, UTC+12, so
        ## we must tell MySQL that it should work in UTC, not UTC+12.

        ## The following call requires that the steps outlined in 
        ##   http://dev.mysql.com/doc/refman/5.1/en/time-zone-support.html
        ## have been followed.
        db.set_time_zone_gmt()

        ## Get the latest insert event. Report an error if it's more than ten minutes
        ## ago.

        last_insert_time = ''
        last_store_time=''
        last_report_time=''
        
        hb_events = db.get_last_insert_event()
        if len(hb_events) == 0:
            log(syslog.LOG_ERR,"No heartbeat events have been recorded.")
            sys.exit(2)
        else:
            now=time.time()
            et=now - hb_events[0].insert_time_ux
            last_insert_time=elapsed_to_string(elapsed(et))
            if (et >= cfg_object.insert_age):
                log(syslog.LOG_ERR,"No heartbeat events have been recorded in the past %s. One should be recorded every five minutes. Last event was recorded at %s, %s ago." % (elapsed_to_string(elapsed(cfg_object.insert_age)),hb_events[0].insert_time,last_insert_time))
                sys.exit(2)

        ## Get the latest store event. A store event occurs when a beacon heartbeat line is
        ## added to the store.
        hb_store_events = db.get_last_store_event()
        if len(hb_store_events) == 0:
            log(syslog.LOG_ERR,"No heartbeat store events have been recorded.")
            sys.exit(2)
        else:
            the_event=hb_store_events[0]
            now=time.time()
            et=now - the_event.store_time_ux
            last_store_time=elapsed_to_string(elapsed(et))
            if (et >= cfg_object.store_age):
                log(syslog.LOG_ERR,"No heartbeat store events have been recorded in the past %s. Last event was recorded at %s, %s ago." % (
                    elapsed_to_string(elapsed(cfg_object.store_age)),the_event.store_time,last_store_time))
                sys.exit(2)
                

        ## Get the latest report event.
        hb_report_events = db.get_last_report_event()
        if len(hb_report_events) == 0:
            log(syslog.LOG_ERR,"No heartbeat report events have been recorded.")
            sys.exit(2)
        else:
            the_event=hb_report_events[0]
            now=time.time()
            et=now - the_event.report_time_ux
            last_report_time=elapsed_to_string(elapsed(et))
            if (et > cfg_object.report_age):
                log(syslog.LOG_ERR,"No heartbeat report events have been recorded in the past %s. Last event was recorded at %s, %s ago." % (elapsed_to_string(elapsed(cfg_object.report_age)),the_event.report_time,last_report_time))
                sys.exit(2)

        ## If we get here, all is ok.
        log(syslog.LOG_INFO,"OK. Heartbeat Insert %s ago: Heartbeat Store: %s ago: Heartbeat Report %s ago" % (
            last_insert_time,last_store_time,last_report_time))
        
    except MySQLdb.MySQLError,e:
        log(syslog.LOG_CRIT, "Failed to establish a connection to the database: %s" % e)
        sys.exit(2)

    
if __name__ == '__main__':
    parser=OptionParser()

    ## note how defaults for age options are 0. This is deliberate and allows us to tell
    ## when the user has not specified these values. If the user *does* specify a value for
    ## one of these then we want to override the configuration file specified option with that
    ## new option.
    parser.add_option("-c","--config", dest="config", default='heartbeat.cfg',
                      help="Load the named configuration file. This configuration file defines the hostname, username and password for the database to query for heartbeat data. Defaults to heartbeat.cfg in the current directory.")
    
    parser.add_option("-i","--insert-age", dest="insertage", default=0, type="int",
                      help="The maximum amount of time (in seconds) that can elapse between heartbeat insert events before an error is returned. Defaults to 600 seconds or ten minutes.")

    parser.add_option("-s","--store-age", dest="storeage", default=0, type="int",
                      help="The maximum amount of time (in seconds) that can elapse between heartbeat store events before an error is returned. Defaults to 1800 seconds or 30 minutes.")

    parser.add_option("-r","--report-age", dest="reportage", default=0, type="int",
                      help="The maximum amount of time (in seconds) that can elapse between heartbeat report events before an error is returned. Defaults to 1800 seconds or 30 minutes.")


    (options,args) = parser.parse_args()
    config = options.config
    insertage=options.insertage
    storeage=options.storeage
    reportage=options.reportage

    if (not os.path.exists(config)):
        log(syslog.LOG_CRIT,"Configuration file '%s' was not found. This program cannot run without this configuration file to specify the database host, username and password." % config)
        parser.print_help()
        sys.exit(2)
        
    cfg_obj = load_configuration_file(config)

    ## If the user specified values for insert_age, report_age or store_age, these override
    ## values specified in the configuration file.
    if insertage != 0:
        cfg_obj.insert_age = insertage
    if storeage != 0:
        cfg_obj.store_age = storeage
    if reportage != 0:
        cfg_obj.report_age = reportage
        
    main(cfg_obj)
    
