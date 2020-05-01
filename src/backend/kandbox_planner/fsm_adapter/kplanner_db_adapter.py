import datetime
import pandas as pd
import numpy as np  
import json
from datetime import datetime, timedelta

MAX_CONFLICT_LEVEL = 2

# import kandbox_planner.config as config
from sqlalchemy import create_engine

import kandbox_planner.config as config
import kandbox_planner.util.planner_date_util  as date_util

# from kpweb.kpdata.models import Game

# SQLALCHEMY_DATABASE_URI = 'postgresql://odoo:odoo@localhost:5432/kpweb'  # config.DATABASES['default']
'''

db_dict = config.DATABASES["default"]

engine_name = db_dict['ENGINE'].split('.')[-1]
if len(engine_name_list) > 1:
    engine_name = engine_name_list[3]
else:
    engine_name

SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(engine_name,
    db_dict['USER'],
    db_dict['PASSWORD'],
    db_dict['HOST'],
    db_dict['PORT'],
    db_dict['NAME']
    )
local_engine =  create_engine(  SQLALCHEMY_DATABASE_URI ) 

'''

# print('trying db:',  config.DATABASE_URI)
local_engine =  create_engine(  config.DATABASE_URI ) 
cnx = local_engine.connect().execution_options(autocommit=True)
#print('SQLALCHEMY_DATABASE_URI',SQLALCHEMY_DATABASE_URI)

# from django.db import connection

