import datetime
#import pandas as pd
#import numpy as np 
import json
import math
import kandbox_planner.config as config

def minutes_to_time_string(minutes): 
    if 0< minutes < 24*60:
        return ':'.join(str(datetime.timedelta(minutes=minutes )).split(':')[0:2])
    else:
        return ':'.join(str(datetime.timedelta(minutes=minutes % (24*60) )).split(':')[0:2])

def time_string_hhmm_to_minutes(time_str):
    return int(time_string_hhmm_to_seconds(time_str)/60)

def strp_minutes_from_datetime(input_date):
    return input_date.hour*60 + input_date.minute



def day_minutes_to_datetime(k_day='20191201', minutes = 1):
    new_date = datetime.datetime.strptime(k_day,config.KANDBOX_DATE_FORMAT) +  datetime.timedelta(minutes=minutes)

    return new_date

def datetime_to_google_calendar_date_str(k_date): 
    
    return '{}-00:00'.format(k_date.isoformat().split('.')[0]   )

def seconds_to_time_string(seconds): 
    return str(datetime.timedelta(seconds=seconds))
    
def time_string_to_seconds(time_str):
    t = '10:15:30'
    t = time_str
    sp = t.split(':')
    if len(sp) == 2:
        m,s = sp
        return (int(datetime.timedelta(hours=0,minutes=int(m),seconds=int(s)).total_seconds()))
    else:
        h,m,s = sp
        return (int(datetime.timedelta(hours=int(h),minutes=int(m),seconds=int(s)).total_seconds()))
def time_string_to_minutes(time_str):
    return int(time_string_to_seconds(time_str)/60)
def time_string_hhmm_to_seconds(time_str):
    t = '10:15'
    t = time_str
    try:
        sp = t.split(':')
    except:
        print("An exception occurred with value {}".format(time_str))
        return 0
    
    if len(sp) == 2:
        h,m  = sp
        return (int(datetime.timedelta(hours=int(h),minutes=int(m),seconds=0).total_seconds()))
    else:
        h,m,s = sp
        return (int(datetime.timedelta(hours=int(h),minutes=int(m),seconds=int(s)).total_seconds()))

def get_right_end_minutes(startDate, endDate):

    if startDate > endDate  :
        return endDate + 1440  
    else:
        return endDate  

    
def int_hhmm_to_minutes(int_time_str): 
    t = int(int_time_str)
    return math.floor(t/100) * 60 + int(t% 100) 


def transform_weekly_worker_time_from_rhythm_v6(time_str):
    weekly_working_minutes = []
    ws = time_str.split(';')
    for work_day in ws:
        if len(work_day) < 2:
            weekly_working_minutes.append( [0,0  ]   )
            continue
        work_day_start =  int_hhmm_to_minutes(work_day.split('_')[0])
        work_day_end =  int_hhmm_to_minutes(work_day.split('_')[1])
        if work_day_end < work_day_start:
            work_day_end += 12*60
        
        weekly_working_minutes.append( [work_day_start,work_day_end  ]   )
    
    return json.dumps(weekly_working_minutes)
    
# print(transform_weekly_worker_time_from_rhythm_v6 ('0_0000_00;1_0830_0550;2_0830_0550;3_0830_0550;4_0830_0550;5_0830_0550;6_0830_0240'))
    



def clip_time_period(p1, p2):
  # each P is [<=, <]
  if p1[0] >= p2[1]:
    return []
  if p1[1] <= p2[0]:
    return []
  if p1[0] < p2[0]:
    start = p2[0]
  else: 
    start = p1[0]

  if p1[1] < p2[1]:
    end = p1[1]
  else: 
    end = p2[1]
  return [start, end]



def transform_kandbox_day_2_postgres_datetime(k_day = None):
    
    new_date = datetime.datetime.strftime ( datetime.datetime.strptime(k_day,config.KANDBOX_DATE_FORMAT) ,
        config.KANDBOX_DATETIME_FORMAT_WITH_MS)
    return new_date


def add_days_2_day_string(k_day = None, days = None):
    
    new_date = datetime.datetime.strptime(k_day,config.KANDBOX_DATE_FORMAT) +  datetime.timedelta(days=days)

    return datetime.datetime.strftime(new_date,config.KANDBOX_DATE_FORMAT) 


def days_between_2_day_string(start_day = None, end_day = None):
    
    start_date = datetime.datetime.strptime(start_day,config.KANDBOX_DATE_FORMAT)  
    end_date = datetime.datetime.strptime(end_day,config.KANDBOX_DATE_FORMAT) 

    return (end_date - start_date).days
