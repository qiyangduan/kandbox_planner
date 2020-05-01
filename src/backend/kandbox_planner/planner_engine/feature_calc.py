from datetime import datetime, timedelta 
import pandas as pd
import numpy as np 
import json
import glob
import math
import xmlrpc.client

import sys

import kandbox_planner.util.planner_date_util  as date_util
# import kandbox_planner.config as config


from kandbox_planner.fsm_adapter.kplanner_db_adapter import  KPlannerDBAdapter
# kplanner_db = KPlannerDBAdapter() 

from kandbox_planner.util.travel_time  import  HaversineTravelTime

travel_router = HaversineTravelTime(travel_speed=10)

def _assemble_hist(series):
    hist_dict = {}
    
    for index,items in series.iteritems(): 
        if items not in hist_dict.keys():
            hist_dict[items] = 1
        else:
            hist_dict[items] += 1
    return json.dumps(hist_dict)
#sr1111 = pd.Series([11, 21, 8, 8, 65, 8, 32, 5, 5, 24, 11])
#assemble_hist(sr1111)



class KPlannerFeatureCalculator:
    working_dir = None 
    def __init__(self, working_dir = '/xyz/working_area_ri_usa_20191201',connect_dict=None ):      

        self.connect()  
        ##self.get_worker_id_dict() 
        #self.get_order_type_id_dict()
        #self.get_worker_employee_code_dict ( )
    def connect(self):
        self.kplanner_db = KPlannerDBAdapter()

    def add_travel_time_to_orig_job_status(self, planner_code = 'orig', start_day = '20191101', end_day =  '20191230'):
        # Move original jobs to jobstatus and act like "ORIG" fake planner
        
        self.kplanner_db.purge_planner_job_status(planner_code = 'orig', start_date = '20191101', end_date =  '20191230')
        visit_cust  = self.kplanner_db.load_jobs_original_df( 
            start_day = start_day, 
            end_day = end_day
            )

        if visit_cust.count().max() < 1:
            print("add_travel_time_to_orig_job_status: No jobs are found, quitting  .")
            return
        # visit_cust.sort_values(['PlannedEmployeeId','PlannedVisitDate' ,'scheduled_start_minutes' ],ascending=True)
        # visit_cust['planning_status'] =  'I'


        # This is only for production 
        # TODO
        # visit_cust = visit_cust[visit_cust['planning_status'] ==  'I'].copy()
        visit_cust['planner_code'] = 'orig'
        visit_cust['game_code'] = '{}-{}'.format('orig', start_day) 
        visit_cust['effective_from_date'] = datetime.now()

        visit_cust['scheduled_travel_prev_code'] =  visit_cust.job_code.shift(1)
        visit_cust['shifted_gpsx'] =  visit_cust.geo_longitude.shift(1)
        visit_cust['shifted_gpsy'] =  visit_cust.geo_latitude.shift(1)
        #visit_cust['shifted_gpsx'].fillna(0, inplace=True)
        #visit_cust['shifted_gpsy'].fillna(0, inplace=True)
        # print(visit_cust.columns )

        visit_cust['shifted_day'] =  visit_cust.scheduled_start_day.shift(1)
        visit_cust['shifted_minute'] =  visit_cust.scheduled_start_minutes.shift(1)
        visit_cust['shifted_scheduled_duration_minutes'] =  visit_cust.scheduled_duration_minutes.shift(1)
        visit_cust['shifted_location_id_'] =  visit_cust.location_code.shift(1) 

        visit_cust['scheduled_travel_minutes_before'] = visit_cust.apply(lambda x: travel_router.get_travel_minutes_2locations([float(x['geo_longitude']),float(x['geo_latitude'])    ],\
                                                                            [float(x['shifted_gpsx']),float(x['shifted_gpsy'])    ]) , axis=1 )
        visit_cust['scheduled_travel_minutes_before'].fillna(0, inplace=True)
        visit_cust['scheduled_travel_prev_code'].fillna('__HOME', inplace=True)
        visit_cust ['scheduled_duration_minutes']  = visit_cust ['requested_duration_minutes']


        # visit_cust = visit_cust[visit_cust['shifted_day'] == visit_cust['scheduled_start_day']] 
        
        job_df = visit_cust[["job_code", "job_type","game_code", "planning_status", "scheduled_worker_code",'location_code', 'geo_latitude', 'geo_longitude' ,
                "scheduled_start_day", "scheduled_start_minutes", "scheduled_duration_minutes", 'requested_start_day',
                "scheduled_travel_minutes_before","scheduled_travel_prev_code","planner_code","effective_from_date"]]

        curr_game_code = '{}'.format('orig_all')  # datetime.strftime(current_date,config.KANDBOX_DATE_FORMAT) 
        #job_df['game_code'] = curr_game_code
        #job_df['planner_code'] = 'orig'
        game_info = {
            'planner_code': 'orig',
            'game_code': curr_game_code,
        }

        self.kplanner_db.save_schedued_jobs(job_df,game_info)
        self.kplanner_db.save_game_info(game_code=curr_game_code
            , planner_code= 'orig'
            , data_start_day = job_df['scheduled_start_day'].min()
            , data_end_day = job_df['scheduled_start_day'].max()
            )


    def calc_planner_travel_time_statistics(self, planner_code = 'orig', start_day = '20191101', end_day =  '20191230'):
 
        visit_cust  = self.kplanner_db.load_job_status_df(
            planner_code = planner_code,
            start_day = start_day, 
            end_day = end_day
            )
        if visit_cust.count().max() < 1:
            print("no data!")
            return
        # visit_cust.sort_values(['PlannedEmployeeId','PlannedVisitDate' ,'scheduled_start_minutes' ],ascending=True)
        visit_cust['shifted_gpsx'] =  visit_cust.geo_longitude.shift(1)
        visit_cust['shifted_gpsy'] =  visit_cust.geo_latitude.shift(1)
        visit_cust['shifted_day'] =  visit_cust.scheduled_start_day.shift(1)
        visit_cust['shifted_minute'] =  visit_cust.scheduled_start_minutes.shift(1)
        visit_cust['shifted_scheduled_duration_minutes'] =  visit_cust.scheduled_duration_minutes.shift(1)
        visit_cust['shifted_location_id_'] =  visit_cust.location_code.shift(1) 

        visit_cust['unplanned_count'] =  visit_cust.apply(lambda x:  \
            0 if x['planning_status'] == 'I' else 1 \
            , axis=1 )

        visit_cust['inplanning_count'] =  visit_cust.apply(lambda x:  \
            0 if x['planning_status'] == 'I' else 1 \
            , axis=1 )

        visit_cust = visit_cust[visit_cust.shifted_gpsx.notnull()]
        visit_cust = visit_cust[visit_cust['shifted_day'] == visit_cust['scheduled_start_day']]

        visit_cust['end_time_minute'] = visit_cust['scheduled_start_minutes'] + visit_cust['scheduled_duration_minutes']
        visit_cust['haversine_minutes'] = visit_cust.apply(lambda x: travel_router.get_travel_minutes_2locations([float(x['geo_longitude']),float(x['geo_latitude'])    ],
                                                                            [float(x['shifted_gpsx']),float(x['shifted_gpsy'])    ]) , axis=1 )
        travel_sum = visit_cust.groupby(['planner_code','scheduled_worker_code', 'scheduled_start_day']).agg(
            min_job_start=('scheduled_start_minutes', 'min'),
            max_job_end=('end_time_minute', 'max'),
            total_service_minute=('scheduled_duration_minutes', 'sum'),
            total_travel_minute=('haversine_minutes', 'sum'),
            total_job_count=('job_code', 'count'),
            total_unplanned_job_count=('unplanned_count', 'sum'),
            total_inplanning_job_count=('inplanning_count', 'sum'), 
        ).sort_values(['scheduled_worker_code', 'scheduled_start_day'], ascending=False).reset_index().copy()

        travel_sum['total_on_duty_minute'] =  travel_sum.apply(lambda x:  \
            x['max_job_end'] - x['min_job_start']\
            , axis=1 )

        travel_sum['on_site_service_time_ratio'] =  travel_sum.apply(lambda x:  \
            x['total_service_minute'] / x['total_on_duty_minute']\
            , axis=1 ) 



        travel_sum_day_only = travel_sum.groupby([ 'scheduled_start_day']).agg(
            mean_on_site_service_time_ratio=('on_site_service_time_ratio', 'mean'),
            sum_total_travel_minute=('total_travel_minute', 'sum'), 
            sum_total_service_minute=('total_service_minute', 'sum'), 
            sum_total_on_duty_minute=('total_on_duty_minute', 'sum'), 
            total_job_count=('total_job_count', 'sum'),
            total_unplanned_job_count=('total_unplanned_job_count', 'sum'),
            total_inplanning_job_count=('total_inplanning_job_count', 'sum'), 
        ).sort_values([ 'scheduled_start_day'], ascending=False).reset_index().copy()



        travel_sum_tech_only = travel_sum.groupby([ 'scheduled_worker_code']).agg(
            mean_on_site_service_time_ratio=('on_site_service_time_ratio', 'mean'),
            sum_total_travel_minute=('total_travel_minute', 'sum'), 
            sum_total_service_minute=('total_service_minute', 'sum'), 
            sum_total_on_duty_minute=('total_on_duty_minute', 'sum'), 
            total_job_count=('total_job_count', 'sum'),
            total_unplanned_job_count=('total_unplanned_job_count', 'sum'),
            total_inplanning_job_count=('total_inplanning_job_count', 'sum'), 
        ).sort_values([ 'scheduled_worker_code'], ascending=False).reset_index().copy()

        travel_sum_tech_only['planner_code'] = planner_code
        travel_sum_day_only['planner_code'] = planner_code


        travel_sum_tech_only.to_sql( name = 'kpdata_stats_features_per_worker', con=self.kplanner_db.cnx, schema=None, 
            if_exists='append', index=False )

        travel_sum_day_only.to_sql( name = 'kpdata_stats_features_per_day', con=self.kplanner_db.cnx, schema=None, 
            if_exists='append', index=False )


    def calc_job_location_history_features(self, planner_code = 'opti1day', start_day = None, end_day =  None):
        
        nbr_days = 100
        # kjs.scheduled_start_minutes  as actual_start_minutes, 
        print(datetime.now(), 'calc_job_location_history_features: Loading kpdata_jobstatus ...')
        self.kplanner_db.cnx.execute( '''delete from kpdata_location_job_history_features '''  )

        print(datetime.now(), 'calc_job_location_history_features: purged previous history_features ...')
        query_sql = '''
                SELECT kj.job_code, kj.job_type, kj.geo_longitude, kj.geo_latitude, kj.location_code, kjs.planner_code, 
                    kj.requested_worker_code,
                    kj.requested_start_datetime, 
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
                                date_util.transform_kandbox_day_2_postgres_datetime(start_day),  
                                date_util.transform_kandbox_day_2_postgres_datetime(end_day)
                            )


        visit  = self.kplanner_db.read_sql(query_sql)
        if visit.count().max() < 1:
            print("No history data is found ...")
            return


        print(datetime.now(), 'calc_job_location_history_features: started calc worker.served_location_gmm  ...')
        query_sql = '''
                SELECT worker_code as  actual_worker_code, worker_code as location_code, geo_longitude, geo_latitude 
                FROM  kpdata_worker 
                    ''' 


        worker_df  = self.kplanner_db.read_sql(query_sql)

        visit_with_worker_home = pd.concat( [ 
            visit[['actual_worker_code','location_code','geo_longitude','geo_latitude']]  ,
            worker_df
        ]).copy()
        visit_with_worker_home.rename(columns={'actual_worker_code': 'worker_code'}, inplace=True)

        worker_gmm_df = visit_with_worker_home.groupby(['worker_code']).agg( 
            # job_count=pd.NamedAgg(column='location_code', aggfunc='count')
            avg_geo_longitude=pd.NamedAgg(column='geo_longitude', aggfunc='mean')
            , avg_geo_latitude=pd.NamedAgg(column='geo_latitude', aggfunc='mean') 
            ).reset_index() # .sort_values(['location_code'], ascending=True)



        worker_update_sql = '''
            update kpdata_worker 
                SET served_location_gmm =   '{}'  
                where worker_code = '{}'
                ''' 

        for index, job in worker_gmm_df.iterrows():  
            worker_upsert_query = worker_update_sql.format(  
                  json.dumps({"mu":[job['avg_geo_longitude'],job['avg_geo_latitude']]})
                 ,job['worker_code'] 
            )
            
            self.kplanner_db.cnx.execute(worker_upsert_query)
        print(datetime.now(), 'calc_job_location_history_features: Saved worker.served_location_gmm  ...')



        visit['days_delay'] =  visit.apply(lambda x:  \
            (datetime.strptime(x['actual_start_day'], '%Y%m%d') -  datetime.strptime(x['requested_start_day'], '%Y%m%d')).days \
            , axis=1 )

        hjw = visit.groupby(['location_code']).agg(
            # job_historical_worker_service_dict = pd.NamedAgg(column='actual_worker_code', aggfunc=_assemble_hist)
            job_count=pd.NamedAgg(column='job_code', aggfunc='count')
            , geo_latitude=pd.NamedAgg(column='geo_latitude', aggfunc='mean')
            , geo_longitude=pd.NamedAgg(column='geo_longitude', aggfunc='mean')
            , list_requested_worker_code=pd.NamedAgg(column='requested_worker_code', aggfunc=list)
            , avg_actual_start_minutes=pd.NamedAgg(column='actual_start_minutes', aggfunc='mean')
            , avg_actual_duration_minutes=pd.NamedAgg(column='actual_duration_minutes', aggfunc='mean')
            , avg_days_delay=pd.NamedAgg(column='days_delay', aggfunc='mean') 
            , stddev_days_delay=pd.NamedAgg(column='days_delay', aggfunc='std') 
            ).sort_values(['location_code'], ascending=True).reset_index()

        # pd.Series.unique
        # hjw['list_requested_worker_code'] = hjw.apply(lambda x: json.dumps(list(set([x['list_requested_worker_code']]))), axis=1 )
        hjw['list_requested_worker_code'] = hjw.apply(lambda x: json.dumps(
            list(set([str(y) for y in x['list_requested_worker_code'] ]))  #  list(set([x['list_requested_worker_code']]))
            ), axis=1 )
       

        worker_gmm_df['_tmpkey'] = 1
        hjw['_tmpkey'] = 1

        res = pd.merge(worker_gmm_df, hjw, on='_tmpkey'
            ).drop('_tmpkey', axis=1
                ).sort_values( 
                    [ 'location_code','worker_code' ] 
                    )

        res['job_count'] = res.apply(lambda x:  \
            x['job_count'] + 100  if x['worker_code'] in x['list_requested_worker_code'] else x['job_count']  \
            , axis=1 )


        res['location_2_working_gmm_distance'] = res.apply(lambda x: 1000 - (round( travel_router.get_travel_minutes_2locations([float(x['geo_longitude']),float(x['geo_latitude'])    ],\
                                                                            [float(x['avg_geo_longitude']),float(x['avg_geo_latitude'])    ]), 0)) , axis=1 )
        res['affinity_score'] = res.apply(lambda x: x['job_count']*1000 +  x['location_2_working_gmm_distance'], axis=1 )
        res['affinity_score'].fillna(0,inplace=True)
        res['worker_affinity_score'] = res.apply(lambda x: [str(x['worker_code']), int(x['affinity_score'])], axis=1 )


        hjw_hist_dict = res.groupby(['location_code']).agg(
            job_historical_worker_service_dict_obj = pd.NamedAgg(column='worker_affinity_score', aggfunc=list)
            ).sort_values(['location_code'], ascending=True).reset_index().copy()
        
        hjw_hist_dict['job_historical_worker_service_dict'] = hjw_hist_dict.apply(lambda x: json.dumps(x['job_historical_worker_service_dict_obj']), axis=1 )
 
        worker_affinity_all_df = pd.merge(hjw, 
            hjw_hist_dict, 
            how='inner',   suffixes=('','_input'),
                    left_on=   [ 'location_code' ], 
                    right_on = [ 'location_code' ])
        worker_affinity_all_df.drop(columns = ['geo_longitude','geo_latitude','_tmpkey','job_historical_worker_service_dict_obj'],inplace=True)


        worker_affinity_all_df.to_sql( name = 'kpdata_location_job_history_features', con=self.kplanner_db.cnx, schema=None, 
            if_exists='append', index=False )
        print(datetime.now(), ': Saved calc_job_location_history_features...')






if __name__ == '__main__': 

    kfc = KPlannerFeatureCalculator()
    #kfc.purge_travel_time_statistics(planner_code = 'orig')

    '''
    # Copy orig to status table and add travel.
    kfc.add_travel_time_to_orig_job_status(planner_code = 'orig')


    kfc.calc_planner_travel_time_statistics(planner_code = 'orig')
    kfc.calc_planner_travel_time_statistics(planner_code = 'opti1day')
    '''
    kfc.calc_job_location_history_features(planner_code = 'prod_1', start_day = '20200107', end_day =  '20200908')

    #kfc.calc_planner_travel_time_statistics(planner_code = 'opti')
    #kfc.calc_planner_travel_time_statistics(planner_code = 'airhythm49')
    #kfc.calc_planner_travel_time_statistics(planner_code = 'rl7days')
    