# https://pypi.org/project/holidays/#description
import holidays
# KANDBOX_DATE_FORMAT = "%Y%m%d"
class KPlannerDBAdapter:
    def __init__(self):      
        # Create your connection.
        # TODO: use same config.
        # 'postgresql://odoo:odoo@localhost:5432/kp lanner_riusa')
        self.cnx =  cnx
         
 
    def read_sql(self, sql):  
       return self.__convert_df_datetime_to_day_minutes ( pd.read_sql(sql=sql, con = self.cnx) )


    
    def loaded_historical_location_features(self):  
        job_location_w_df  = pd.read_sql(sql = '''
                select f.*
                from   kpdata_location_job_history_features f 
        ''', con=self.cnx)  

        w,d = self.load_transformed_workers(start_day = '20190204') # , nbr_days = 7

        loc_feature_dict = {}
        for index, f in job_location_w_df.iterrows():

            worker_bitmap = [ 0 for _ in self.workers_id_dict.keys()]
            worker_count_dict = json.loads(f['job_historical_worker_service_dict'])
            # TODO : Why Do i need "int()"
            for worker_count in worker_count_dict: # .keys():
                worker_bitmap[  self.workers_id_dict[ worker_count[0]   ]  ]  = worker_count[1]  
            
            loc_feature_dict[f['location_code']] = {
                'job_count': f['job_count'], 
                'avg_actual_start_minutes': f['avg_actual_start_minutes'], 
                'avg_days_delay': f['avg_days_delay'], 
                'stddev_days_delay': f['stddev_days_delay'],  
                'job_historical_worker_service_dict':worker_count_dict,
                'history_job_worker_count': worker_bitmap 
            }
        self.loc_feature_dict = loc_feature_dict
        return loc_feature_dict

    def load_worker_status_df(self, game_code = None, worker_list= None):  
        if len(worker_list) > 0:
            w_list = worker_list.split(',')
            if len(w_list) > 1:
                w_str = "'" + "','".join(w_list) + "'"
            else:
                w_str = "'" +  w_list[0] + "'"
            query = '''
                    SELECT *
                    FROM kpdata_workerstatus w  
                    where w.game_code = '{}' and w.worker_code in ({})
                    order by w.worker_code'''.format(game_code,w_str)
            
        else:
            query = '''
                    SELECT *
                    FROM kpdata_workerstatus w  
                    where w.game_code = '{}' 
                    order by w.worker_code'''.format(game_code)
        # print(query)
        k_workers = pd.read_sql_query(query,self.cnx ) 
        return k_workers 



    def load_workers_original_df(self, worker_list= ''):   # start_day = '20191101', end_day =  '20191201',
        if len(worker_list) > 0:
            w_list = worker_list.split(',')
            if len(w_list) > 1:
                w_str = "'" + "','".join(w_list) + "'"
            else:
                w_str = "'" +  w_list[0] + "'"
            query = '''
                    SELECT *
                    FROM kpdata_worker w  
                    where w.worker_code in ({}) 
                    order by w.worker_code ''' .format( w_str) #  and active=1
            
        else:
            query = '''
                    SELECT *
                    FROM kpdata_worker w  
                    order by w.worker_code'''
                    # where active=1
        # print(query)
        k_workers = pd.read_sql_query(query, self.cnx) 
        return k_workers


    def _convert_df_day_minutes_to_datetime(self, jobs_df = None, drop_original=True): #  String
        all_columns = jobs_df.columns

        jobs_df = jobs_df.copy()
        if 'requested_start_minutes' in all_columns:
            jobs_df['requested_start_datetime'] = jobs_df.apply(
                lambda x: datetime.strptime( str(x['requested_start_day']), config.KANDBOX_DATE_FORMAT) +\
                    timedelta(minutes = x['requested_start_minutes'])  , axis=1 )
            if drop_original:
                jobs_df.drop(columns=['requested_start_minutes', 'requested_start_day'],inplace=True)
        if 'scheduled_start_minutes' in all_columns:
            jobs_df['scheduled_start_datetime'] = jobs_df.apply(
                lambda x: datetime.strptime( str(x['scheduled_start_day']), config.KANDBOX_DATE_FORMAT) +\
                    timedelta(minutes = x['scheduled_start_minutes'])  , axis=1 )
            if drop_original:
                jobs_df.drop(columns=['scheduled_start_minutes', 'scheduled_start_day'],inplace=True)
        if ('actual_start_minutes' in all_columns) and ('actual_start_day' in all_columns):
            jobs_df['actual_start_datetime'] = jobs_df.apply(
                lambda x: datetime.strptime( str(x['actual_start_day']), config.KANDBOX_DATE_FORMAT) +\
                    timedelta(minutes = x['actual_start_minutes'])  , axis=1 )
            if drop_original:
                jobs_df.drop(columns=['actual_start_minutes', 'actual_start_day'],inplace=True)
        return jobs_df

    def convert_df_datetime_to_day_minutes(self, jobs_df = None): #  String
        return self.__convert_df_datetime_to_day_minutes(jobs_df)

    def __convert_df_datetime_to_day_minutes(self, jobs_df = None): #  String
        all_columns = jobs_df.columns

        # print(all_columns)
        jobs_row_count = jobs_df.count().max()
        # print("df row count: ", jobs_df.count().max())
        if ( 'requested_start_datetime' in all_columns ):
            # if (jobs_df['requested_start_datetime'].count().max() == jobs_row_count) & (jobs_row_count > 0):
            if (jobs_df['requested_start_datetime'].count().max()  > 0):
                jobs_df['requested_start_day'] = jobs_df.apply(
                    lambda x: datetime.strftime( x['requested_start_datetime'], config.KANDBOX_DATE_FORMAT)  , axis=1 )
                jobs_df['requested_start_minutes'] = jobs_df.apply(
                    lambda x: date_util.strp_minutes_from_datetime ( x['requested_start_datetime']) , axis=1 )

        if ('scheduled_start_datetime' in all_columns):
            # if (jobs_df['scheduled_start_datetime'].count().max()== jobs_row_count) & (jobs_row_count > 0):
            if (jobs_df['scheduled_start_datetime'].count().max()   > 0):
                jobs_df['scheduled_start_day'] = jobs_df.apply(
                    lambda x: datetime.strftime( x['scheduled_start_datetime'], config.KANDBOX_DATE_FORMAT)  , axis=1 )
                jobs_df['scheduled_start_minutes'] = jobs_df.apply(
                    lambda x: date_util.strp_minutes_from_datetime ( x['scheduled_start_datetime']) , axis=1 )

        if ('actual_start_datetime' in all_columns) :
            # if (jobs_df['actual_start_datetime'].count().max() ==  jobs_row_count) & (jobs_row_count > 0):
            if (jobs_df['actual_start_datetime'].count().max()  > 0):
                jobs_df['actual_start_day'] = jobs_df.apply(
                    lambda x: datetime.strftime( x['actual_start_datetime'], config.KANDBOX_DATE_FORMAT)  , axis=1 )
                jobs_df['actual_start_minutes'] = jobs_df.apply(
                    lambda x: date_util.strp_minutes_from_datetime ( x['actual_start_datetime']) , axis=1 )
        #print(jobs_df.columns)
        return jobs_df


    def load_workerabsence_as_jobs_df(self, start_day = None, end_day = None, game_code = None): #  String
        '''
(start_datetime, end_datetime, last_update_by, last_update_game_code, effective_from_date, 
worker_code, "EmployeeCode", 
"EventCode", "WorkRestInd", absence_code, absence_type, geo_latitude, geo_longitude)

            
            SELECT job_code, job_type, location_code, geo_longitude, geo_latitude, planner_code,
                kjs.planning_status, 
                kjs.scheduled_start_datetime,
                kjs.scheduled_travel_minutes_before , 
                kjs.scheduled_travel_minutes_after,
                kjs.scheduled_travel_prev_code , 
                kjs.scheduled_duration_minutes, kjs.scheduled_worker_code, kjs.conflict_level


        '''
        if game_code is None:
            query_sql = '''
                SELECT * 
                FROM   kpdata_workerabsence 
                where  start_datetime >= '{}'
                    and start_datetime < '{}'
                order by  worker_code, start_datetime 
                '''.format( date_util.transform_kandbox_day_2_postgres_datetime(start_day),  
                                    date_util.transform_kandbox_day_2_postgres_datetime(end_day))
        else:
            query_sql = '''
                SELECT * 
                FROM   kpdata_workerabsencestatus
                where  start_datetime >= '{}'
                    and start_datetime < '{}'
                    and game_code = '{}'
                order by  worker_code, start_datetime 
                '''.format( date_util.transform_kandbox_day_2_postgres_datetime(start_day),  
                            date_util.transform_kandbox_day_2_postgres_datetime(end_day),
                            game_code
                            )

        jobs_df  = self.read_sql(query_sql)
        if jobs_df.count().max() < 1:
            return None
        jobs_df['requested_skills']= '{}' 
        jobs_df['job_type']= jobs_df.apply(lambda x:  'EVT_{}_{}_0_0_N'.format(  x['absence_type']  , x['EventCode']   )  , axis=1 )   
        jobs_df['job_code']= jobs_df.apply(lambda x:  'EVT_{}'.format(  x['absence_code']  )  , axis=1 )   
        jobs_df['scheduled_duration_minutes']= jobs_df.apply(lambda x:   (x['end_datetime'] - x['start_datetime']) .seconds//60 , axis=1 )   
        jobs_df.rename(columns={
            'start_datetime': 'scheduled_start_datetime', 
            'worker_code': 'scheduled_worker_code',
            }, inplace=True )
        jobs_df['planning_status']= 'P' # ~'E'
        jobs_df['scheduled_share_status']= 'N' # ~'E'
        



        jobs_df[['requested_worker_code','requested_start_datetime', 'requested_duration_minutes' ]] = jobs_df.apply( \
            lambda x: [x['scheduled_worker_code'], x['scheduled_start_datetime'], x['scheduled_duration_minutes'] ] , \
            axis=1, result_type='expand' )

        jobs_df[['actual_worker_code','actual_start_datetime', 'actual_duration_minutes']] = jobs_df.apply( \
            lambda x: [x['scheduled_worker_code'], x['scheduled_start_datetime'], x['scheduled_duration_minutes']] , \
            axis=1, result_type='expand' )

        jobs_df[['scheduled_travel_minutes_before','scheduled_travel_minutes_after', 'scheduled_travel_prev_code', 'conflict_level'
                ]] = jobs_df.apply(lambda x: [0,0, '_NONE',0], axis=1, result_type='expand' )




        return self.__convert_df_datetime_to_day_minutes(jobs_df)



    def load_jobs_original_df(self, start_day = None, end_day =  None ): #  String '20191101' '20191201'


        query_sql = '''
            SELECT 'orig' as  planner_code, kj.* 
            FROM   kpdata_job kj
            where  kj.requested_start_datetime >= '{}'
                and kj.requested_start_datetime < '{}'
            order by  scheduled_worker_code, scheduled_start_datetime 
            '''.format( date_util.transform_kandbox_day_2_postgres_datetime(start_day),  
                                date_util.transform_kandbox_day_2_postgres_datetime(end_day))
        jobs_df  = self.read_sql(query_sql)

        return self.__convert_df_datetime_to_day_minutes(jobs_df)



    def load_jobs_original_with_absence_df(self, start_day = None, end_day =  None ): #  String '20191101' '20191201'
        start_date = datetime.strptime(start_day, config.KANDBOX_DATE_FORMAT)
        '''
                    kj.requested_start_minutes,
                    kj.requested_duration_minutes,
                    kj.scheduled_start_minutes  as actual_start_minutes, 
        '''
        query_sql = '''
                SELECT kj.job_code, kj.job_type, kj.geo_longitude, kj.geo_latitude, kj.location_code,
                    kj.requested_worker_code,
                    kj.requested_start_datetime, 
                    kj.requested_duration_minutes,
                    kj.requested_skills,
                    kj.planning_status,
                    kj.preferred_day_flag  , 
                    kj.requested_start_min_day  , 
                    kj.requested_start_max_day  , 
                    kj.preferred_minutes_minmax_flag, 
                    kj.mandatory_minutes_minmax_flag ,
                    kj.requested_start_min_minutes  , 
                    kj.requested_start_max_minutes  , 
                    kj.conflict_level,

                    kj.scheduled_worker_code ,
                    kj.scheduled_start_datetime , 
                    kj.scheduled_duration_minutes ,
                    kj.scheduled_share_status , 
                    scheduled_travel_minutes_before,
                    scheduled_travel_minutes_after,
                    scheduled_travel_prev_code, 

                    kj.scheduled_worker_code as actual_worker_code ,
                    kj.scheduled_start_datetime as actual_start_datetime, 
                    kj.scheduled_duration_minutes  as actual_duration_minutes 
                FROM  kpdata_job kj
                where   kj.requested_start_datetime >= '{}'
                    and kj.requested_start_datetime < '{}'
                order by  kj.scheduled_worker_code, kj.scheduled_start_datetime 
                    '''.format( datetime.strftime(start_date, config.KANDBOX_DATETIME_FORMAT_WITH_MS),  \
                                datetime.strftime(datetime.strptime(end_day, config.KANDBOX_DATE_FORMAT) , config.KANDBOX_DATETIME_FORMAT_WITH_MS))
        # print(query_sql)
        jobs_df = self.__convert_df_datetime_to_day_minutes ( pd.read_sql_query(query_sql, self.cnx)  )

        absence_df = self.load_workerabsence_as_jobs_df(start_day = start_day, end_day = end_day, game_code=None)
        # 'effective_from_date',
        if absence_df is not None:
            '''
            cols =['scheduled_start_day',  'scheduled_start_minutes',  'scheduled_worker_code',
                    'geo_latitude', 'geo_longitude', 'job_type', 'job_code',
                    'scheduled_duration_minutes', 'planning_status',
                    'scheduled_travel_minutes_before', 'scheduled_travel_minutes_after',
                    'scheduled_travel_prev_code', 'conflict_level'] 
            '''
            absence_d = absence_df.astype(dtype= {
                "scheduled_duration_minutes":"int64",
                "scheduled_travel_minutes_before":"int64",
                "scheduled_travel_minutes_after":"int64"}
                )
            job_d = jobs_df.astype(dtype= {
                "scheduled_duration_minutes":"int64",
                "scheduled_travel_minutes_before":"int64",
                "scheduled_travel_minutes_after":"int64"}
                )

            jobs_df = pd.concat([absence_d, job_d])
        jobs_df['changed_flag'] = 0
        return jobs_df



    def load_job_status_df(self, planner_code= None, start_day = None, end_day = None, game_code = None, order_by=None): #  

        if game_code is None:
            game_code = '%%'


        if order_by is None:
            order_by = ' scheduled_worker_code, scheduled_start_datetime '

        query_sql = '''
                SELECT kj.job_code, kj.job_type, kj.geo_longitude, kj.geo_latitude, kj.location_code,
                    kj.requested_worker_code,
                    kj.requested_start_datetime,
                    kj.requested_duration_minutes,
                    kj.requested_skills,
                    kj.preferred_day_flag  , 
                    kj.requested_start_min_day  , 
                    kj.requested_start_max_day  , 
                    kj.preferred_minutes_minmax_flag  , 
                    kj.mandatory_minutes_minmax_flag,
                    kj.requested_start_min_minutes  , 
                    kj.requested_start_max_minutes  ,  
                    kjs.planning_status,
                    kjs.planner_code, 
                    kjs.scheduled_share_status , 
                    kjs.scheduled_start_datetime , 
                    kjs.scheduled_worker_code ,
                    kjs.scheduled_travel_minutes_before , 
                kjs.scheduled_travel_minutes_after,
                kjs.scheduled_travel_prev_code ,  
                    kjs.scheduled_duration_minutes ,
                    kjs.scheduled_start_datetime as actual_start_datetime, 
                    kjs.scheduled_worker_code as actual_worker_code,
                    kjs.scheduled_travel_minutes_before as scheduled_travel_minutes,
                    kjs.scheduled_duration_minutes  as actual_duration_minutes ,
                    kjs.conflict_level,
                    kjs.changed_flag
                FROM kpdata_jobstatus kjs, kpdata_job kj
                where kj.job_code = kjs.job_code
                    and kjs.planner_code = '{}'
                    and kjs.game_code like '{}'
                    and kjs.scheduled_share_status != 'D'
                    and kjs.scheduled_start_datetime >= '{}'
                    and kjs.scheduled_start_datetime < '{}'
                order by  kjs.scheduled_worker_code, kjs.scheduled_start_datetime 
                    '''.format(planner_code, game_code,
                                date_util.transform_kandbox_day_2_postgres_datetime(start_day),  
                                date_util.transform_kandbox_day_2_postgres_datetime(end_day)
                            )

        #  kjs.scheduled_start_day, kjs.scheduled_start_minutes, 
        '''
        query_sql = 
            SELECT job_code, job_type, location_code, geo_longitude, geo_latitude, planner_code,
                kjs.planning_status, 
                kjs.requested_worker_code, 
                kjs.requested_start_datetime,
                kjs.requested_duration_minutes, 
                kjs.scheduled_worker_code, 
                kjs.scheduled_share_status , 
                kjs.scheduled_start_datetime,
                kjs.scheduled_travel_minutes_before , 
                kjs.scheduled_travel_minutes_after,
                kjs.scheduled_travel_prev_code , 
                kjs.scheduled_duration_minutes, 
                kjs.scheduled_start_datetime as actual_start_datetime, 
                kjs.scheduled_worker_code as actual_worker_code ,
                kjs.scheduled_duration_minutes  as actual_duration_minutes,
                kjs.conflict_level
            FROM kpdata_jobstatus kjs 
            where  kjs.game_code like '{}'
                and kjs.planner_code = '{}'
                and kjs.scheduled_start_datetime >= '{}'
                and kjs.scheduled_start_datetime < '{}'
            order by  {} 
                .format(game_code, planner_code, 
                            date_util.transform_kandbox_day_2_postgres_datetime(start_day),  
                            date_util.transform_kandbox_day_2_postgres_datetime(end_day), 
                            order_by)
            '''
        # order by  
        # print(query_sql)
        jobs_df  = self.read_sql(query_sql)

        jobs_df = self.__convert_df_datetime_to_day_minutes(jobs_df)

        if game_code != '%%':
            # game_code = '%%'

            absence_df = self.load_workerabsence_as_jobs_df(start_day = start_day, end_day = end_day, game_code=game_code)
            absence_df['changed_flag'] = 0
            jobs_df["changed_flag" ] = jobs_df["changed_flag" ].fillna(0)
            # 'effective_from_date',
            if absence_df is not None: 
                absence_d = absence_df.astype(dtype= {
                    "scheduled_duration_minutes":"int64",
                    "scheduled_travel_minutes_before":"int64",
                    "scheduled_travel_minutes_after":"int64"}
                    )

                jobs_df['scheduled_duration_minutes']=jobs_df.apply(lambda x:  int( x['scheduled_duration_minutes']  ) if x['scheduled_duration_minutes']  is not None else 0, axis=1 )
                jobs_df['scheduled_travel_minutes_before']=jobs_df.apply(lambda x:  int( x['scheduled_travel_minutes_before']  )  if x['scheduled_travel_minutes_before']  is not None else 0, axis=1 )
                jobs_df['scheduled_travel_minutes_after']=jobs_df.apply(lambda x:  int( x['scheduled_travel_minutes_after']  )  if x['scheduled_travel_minutes_after']  is not None else 0, axis=1 )
                '''
                # jobs_df[["scheduled_duration_minutes","scheduled_travel_minutes_before","scheduled_travel_minutes_after"]].fillna('0',inplace=True)
                job_d = jobs_df.astype(dtype= {
                    "scheduled_duration_minutes":"int64",
                    "scheduled_travel_minutes_before":"int64",
                    "scheduled_travel_minutes_after":"int64"}
                    )
                '''
                jobs_df = pd.concat([absence_d, jobs_df])
            
        return jobs_df


    def load_transformed_workers(self,start_day = None):  
    #        return self.load_workers_original(start_day)
    #def load_workers_original(self,start_day = '20191101'):  
        query = '''
                SELECT *
                FROM kpdata_worker w  
                order by w.worker_code'''
        k_workers = pd.read_sql_query(query, self.cnx) 

        start_date = datetime.strptime(start_day, config.KANDBOX_DATE_FORMAT)
        return self._transform_workers(k_workers=k_workers, start_date=start_date)

    def _transform_workers(self,k_workers = None, start_date = None):  
        w=[]
        w_dict = {}
        k_workers = k_workers.reset_index() 
        # 
        # us_holidays = holidays.UnitedStates()
        us_holidays = []


        for index, worker in k_workers.iterrows():
            weekly_working_time_orig = json.loads( worker["weekly_working_minutes"] ) 

            worker_week_day = (start_date.weekday()+1) % 7 

            weekly_working_time = weekly_working_time_orig[worker_week_day:] + weekly_working_time_orig[0:worker_week_day]
            # TODO: Append and repeat later. 
            for day_i in range(len(weekly_working_time)):
                if start_date + timedelta(days=day_i) in us_holidays:
                    weekly_working_time[day_i] = [0, 0]

            w_r = {
                "worker_id": index,
                "worker_index": index,
                "worker_code": worker["worker_code"],
                "active": worker['active'],
                "level": worker["level"],
                "skills": json.loads(worker["skills"]),
                'geo_longitude':worker['geo_longitude'],
                'geo_latitude':worker['geo_latitude'],
                "home_gps": [
                    worker['geo_longitude'],
                    worker['geo_latitude']
                ], 
                "served_gps_gaussian": [
                    0,
                    0,
                    0,
                    0
                ],
                "working_minutes":  weekly_working_time , # 6 times  for _ in range(len(k_worker['result'])) 
                "working_time":  weekly_working_time , # 6 times  for _ in range(len(k_worker['result'])) 
                #TODO Remove time.
                "weekly_max_working_minutes":   0  ,
            }
            w.append(w_r)
            w_dict[worker["worker_code"]] = index

        self.workers_id_dict = w_dict 
        return w, w_dict


    def load_transformed_jobs_current(self, start_day = None, nbr_days = 1 ): # _for_training
        start_date = datetime.strptime(start_day, config.KANDBOX_DATE_FORMAT)

        jobs_df  = self.load_jobs_original_with_absence_df(
            start_day = start_day, 
            end_day = date_util.add_days_2_day_string(k_day=start_day, days=nbr_days)
        )
        return self._transform_jobs (jobs=jobs_df, start_date=start_date)

        '''
                    kj.requested_start_minutes,
                    kj.requested_duration_minutes,
                    kj.scheduled_start_minutes  as actual_start_minutes, 
        '''
        query_sql = '''
                SELECT kj.job_code, kj.job_type, kj.geo_longitude, kj.geo_latitude, kj.location_code,
                    kj.requested_worker_code,
                    kj.requested_start_datetime, 
                    kj.requested_duration_minutes,
                    kj.requested_skills,
                    kj.planning_status,
                    kj.preferred_day_flag  , 
                    kj.requested_start_min_day  , 
                    kj.requested_start_max_day  , 
                    kj.preferred_minutes_minmax_flag, 
                    kj.mandatory_minutes_minmax_flag ,
                    kj.requested_start_min_minutes  , 
                    kj.requested_start_max_minutes  , 
                    kj.scheduled_start_datetime as actual_start_datetime, 
                    kj.scheduled_worker_code as actual_worker_code ,
                    kj.scheduled_duration_minutes  as actual_duration_minutes 
                FROM  kpdata_job kj
                where   kj.requested_start_datetime >= '{}'
                    and kj.requested_start_datetime < '{}'
                order by  kj.scheduled_worker_code, kj.scheduled_start_datetime 
                    '''.format( datetime.strftime(start_date, config.KANDBOX_DATETIME_FORMAT_WITH_MS),  \
                                datetime.strftime(start_date + timedelta(days=nbr_days), config.KANDBOX_DATETIME_FORMAT_WITH_MS))
        # print(query_sql)
        jobs = self.__convert_df_datetime_to_day_minutes ( pd.read_sql_query(query_sql, self.cnx)  )

        return self._transform_jobs (jobs, start_date)

        '''
        '''

    def load_transformed_jobs_from_status(self, workers_id_dict = None, start_day = None, nbr_days = 1, planner_code = 'opti1day'): # _for_training
        #            kj.requested_start_minutes,
        #            kjs.scheduled_start_minutes  as actual_start_minutes, 
        start_date = datetime.strptime(start_day, config.KANDBOX_DATE_FORMAT)

        jobs_df = self.load_job_status_df( planner_code= planner_code, start_day = start_day, end_day =  date_util.add_days_2_day_string(k_day=start_day, days=nbr_days), 
            game_code = None, order_by=None) 

        return self._transform_jobs (jobs=jobs_df, start_date=start_date)

        print('#TODO')
        query_sql = '''
                SELECT kj.job_code, kj.job_type, kj.geo_longitude, kj.geo_latitude, kj.location_code, kjs.planner_code, 
                    kj.requested_worker_code,
                    kj.requested_start_datetime,
                    kj.requested_duration_minutes,
                    kj.requested_skills,
                    kj.planning_status,
                    kj.preferred_day_flag  , 
                    kj.requested_start_min_day  , 
                    kj.requested_start_max_day  , 
                    kj.preferred_minutes_minmax_flag  , 
                    kj.mandatory_minutes_minmax_flag,
                    kj.requested_start_min_minutes  , 
                    kj.requested_start_max_minutes  ,  
                    kjs.scheduled_start_datetime as actual_start_datetime, 
                    kjs.scheduled_worker_code as actual_worker_code,
                    kjs.scheduled_travel_minutes_before as scheduled_travel_minutes,
                    kjs.scheduled_duration_minutes  as actual_duration_minutes 
                FROM kpdata_jobstatus kjs, kpdata_job kj
                where kj.job_code = kjs.job_code
                    and kjs.planner_code = '{}'
                    and kjs.scheduled_start_datetime >= '{}'
                    and kjs.scheduled_start_datetime < '{}'
                order by  kjs.scheduled_worker_code, kjs.scheduled_start_datetime 
                    '''.format(planner_code, 
                                datetime.strftime(start_date, config.KANDBOX_DATETIME_FORMAT_WITH_MS),  \
                                datetime.strftime(start_date + timedelta(days=nbr_days), config.KANDBOX_DATETIME_FORMAT_WITH_MS))

        jobs_from_db = pd.read_sql_query(query_sql, self.cnx)  
        jobs_df = self.__convert_df_datetime_to_day_minutes(jobs_df=jobs_from_db)
        '''
        jobs_df = self.load_jobs_original_with_absence_df(start_day=start_day, 
            end_day=datetime.strftime(start_date + timedelta(days=nbr_days), config.KANDBOX_DATE_FORMAT)
            )
                '''

        return self._transform_jobs (jobs=jobs_df, start_date=start_date)


    def _transform_jobs(self, jobs = None, start_date= None): # _for_training
        # Merge Secondary jobs information into its primary
        
        primary_jobs_dict = {}
        for index, job in jobs.iterrows():  
            #if job['scheduled_share_status'] == 'P':
            #    primary_jobs_dict[job['job_code']] = 
            if job['scheduled_share_status'] == 'S':
                primary_job_code = job['job_code'].split('___')[0]
                if primary_job_code in primary_jobs_dict.keys():
                    primary_jobs_dict[primary_job_code].append(job['scheduled_worker_code'])
                else:
                    primary_jobs_dict[primary_job_code]=[job['scheduled_worker_code']]

        # if not self.loc_feature_dict:
        self.loaded_historical_location_features()
        w = []


        for index, order in jobs.iterrows():  
            # print("transformating: ", index)
            if order['scheduled_share_status'] in ( 'S', 'D'):
                continue
            if (order['planning_status'] in ['C','P']) & (order['scheduled_start_day'] < datetime.strftime(start_date, config.KANDBOX_DATE_FORMAT)):
                # DO NOT Skip those status as ['C','P'], but scheduled to past. 
                pass
                # continue

            if order['scheduled_share_status'] == 'P':
                # order['scheduled_share_count'] = len ( primary_jobs_dict[order['job_code']] ) + 1
                if order['job_code'] in primary_jobs_dict.keys():
                    order['scheduled_related_worker_code'] =  list(set(primary_jobs_dict[order['job_code']]))
                else:
                    order['scheduled_related_worker_code']=[]

            else:
                # order['scheduled_share_count'] = 1
                order['scheduled_related_worker_code'] = []
                

            if np.isnan( order['actual_start_minutes'] ):
                print("job {} at sequence {} has no actual_start_time, and therefore skipped for training.".format(order['job_code'], index) )
                # continue 

            if order['requested_worker_code'] not  in self.workers_id_dict.keys(): # TODO Ignored for now
                print("job {} has invalid requested_worker_code: {}, skipped".format(order['job_code'], order['requested_worker_code']) )
                continue

            if 'actual_worker_code' in order.keys(): # TODO always true
                if order['actual_worker_code'] not  in self.workers_id_dict.keys(): # TODO Ignored for now
                    print("job {} at sequence {} has no actual_worker_code.".format(order['job_code'], index) )
                    continue
                a_worker_id =  self.workers_id_dict[ order['actual_worker_code']  ]  # if (workers_id_dict is not None)   else None 
            else:
                # a_worker_id = -1
                continue
            if order['location_code'] in self.loc_feature_dict.keys():
                job_hist = self.loc_feature_dict[order['location_code']]['history_job_worker_count'] # history_job_worker_count job_worker_service_history

            else:
                job_hist = [0 for _ in range(6)]
                # TODO: should be only for prediction.
                self.loc_feature_dict[order['location_code']] = {}

                self.loc_feature_dict[order['location_code']]['history_job_worker_count'] = job_hist  # job_worker_service_history
                self.loc_feature_dict[order['location_code']]['avg_actual_start_minutes'] = 700
                self.loc_feature_dict[order['location_code']]['avg_days_delay'] = 0
                self.loc_feature_dict[order['location_code']]['stddev_days_delay'] = 3

                #TODO, clean up.
                self.loc_feature_dict[order['location_code']]['job_historical_worker_service_dict'] = [[order['requested_worker_code'],10001]] # json.dumps()

            try: 
                order_skills = json.loads(order["requested_skills"]) # order["requested_skills"]
            except :
                # if not order_skills: 
                print("Warning: Failed to get skills for job {} ".format(order['job_code']) )
                
                order_skills= {}
            '''
            # if (order['preferred_day_flag'] is not None) & (not np.isnan(order['preferred_day_flag'])) else {}
            '''
                
            w.append({
                "duration":  order['requested_duration_minutes']  ,
                # TODO: Unify job and workorder.
                "job_id": order['job_code']  , # "job_seq": 89, order['job_code']
                "job_type": order['job_type']  , # "job_seq": 89, order['job_code']
                "job_code": order['job_code']  , # "job_seq": 89, order['job_code']
                "location_code": order['location_code']  , # "job_seq": 89, order['job_code']
                "geo_longitude": order['geo_longitude']  , # "job_seq": 89, order['job_code']
                "geo_latitude": order['geo_latitude']  , # "job_seq": 89, order['job_code']
                "requested_skills": order_skills ,
                "planning_status":  order['planning_status'], 

                "tolerated_day_flag":  1 if order['preferred_day_flag'] else 0 , 
                "tolerated_day_min": order['requested_start_min_day']  if order['preferred_day_flag']== 1 else 0, 
                "tolerated_day_max": order['requested_start_max_day']   if order['preferred_day_flag']== 1 else 0, 
                "preferred_time_flag":   1 if  order['preferred_minutes_minmax_flag'] == 1 else 0, 
                "mandatory_minutes_minmax_flag":   1 if  order['mandatory_minutes_minmax_flag'] == 1 else 0, 
                # "preferred_minutes_minmax_flag":   1 if  order['preferred_minutes_minmax_flag'] == 1 else 0, 
                #TODO 
                "preferred_time_min_minutes":  order['requested_start_min_minutes'] if order['preferred_minutes_minmax_flag']== 1 else 0, 
                "preferred_time_max_minutes":  order['requested_start_max_minutes'] if order['preferred_minutes_minmax_flag']== 1 else 0, 
                #"preferred_time_min_minutes":    0, 
                #"preferred_time_max_minutes":   0, 
                "requested_start_min_minutes":  order['requested_start_min_minutes'], 
                "requested_start_max_minutes":  order['requested_start_max_minutes'], 

                "job_gps": [
                    order['geo_longitude'],
                    order['geo_latitude']
                ],
                "history_job_worker_count": job_hist,
                "job_historical_worker_service_dict": self.loc_feature_dict[order['location_code']]['job_historical_worker_service_dict'],  # json.loads(  )
                

                "avg_actual_start_minutes":  self.loc_feature_dict[order['location_code']]['avg_actual_start_minutes'], 
                "avg_days_delay": self.loc_feature_dict[order['location_code']]['avg_days_delay'],
                "stddev_days_delay":  self.loc_feature_dict[order['location_code']]['stddev_days_delay'],  

                # "expected_job_day": (datetime.strptime(order['requested_start_day'], config.KANDBOX_DATE_FORMAT).date() - start_date ).days,   
                "requested_worker_code":  order['requested_worker_code'] , # if (self.workers_id_dict is not None)   else None ,
                "requested_start_minutes": order['requested_start_minutes'] ,
                "requested_start_day":  order['requested_start_day'] , 
                "requested_start_day_sequence": (datetime.strptime(order['requested_start_day'], config.KANDBOX_DATE_FORMAT).date() - start_date.date() ).days,   
                "requested_duration_minutes":  order['requested_duration_minutes'], # TODO remove plural

                "actual_worker_code": order['actual_worker_code'] ,
                "actual_job_day": (datetime.strptime(order['actual_start_day'], config.KANDBOX_DATE_FORMAT).date() - start_date.date() ).days,
                "actual_start_minutes":  order['actual_start_minutes'], # TODO remove plural
                "actual_duration_minutes":  order['actual_duration_minutes'], # TODO remove plural
                "changed_flag" :0,
                'scheduled_share_status' : order['scheduled_share_status'] ,
                'scheduled_related_worker_code' : order['scheduled_related_worker_code'] ,

                "requested_worker_index":  self.workers_id_dict[ order['requested_worker_code']  ] , # if (self.workers_id_dict is not None)   else None ,
                "actual_worker_index": self.workers_id_dict[ order['actual_worker_code']  ] ,
                # "actual_duration_minutes": order['actual_duration_minutes']  , 
            } )

        return w 




    def save_workerstatus(self, worker_df, game_info):  
        worker_df['planner_code'] = game_info['planner_code']
        worker_df['game_code'] = game_info['game_code']
        worker_df.to_sql(name = 'kpdata_workerstatus' , 
               con=self.cnx, schema=None, if_exists='append', index=False )
        # self._upate_current_workers_from_batch(worker_df, game_info=game_info)

    def _upate_current_workers_from_batch(self, workers_df, game_info):  

        worker_upsert_query_template = '''
            INSERT INTO kpdata_worker
                   (worker_code, geo_longitude, geo_latitude, weekly_working_minutes, max_conflict_level,
                    last_update_by, effective_from_date , active, skills)
                values ('{0}', {1},{2},'{3}',
                     {4},  '{5}',   Now() ,1, '{6}'  )
                ON CONFLICT (worker_code)  DO
                UPDATE
                SET geo_longitude = {1} , geo_latitude = {2}
                  , weekly_working_minutes = '{3}' , max_conflict_level = {4}
                  , last_update_by = '{5}'
                  , effective_from_date = Now()
                  , skills = '{6}'
                ''' 

        for index, w in workers_df.iterrows():  
            w_upsert_query = worker_upsert_query_template.format(  
                  w['worker_code']
                 ,w['geo_longitude']
                 ,w['geo_latitude']
                 ,w['weekly_working_minutes']
                 ,w['max_conflict_level']
                 ,game_info['planner_code']
                 ,w['skills']
            )
             
            self.cnx.execute(w_upsert_query)

    def _reload_current_workers_by_batch(self, workers_df, game_info):  
        query = '''
                SELECT *
                FROM kpdata_worker w   ''' 
        orig_jobs_df = pd.read_sql_query(query, self.cnx) 

        new_jobs_df_only  = pd.merge(
            orig_jobs_df['worker_code'], workers_df, 
            how='outer', on='worker_code', indicator=True, suffixes=('_orig','')) .query(
                '_merge == "right_only"') 


        new_jobs_df_and_current_joined  = pd.merge(
            orig_jobs_df['worker_code'], workers_df, 
            how='inner', on='worker_code', indicator=True, suffixes=('_orig','')) 


        existing_jobs_df_only = pd.merge(
            orig_jobs_df, workers_df['worker_code'], 
            how='outer', on='worker_code', indicator=True, suffixes=('','_new')).query(
                '_merge == "left_only"') 
        # https://stackoverflow.com/questions/34506112/strip-timezone-info-in-pandas
        #existing_jobs_df_only['scheduled_start_datetime'] = existing_jobs_df_only['scheduled_start_datetime'].astype(str).str[:-6]
        #existing_jobs_df_only['requested_start_datetime'] = existing_jobs_df_only['requested_start_datetime'].astype(str).str[:-6]
        all_columns = ['name', 'geo_longitude', 'geo_latitude', 'active', #  'lunch_break_minutes',  'level', 'skills', 'last_update_by', 'last_update_game_code', 'effective_from_date',
        'max_conflict_level', 'weekly_working_minutes',
        'weekly_max_working_minutes',
         'Branch', 'Business',
        'CanPrimaryServing', 'Country', 'CustomerTypeRequirement',
        'EmployeeCode', 'MaxOvertimePerDay', 'MaxOvertimePerWeek',
        'NationalKeyAccountInd', 'PermanentPairForSecondaryServing',
        'ProductCodeRequirement', 'StartEndGPS', 'VehicleClass', 'worker_code', 'skills']

        # [all_columns] [all_columns]]
        
        # new_jobs =   pd.concat( [existing_jobs_df_only, new_jobs_df_and_current], sort=False).copy()
        # TODO, to update
        new_jobs = new_jobs_df_only[all_columns].copy() 
        # new_jobs.drop(columns =['_merge','game_code'], inplace = True)
        # self.cnx.execute( '''truncate table kpdata_worker''' )

        new_jobs.drop_duplicates(subset ="worker_code", 
                     keep = 'first', inplace = True)
        
        new_jobs.to_sql(name = 'kpdata_worker' , 
               con=self.cnx, schema=None, if_exists='append', index=False )


        batch_workers = workers_df[all_columns].copy()
        batch_workers['planner_code'] = game_info['planner_code']
        batch_workers['game_code'] = game_info['game_code']
        
        batch_workers.to_sql(name = 'kpdata_workerstatus' , 
               con=self.cnx, schema=None, if_exists='append', index=False )

        batch_workers['planner_code'] = 'rl_heur'
        batch_workers['game_code'] = game_info['game_code'][:-1]+'rl'
        
        batch_workers.to_sql(name = 'kpdata_workerstatus' , 
               con=self.cnx, schema=None, if_exists='append', index=False )




    def _reload_current_jobs_by_batch(self, jobs_df=None, game_info=None, update_current = True):  
        # This one load into pandas, merge and replace in batch
        query = '''
                SELECT *
                FROM kpdata_job w   '''
                #where requested_start_datetime >= '{}'
                #'''.format(config.KANDBOX_JOB_MINIMUM_START_DAY)
        orig_jobs_df = pd.read_sql_query(query, self.cnx) 

        #TODO, remove The_Company columns
        input_visit_columns  =[ "requested_skills",
            'scheduled_worker_code',  'planning_status', 'scheduled_share_status', 'requested_worker_code',  'requested_duration_minutes', 'scheduled_duration_minutes', 'location_code', 'geo_longitude', 'geo_latitude', 'job_type', 'job_code', 'scheduled_travel_minutes_before', 'scheduled_travel_minutes_after', 'scheduled_travel_prev_code', 'scheduled_travel_next_code', 'requested_start_datetime', 'scheduled_start_datetime'
        ]


        real_input_cols = [x for x in input_visit_columns if x in jobs_df.columns]

        new_jobs_df_only = pd.merge(
            orig_jobs_df['job_code'], jobs_df[real_input_cols], 
            how='outer', on='job_code', indicator=True, suffixes=('_orig','')).query(
                '_merge == "right_only"')


        
        new_jobs =  new_jobs_df_only.copy() 
        new_jobs.drop(columns =['_merge' ], inplace = True) # ,'error_message','game_code','planner_code' ,'error_message'
        # self.cnx.execute( '''truncate table kpdata_job''' )
        # self.cnx.execute( '''delete from kpdata_job''' )
        new_jobs.to_sql(name = 'kpdata_job' , 
               con=self.cnx, schema=None, if_exists='append', index=False, method=None )




        existing_jobs_df_only = pd.merge(
            orig_jobs_df, jobs_df['job_code'],  # ['job_code']
            how='outer', on='job_code', indicator=True, suffixes=('','_new')).query(
                '_merge == "left_only"')

        delete_sql = '''delete from kpdata_job where job_code = '{}'  '''
        # ~delete_sql = '''update kpdata_job set active = 0, last_update_game_code = '{}' where job_code = '{}'  '''
        for index, job in existing_jobs_df_only.iterrows():  
            # print(datetime.now(), 'Job ({}) is no longer in batch input ({}) and is being deleted ... '.format(job['job_code'],game_info['game_code'] ))
            try:
                pass
                # TODO: The_Company specifics
                # self.cnx.execute(delete_sql.format( job['job_code'])) # game_info['game_code'] ,
            except Exception as err:
                print(err)




        existing_jobs_df_only['game_code'] = game_info['game_code']
        existing_jobs_df_only['planner_code'] = game_info['planner_code']
        existing_jobs_df_only ['operation'] = 'D'
        job_history_track_columns_candidate = ['job_code','planning_status', 'game_code', 'planner_code','operation',
            'scheduled_share_status', 'scheduled_start_datetime', 'scheduled_duration_minutes','scheduled_worker_code',
            'scheduled_travel_minutes_before',  'scheduled_travel_prev_code'
            ]
        # 2020-04-10 08:28:08 , not tracking skills changes yet
        # ,'requested_skills'

        existing_jobs_df_only[job_history_track_columns_candidate].to_sql(name = 'kpdata_job_change_history' , 
               con=self.cnx, schema=None, if_exists='append', index=False )


        job_history_track_columns = [x for x in job_history_track_columns_candidate if (x in jobs_df.columns) ]


        # [job_history_track_columns]
        d = pd.merge(orig_jobs_df, 
                     jobs_df , 
                                    how='inner',  
                                    suffixes = ('_orig', ''),
                    left_on=   [ 'job_code' ], 
                    right_on = [ 'job_code' ]) 

        if d.count().max() < 1:
            print(datetime.now(), "_reload_current_jobs_by_batch: No updated rows, finished!", game_info['game_code'])
            return
        d['scheduled_start_datetime_orig'].fillna(datetime.now(),inplace=True)
        # d['scheduled_start_datetime_orig'] = d['scheduled_start_datetime_orig'].dt.tz_localize(None)
        #d['requested_start_datetime'] = d['requested_start_datetime'].dt.tz_localize(None)


        d['scheduled_start_datetime_orig__STR'] = d.apply(lambda x:  datetime.strftime (  x['scheduled_start_datetime_orig'], "%Y-%m-%d %H:%M:%S" ) , axis=1 )
        d['scheduled_start_datetime__STR'] = d.apply(lambda x:  datetime.strftime (  x['scheduled_start_datetime'], "%Y-%m-%d %H:%M:%S" ) , axis=1 )


        # d['scheduled_start_datetime'] = d['scheduled_start_datetime'].dt.tz_localize(None)

        d_changed = d[
            (d['planning_status_orig']!=d['planning_status']) | \
            (d['scheduled_start_datetime_orig__STR']!=d['scheduled_start_datetime__STR']) | \
            (d['scheduled_duration_minutes_orig']!=d['scheduled_duration_minutes']) | \
            (d['scheduled_worker_code_orig']!=d['scheduled_worker_code']) |  \
            (d['scheduled_share_status_orig']!=d['scheduled_share_status']) \
        ]
        # (d['scheduled_related_worker_code_orig']!=d['scheduled_related_worker_code']) \
        if d_changed.count().max() < 1:
            print(datetime.now(), 'No changes to existing jobs are detected from game: ', game_info['game_code'])
            return 

        changed_jobs_df = d_changed[job_history_track_columns].copy()
        changed_jobs_df['game_code'] = game_info['game_code']
        changed_jobs_df['planner_code'] = game_info['planner_code']
        changed_jobs_df['effective_from_date'] = datetime.now()
        changed_jobs_df['operation'] = 'U'


        changed_jobs_df.to_sql(name = 'kpdata_job_change_history' , 
               con=self.cnx, schema=None, if_exists='append', index=False )


        # update inside database in one go. 

        if not update_current:
            print("Skipped updating current jobs after saving update history ...")
            return changed_jobs_df
        
        try:
            self.cnx.execute('''
                    UPDATE kpdata_job b
                    SET scheduled_start_datetime = a.scheduled_start_datetime,
                        planning_status = a.planning_status,
                        scheduled_worker_code = a.scheduled_worker_code , 
                        scheduled_travel_minutes_before = a.scheduled_travel_minutes_before , 
                        scheduled_travel_prev_code = a.scheduled_travel_prev_code ,
                        scheduled_share_status = a.scheduled_share_status ,
                        last_update_by = a.planner_code ,
                        scheduled_related_worker_code = a.scheduled_related_worker_code
                    from public.kpdata_job_change_history a
                    WHERE a.job_code = b.job_code
                        AND a.game_code  = '{}'
                '''.format(game_info['game_code']))
        except Exception as inst:
            print("failed to updated latest job table ...")
            print(inst)
        
        return changed_jobs_df



    def _update_current_jobs_with_history(self, jobs_df, game_info):  
        # y, scheduled_start_minutes
        # This one insert row by row and then update inside database 
        query = '''
                SELECT job_code,  planning_status, conflict_level,
                    scheduled_start_datetime, scheduled_duration_minutes, scheduled_worker_code,
                    requested_start_datetime, requested_duration_minutes,requested_worker_code
                FROM kpdata_job w   '''
                #where requested_start_datetime >= '{}'
                #'''.format(config.KANDBOX_JOB_MINIMUM_START_DAY)
        orig_jobs_df = pd.read_sql_query(query, self.cnx) 

        job_history_track_columns_candidate = ['job_code','planning_status', 'scheduled_related_worker_code',
            'scheduled_start_datetime', 'scheduled_duration_minutes','scheduled_worker_code'
            ]
        
        job_history_track_columns = [item for item in job_history_track_columns_candidate if (item in jobs_df.columns) ]

        # 'conflict_level', 'requested_start_datetime', 'requested_duration_minutes','requested_worker_code'


        new_jobs_df_only = pd.merge(
            orig_jobs_df, jobs_df, 
            how='outer', on='job_code', indicator=True, suffixes=('_orig','')).query(
                '_merge == "right_only"')


        # _with_requested_start 
        job_upsert_query_template= '''
                insert into kpdata_job (
                    job_code, planning_status, last_update_game_code, 
                    conflict_level, scheduled_travel_minutes_before,scheduled_travel_prev_code,
                    last_update_by, location_code, job_type
                    ,geo_longitude ,geo_latitude, effective_from_date
                    ,scheduled_start_datetime  
                    ,scheduled_duration_minutes
                    ,scheduled_worker_code
                    ,requested_start_datetime  
                    ,requested_duration_minutes 
                    ,requested_worker_code 
                    ,scheduled_related_worker_code 
                    ,scheduled_share_status 
                     )
                values ('{0}', '{1}','{2}',
                    '{3}', {4},  '{5}', 
                    '{6}',  '{7}',  '{8}',
                    {9}, {10},Now() 

                    ,'{12}',{13},'{14}'
                    ,'{15}',{16},'{17}','{18}','{19}')
                ''' 
        ''' 
                ON CONFLICT (job_code)  DO
                UPDATE
                SET planning_status = '{1}'  
                    , last_update_game_code = '{2}'
                    , conflict_level = {3}
                    , scheduled_travel_minutes_before = {4} 
                    , scheduled_travel_prev_code = '{5}'
                    , last_update_by = '{6}'
                    , location_code = '{7}'
                    , job_type = '{8}'
                    , geo_longitude={9},geo_latitude ={10} 
                    , effective_from_date = Now()
                    , scheduled_start_datetime = '{12}'
                    , scheduled_duration_minutes = {13}
                    , scheduled_worker_code = '{14}'
                    ,requested_start_datetime ='{15}'
                    ,requested_duration_minutes ={16}
                    ,requested_worker_code ='{17}'
                ''' 
        # print(changed_jobs_df.columns)
        for index, job in new_jobs_df_only.iterrows():  
            # print(type(job['scheduled_related_worker_code']),': ', job['scheduled_related_worker_code'])
            if isinstance(job['scheduled_related_worker_code'], list):
                related_code = ",".join(job['scheduled_related_worker_code'])    # .replace('[','').replace("'",'').replace(']','')
            else:
                related_code = job['scheduled_related_worker_code']

            job_upsert_query = job_upsert_query_template.format(  
                  job['job_code']
                 ,job['planning_status']
                 ,game_info['game_code']
                 ,int(job['conflict_level'])
                 ,job['scheduled_travel_minutes_before'] #4
                 ,job['scheduled_travel_prev_code'] 
                 ,game_info['planner_code']
                 ,job['location_code']
                 ,job['job_type']
                 ,job['geo_longitude'] #9
                 ,job['geo_latitude'] 
                 ,0
                 ,datetime.strftime ( job['scheduled_start_datetime'] , "%Y-%m-%d %H:%M:%S.%f")
                 ,job['scheduled_duration_minutes']
                 ,job['scheduled_worker_code']  
                 ,datetime.strftime ( job['requested_start_datetime'] , "%Y-%m-%d %H:%M:%S.%f") 
                 ,job['requested_duration_minutes']
                 ,job['requested_worker_code']  
                 ,related_code
                 ,job['scheduled_share_status']  
            )                    

            try:
                self.cnx.execute(job_upsert_query)
            except Exception as inst:
                print(inst)

        # orig_jobs_df['scheduled_duration_minutes'] =orig_jobs_df.apply(lambda x:  int(  x['scheduled_duration_minutes']) , axis=1 )

        # planning_note,  to avoid job object  to number.
        if orig_jobs_df.count().max()  < 1:
            orig_jobs_df = orig_jobs_df.astype({'scheduled_duration_minutes': 'int64',   })
        
        # [job_history_track_columns]
        d = pd.merge(orig_jobs_df, 
                     jobs_df , 
                                    how='inner',  
                                    suffixes = ('_orig', ''),
                    left_on=   [ 'job_code' ], 
                    right_on = [ 'job_code' ]) 
        # print(d['scheduled_start_datetime_orig'].dtypes)
        if d.count().max() < 1:
            print("_update_current_jobs_with_history: No updated rows.!")
            return
        d['scheduled_start_datetime_orig'].fillna(datetime.now(),inplace=True)
        # d['scheduled_start_datetime_orig'] = d['scheduled_start_datetime_orig'].dt.tz_localize(None)
        #d['requested_start_datetime'] = d['requested_start_datetime'].dt.tz_localize(None)


        d['scheduled_start_datetime_orig__STR'] = d.apply(lambda x:  datetime.strftime (  x['scheduled_start_datetime_orig'], "%Y-%m-%d %H:%M:%S" ) , axis=1 )
        d['scheduled_start_datetime__STR'] = d.apply(lambda x:  datetime.strftime (  x['scheduled_start_datetime'], "%Y-%m-%d %H:%M:%S" ) , axis=1 )


        # d['scheduled_start_datetime'] = d['scheduled_start_datetime'].dt.tz_localize(None)

        d_changed = d[
            (d['planning_status_orig']!=d['planning_status']) | \
            (d['scheduled_start_datetime_orig__STR']!=d['scheduled_start_datetime__STR']) | \
            (d['scheduled_duration_minutes_orig']!=d['scheduled_duration_minutes']) | \
            (d['scheduled_worker_code_orig']!=d['scheduled_worker_code']) \
        ]

        if d_changed.count().max() < 1:
            print('No changes are detected from game: ', game_info['game_code'])
            return 
        changed_jobs_df = d_changed.copy()
        changed_jobs_df['game_code'] = game_info['game_code']
        changed_jobs_df['planner_code'] = game_info['planner_code']
        changed_jobs_df['effective_from_date'] = datetime.now()

        # TODO update inside database in one go.
        ''' 
                ON CONFLICT (job_code)  DO
                UPDATE
                SET planning_status = '{1}'  
                    , last_update_game_code = '{2}'
                    , conflict_level = {3}
                    , scheduled_travel_minutes_before = {4} 
                    , scheduled_travel_prev_code = '{5}'
                    , last_update_by = '{6}'
                    , location_code = '{7}'
                    , job_type = '{8}'
                    , geo_longitude={9},geo_latitude ={10} 
                    , effective_from_date = Now()

                    , scheduled_start_datetime = '{12}'
                    , scheduled_duration_minutes = {13}
                    , scheduled_worker_code = '{14}'
                    ,requested_start_datetime ='{15}'
                    ,requested_duration_minutes ={16}
                    ,requested_worker_code ='{17}'
                ''' 


        changed_jobs_df = d_changed[job_history_track_columns].copy()
        changed_jobs_df['game_code'] = game_info['game_code']
        changed_jobs_df['planner_code'] = game_info['planner_code']
        changed_jobs_df['effective_from_date'] = datetime.now()


        changed_jobs_df.to_sql(name = 'kpdata_job_change_history' , 
               con=self.cnx, schema=None, if_exists='append', index=False )


        try:
            self.cnx.execute('''
                    UPDATE kpdata_job b
                    SET scheduled_start_datetime = a.scheduled_start_datetime,
                        planning_status = a.planning_status,
                        scheduled_worker_code = a.scheduled_worker_code -- ,  scheduled_share_status = a.scheduled_share_status
                    from public.kpdata_job_change_history a
                    WHERE a.job_code = b.job_code
                        AND a.game_code  = '{}'
                '''.format(game_info['game_code']))
        except Exception as inst:
            print("failed to updated latest job table ...")
            print(inst)



    def update_single_job(self, job):  

        # scheduled_share_status = 'N'
        update_sql = '''
                    UPDATE kpdata_job b
                    SET scheduled_start_datetime = '{0}',
                        planning_status = 'I',
                        scheduled_worker_code = '{1}',
                        last_update_by='{3}',
                        scheduled_travel_prev_code='{4}',
                        scheduled_travel_minutes_before={5} 
                    WHERE job_code = '{2}' 
                '''.format(
                    datetime.strftime( job['scheduled_start_datetime'],  config.KANDBOX_DATETIME_FORMAT_WITH_MS ),
                    job['scheduled_worker_code'],
                    job['job_code'],
                    job['last_update_by'],
                    job['scheduled_travel_prev_code'],
                    job['scheduled_travel_minutes_before']
                    
                    )   
        self.cnx.execute( update_sql )
        return 
        
        try:
            self.cnx.execute( update_sql )
        except Exception as inst:
            print("failed to updated latest job table ...", job)
            print(inst)




    def save_schedued_jobs(self, jobs_df=None, game_info=None, update_current = True):  
        # game_code, planner_code, data_start_day, data_end_day
        # T~his function does:
        #1. calculate confliction.
        #2. update current jobs.

        jobs_df.rename(columns={'scheduled_travel_minutes':'scheduled_travel_minutes_before'}, inplace=True)



        jobs_df = jobs_df.sort_values(['scheduled_worker_code', 'scheduled_start_day','scheduled_start_minutes']).copy()
        # jobs_df.drop(['index' ], axis=1)
        jobs_df['conflict_level'] = 0
        #objs = JobStatus.objects.filter(scheduled_start_day='20190101').order_by('scheduled_worker_code', 'scheduled_start_day','scheduled_start_minutes')
        #for j in objs:

        query = '''
                SELECT *
                FROM kpdata_worker w  
                order by w.worker_code'''
        worker_df = pd.read_sql_query(query, self.cnx) 
        worker_df['max_conflict_level'] = 0
        start_time_day_str = jobs_df['scheduled_start_day'].min()
        if len(start_time_day_str) < 2:
            #TODO: 
            start_time_day_str = '20200202'
        start_time = datetime.strptime(start_time_day_str, config.KANDBOX_DATE_FORMAT)   
        workers_start_end_dict = {}
        workers_dict={} 
        for index, w in worker_df.iterrows():  
            workers_dict[w.worker_code] = {
                'max_conflict_level':0,
                'index':index, 
                }
            workers_start_end_dict [ (w.worker_code,0) ] =  [ start_time, start_time]  

        for index, j in jobs_df.iterrows():  
            curr_worker = j['scheduled_worker_code']
            if curr_worker not in  workers_dict.keys():
                #print('ignored, since not in worker_list, job_code: ',j['job_code'] )
                continue
            scheduled_start_datetime = datetime.strptime( j['scheduled_start_day'], config.KANDBOX_DATE_FORMAT) \
                                     + timedelta (minutes = j['scheduled_start_minutes'] )
            scheduled_end_datetime = scheduled_start_datetime + timedelta (minutes = j['scheduled_duration_minutes'] )     
            conflict_level = 0
            while(conflict_level < MAX_CONFLICT_LEVEL):
                if (curr_worker, conflict_level) in workers_start_end_dict.keys():
                    if scheduled_start_datetime -  ( timedelta (minutes = j['scheduled_travel_minutes_before'])) >= workers_start_end_dict[(curr_worker, conflict_level)][1] :
                        break
                else:
                    workers_start_end_dict[(curr_worker, conflict_level)] = [ start_time, start_time]
                    workers_dict[curr_worker]['max_conflict_level'] = conflict_level
                    break

                conflict_level +=1
            workers_start_end_dict[(curr_worker, conflict_level)] = [scheduled_start_datetime  -  ( timedelta (minutes = j['scheduled_travel_minutes_before'])) ,scheduled_end_datetime]

            jobs_df.at[index,'conflict_level'] = conflict_level

        for index, w in worker_df.iterrows():  
            worker_df.at[index,'max_conflict_level'] = workers_dict[w.worker_code]['max_conflict_level']



        if game_info is not None:
            jobs_df['game_code'] = game_info['game_code']
            jobs_df['planner_code'] = game_info['planner_code']
            worker_df['game_code'] = game_info['game_code']
            worker_df['planner_code'] = game_info['planner_code']
        jobs_df['effective_from_date'] = datetime.now()
        worker_df['effective_from_date'] = datetime.now()
        
        jobs_df_temp = self._convert_df_day_minutes_to_datetime(jobs_df)

        #print("firwstprint", jobs_df.columns)
        # if update_current:
        # self._update_current_jobs_with_history(jobs_df, game_info,)
        changed_jobs_df = self._reload_current_jobs_by_batch(jobs_df_temp, game_info,update_current)

        changed_jobs_df['changed_flag'] = 1


        jobs_df  = pd.merge(
            jobs_df_temp, changed_jobs_df[['job_code','changed_flag']], 
            how='left', on='job_code', indicator=True, suffixes=('','_changed')) 


        jobs_df['changed_flag'].fillna(0,inplace=True)
        # self.save_jobstatus(jobs_df)
        #print("second print", jobs_df.columns)
        
        to_save_columns_candidate = ['job_code', 'job_type', 'planning_status', 'geo_longitude',
            'geo_latitude', 
            'location_code', 
            'scheduled_worker_code', 
            'scheduled_related_worker_code', 'scheduled_share_status',
            'scheduled_duration_minutes',
            'scheduled_travel_minutes_before',
            'scheduled_travel_prev_code',
            'effective_from_date', 'conflict_level', 'game_code', 'planner_code',
            'scheduled_start_datetime', 'error_message']
        to_save_columns = [item for item in to_save_columns_candidate if (item in jobs_df.columns) ]

        optional_columns= [ 'requested_start_datetime', 'requested_duration_minutes', 'requested_worker_code', 
                            'scheduled_travel_minutes_after',  'scheduled_travel_minutes_after']
        
        for a_column in optional_columns:
            if a_column in jobs_df.columns:
                to_save_columns.append(a_column)
        
        to_save_jobs_df = jobs_df[to_save_columns ]

        to_save_jobs_df.to_sql(name = 'kpdata_jobstatus' , 
               con=self.cnx, schema=None, if_exists='append', index=False, method=None )

        self.save_workerstatus(worker_df[['worker_code','game_code', 'name', 'active', 'level', 'skills', 'geo_longitude',
            'geo_latitude', 'weekly_working_minutes', 'max_conflict_level']], game_info) # , 'organization', 'org_level_1', 'org_level_2', 'org_level_3',
        return


    def get_max_game_code(self):   
        insert_query = '''
                select max(game_code)  as game_code from kpdata_game''' 
        result = self.cnx.execute(insert_query)
        for row in result:
            print("game_code:", row['game_code'])
            return row['game_code']

    def get_game_by_code(self, game_code):   
        query = '''
                select * from kpdata_game   where  game_code = '{}'  ''' .format(game_code)
        result = self.cnx.execute(query)
        for row in result:
            # print("game_code:", row['game_code'], "game_config", row['game_config'])
            return {row['game_code']: row['game_config']}
        return None


    def save_game_info(self, game_code = None, planner_code = None, data_start_day = None, data_end_day = None, game_config = None):   
        if game_config is None:
            game_config = json.dumps( {
                'data_start_day': data_start_day,
                'data_end_day':data_end_day
            })
        upsert_query = '''
                insert into kpdata_game (game_code, planner_code, data_start_day, data_end_day, game_config)
                values ('{0}', '{1}','{2}', '{3}', '{4}')
                ON CONFLICT (game_code)  DO
                UPDATE
                SET 
                    planner_code = '{1}'  ,
                    data_start_day = '{2}'  ,
                    game_config = '{4}' 

                '''.format( game_code, planner_code,data_start_day, data_end_day,game_config)   # .replace('"', '\\"')  
        # print(upsert_query)
        self.cnx.execute(upsert_query)
        # self.save_workers_from_orig_for_game(game_code=game_code)
        return 'OK'


    def purge_all_workers_jobs(self, planner_code = 'orig', start_date = '20191101', end_date =  '20191230'):
        print(datetime.now(), "Stared purging all job and worker status")
        self.cnx.execute(
            '''delete from kpdata_jobstatus '''
            )
        self.cnx.execute(
            '''delete from kpdata_job '''
            )
        self.cnx.execute( '''delete from kpdata_workerstatus '''  )
        self.cnx.execute( '''delete from kpdata_worker ''' )
        self.cnx.execute( '''delete from kpdata_workerabsence ''' )  
        self.cnx.execute( '''delete from kpdata_workerabsencestatus ''' ) 
        self.cnx.execute( '''delete from kpdata_game '''  )
        self.cnx.execute( '''delete from kpdata_job_change_history ''' )
        self.cnx.execute( '''delete from kpdata_stats_features_per_worker '''  )
        self.cnx.execute( '''delete from kpdata_stats_features_per_day '''  )
        self.cnx.execute( '''delete from kpdata_location_job_history_features '''  ) # kpdata_location_job_history_features
        print(datetime.now(), "Finished purging all job and worker status")
            
        
            

    def purge_game_job_status(self, game_code = 'orig'):

        sql_jobstatus = '''
            delete from kpdata_jobstatus 
            where game_code = '{}'  
            '''.format(game_code)

        self.cnx.execute(sql_jobstatus)

        self.cnx.execute('''delete from kpdata_game
            where game_code = '{}'  '''.format(game_code))





    def purge_planner_job_status(self, planner_code = 'orig', start_date = None, end_date =  '20191102'):

        if start_date is not None:
            sql_jobstatus = '''
                delete from kpdata_jobstatus 
                where planner_code = '{}' 
                    and scheduled_start_datetime >= '{}'
                    and scheduled_start_datetime < '{}'
                '''.format(planner_code,  
                            date_util.transform_kandbox_day_2_postgres_datetime(start_date),  
                            date_util.transform_kandbox_day_2_postgres_datetime(end_date))
        else:
            sql_jobstatus = '''
                delete from kpdata_jobstatus where planner_code = '{}'
                '''.format(planner_code)

        self.cnx.execute(sql_jobstatus)



        # self.kplanner_db.cnx.commit()
        self.cnx.execute(
            '''
            delete from kpdata_stats_features_per_day where planner_code = '{}'
            '''.format(planner_code))
        self.cnx.execute(
            '''
            delete from kpdata_stats_features_per_worker where planner_code = '{}'
            '''.format(planner_code))

        print("purged job status and stats for planner_code = ", planner_code)


if __name__ == '__main__': 

    # exit(0)
    kdb = KPlannerDBAdapter()
    # workers, workers_id_dict  = kdb.load_workers(start_day = datetime.strptime('20190204',config.KANDBOX_DATE_FORMAT), nbr_days = 7) 
