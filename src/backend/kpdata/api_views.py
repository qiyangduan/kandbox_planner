
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import authentication, permissions

from rest_framework.decorators import api_view, authentication_classes, permission_classes

from datetime import datetime, timedelta
import time
import kandbox_planner.util.planner_date_util  as date_util

from .models import Worker, JobStatus, Job

from kandbox_planner import config
from rest_framework import serializers
import numpy as np
import pandas as pd
from kandbox_planner.fsm_adapter.kplanner_db_adapter import  KPlannerDBAdapter
kplanner_db = KPlannerDBAdapter() 


from kandbox_planner.planner_engine.rl.env.kprl_env_rllib_history_affinity import KPlannerHistoryAffinityTopNGMMEnv
from kandbox_planner.planner_engine.rl.agent.kprl_agent_heuristic_single_job_history import HeuristicAgentSingleJobByHistory



# from kandbox_planner.planner_engine.toy_planner_rl.all_rl_planners_with_history import  rl_run_all, get_replayed_env
#TODO, do not know why it locks kpdata_location_job_history_features
# rl_env, rl_agent = get_replayed_env(batch_name = 'rl_heur',  start_day = '20191103', nbr_days = 1)

rl_env = None
rl_agent = None
# nbr_of_days_planning_window = 2
new_env_config = {
    'run_mode' : 'replay',
    'data_start_day':datetime.strftime(datetime.now(), config.KANDBOX_DATE_FORMAT),
    # 'data_end_day':'20200319',
    'nbr_of_observed_workers':6,
    'nbr_of_days_planning_window':5, 

}

 


# disable for migration
'''


'''


# class JobsTimelineDatasetView(APIView):

@api_view(['GET', 'POST'])
@authentication_classes([authentication.SessionAuthentication, authentication.BasicAuthentication])
@permission_classes([permissions.IsAuthenticated]) 
def worker_job_dataset_json(request):
    #authentication_classes = [authentication.TokenAuthentication]
    #permission_classes = [permissions.IsAdminUser]


    if request.method == 'GET':
        return Response({'received data': request.data, "uid":"?"})

    if request.method == 'POST':

        query_data = request.data
        start_time = datetime.strptime(query_data['start_date'], config.KANDBOX_DATE_FORMAT)  
        end_time = datetime.strptime(query_data['end_date'], config.KANDBOX_DATE_FORMAT)  
        w_list = query_data['worker_list']
        query_game_code = query_data['game_code']
        planner_days = date_util.days_between_2_day_string(
            start_day=query_data['start_date'],
            end_day=query_data['end_date'])

        print(datetime.now(), "worker_job_dataset_json: Started loading from database" )


        workers_dimensions = ['index','skills', 'max_conflict_level',  'worker_code',
            'geo_longitude', 'geo_latitude', 'weekly_working_minutes']
        
        jobs_dimensions = ['scheduled_worker_index',
            'scheduled_start_datetime','scheduled_end_datetime',  # datetime in javascript  MilliSecond.
            'job_code', 'job_type' ,'scheduled_travel_minutes_before', 
            'scheduled_travel_prev_code','conflict_level', 
            'scheduled_worker_code',
            'geo_longitude', 'geo_latitude','changed_flag' ]  


        if query_game_code == 'latest':
            worker_df  = kplanner_db.load_workers_original_df(
                worker_list = query_data['worker_list'] 
            )
            # query_game_code = kplanner_db.get_max_game_code()
        else:

            worker_df  = kplanner_db.load_worker_status_df(
                game_code  = query_game_code,
                worker_list = query_data['worker_list']
                )

        planned_jobs_list = []
        not_planned_jobs_list = []

        if query_game_code == 'latest':
            jobs_df  = kplanner_db.load_jobs_original_with_absence_df(
                start_day = query_data['start_date'], 
                end_day = query_data['end_date']
            )
            '''
            # query_game_code = kplanner_db.get_max_game_code()
            absence_df = kplanner_db.load_workerabsence_as_jobs_df(
                start_day = query_data['start_date'], 
                end_day = query_data['end_date']
                )
            '''
        else:

            jobs_df  = kplanner_db.load_job_status_df(
                game_code  = query_game_code,
                planner_code = query_data['planner_code'],
                start_day = query_data['start_date'], 
                end_day = query_data['end_date'],
                order_by= None # ' job_code '
                )
            # absence_df = None  
            ''' kplanner_db.load_workerabsence_as_jobs_df(
                start_day = query_data['start_date'], 
                end_day = query_data['end_date']
                )'''

        print(datetime.now(), "worker_job_dataset_json: Finished loading from database: " )

        jobs_df['conflict_level'].fillna(0,inplace=True)
        global rl_env
        global rl_agent

        if (rl_env is None ) \
            | (new_env_config ['data_start_day'] != query_data['start_date']) \
            | (new_env_config ['nbr_of_days_planning_window'] != planner_days): #TODO


            # print(new_env_config)
            new_env_config ['data_start_day'] = query_data['start_date']
            new_env_config ['nbr_of_days_planning_window'] = planner_days

            print(datetime.now(), "Started rl loading with config: ", new_env_config )
            # rl_env = KPlannerHistoryAffinityTopNGMMEnv(env_config=new_env_config, from_db=True)
            transformed_workers, workers_id_dict = kplanner_db._transform_workers(k_workers=worker_df, start_date=start_time)
            transformed_jobs = kplanner_db._transform_jobs(jobs=jobs_df, start_date=start_time)
            rl_env = KPlannerHistoryAffinityTopNGMMEnv( 
                workers=transformed_workers, 
                jobs=transformed_jobs, 
                env_config=new_env_config, from_db=False)
            rl_env.replay_env()
            rl_agent = HeuristicAgentSingleJobByHistory(env=rl_env) 

            print(datetime.now(), "Finished rl loading" )

        #TODO : Check & validate
        # rl_env, rl_agent = get_replayed_env(batch_name = 'rl_heur',  start_day = query_data['start_date'], nbr_days = 1)


        print(datetime.now(), "worker_job_dataset_json: Started transforming to dataset for web json... " )

        workers_start_end_dict = {}
        workers_dict={} 
        workers_list = []
        for index, w in worker_df.iterrows():  
            worker1 = {
                'index':index,
                'skills':w['skills'],
                'max_conflict_level':w['max_conflict_level'],
                'worker_code':w['worker_code'],
                'geo_longitude':w['geo_longitude'],
                'geo_latitude':w['geo_latitude'],
                'weekly_working_minutes':w['weekly_working_minutes'], 
                }
            workers_dict[w.worker_code] = worker1
            workers_list.append(worker1)
        
        new_df = pd.DataFrame(workers_list)

        if (len(rl_env.jobs) < 1):
            print("Warning: RL ENV is not ready!")
        df_count = new_df.count().max()
        if (pd.isnull(df_count)) or (df_count < 1):
            return  Response({
                'workers_dimensions': workers_dimensions,
                'workers_data': [],
                'jobs_dimensions': jobs_dimensions,
                'planned_jobs_data': [],
                'not_planned_jobs_data': [], # not_planned_jobs_data
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(), 
            #TODO: worker_time [[day_start, day_end], [day_start, day_end]], office_hours{[day_start, day_end, day_start, day_end, ...] }.
            } )  


            #
        # new_df.columns
        workers_data = new_df[workers_dimensions].values.tolist()


        for index, j in jobs_df.iterrows():  
            if j['scheduled_worker_code'] not in workers_dict.keys():
                continue
            #if workers_dict[curr_worker]['nbr_conflicts'] < conflict_level:
            #    workers_dict[curr_worker]['nbr_conflicts'] = conflict_level
            scheduled_start_datetime = datetime.strptime( j['scheduled_start_day'], config.KANDBOX_DATE_FORMAT) \
                                     + timedelta (minutes = j['scheduled_start_minutes'] ) 

            if (j['scheduled_duration_minutes'] is None) or (np.isnan(j['scheduled_duration_minutes'])):
                j['scheduled_duration_minutes'] = j['requested_duration_minutes']
            scheduled_end_datetime = scheduled_start_datetime + timedelta (minutes = j['scheduled_duration_minutes'] )     
            scheduled_start_datetime_js = int(time.mktime(scheduled_start_datetime.timetuple()) * 1000) 
            scheduled_end_datetime_js = int(time.mktime(scheduled_end_datetime.timetuple()) * 1000) 
            new_job = {
                'job_code': j['job_code'],
                'job_type': j['job_type'] ,
                'scheduled_worker_code': j['scheduled_worker_code'] ,
                'scheduled_worker_index':  workers_dict[j['scheduled_worker_code']]['index'],
                # https://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript
                'scheduled_start_datetime': scheduled_start_datetime_js, #scheduled_start_datetime.isoformat(),
                'scheduled_end_datetime':  scheduled_end_datetime_js, #scheduled_end_datetime.isoformat(),
                'scheduled_start_minutes': j['scheduled_start_minutes'] ,
                'scheduled_duration_minutes': j['scheduled_duration_minutes'] ,  
                'planning_status': j['planning_status'] ,  
                'conflict_level':j['conflict_level']  ,
                'scheduled_travel_minutes_after': j['scheduled_travel_minutes_after'] ,  
                'scheduled_travel_minutes_before': j['scheduled_travel_minutes_before'] ,  
                'scheduled_travel_prev_code': j['scheduled_travel_prev_code'] ,  
                'geo_longitude': j['geo_longitude'] ,  
                'geo_latitude': j['geo_latitude'] ,  
                'changed_flag': j['changed_flag'] ,  
                
                }
            if  j['job_code']== '1016439_1_TRBSB_2_13':
                print('pause for debug')
            if j['planning_status'] not in ['U']: # 'I', 'P', 'C'
                planned_jobs_list.append(new_job)
            else:
                new_job['scheduled_worker_code']=j['requested_worker_code'] 
                not_planned_jobs_list.append(new_job)

        # print(workers_dict)
        # new_planned_job_df.columns
        


        ''' , 'scheduled_start_datetime_js'
            'scheduled_start_minutes',
            'scheduled_duration_minutes', 'planning_status', 
            'scheduled_travel_minutes_after'

            
            '''
        planned_jobs_data = []
        not_planned_jobs_data = []

        if len(planned_jobs_list) > 0:
            new_planned_job_df = pd.DataFrame(planned_jobs_list).fillna(0)
            planned_jobs_data = new_planned_job_df[jobs_dimensions].values.tolist()
        if len(not_planned_jobs_list) > 0:
            new_not_planned_job_df = pd.DataFrame(not_planned_jobs_list).fillna(0).sort_values(by=['job_code'])
            #df = df
            not_planned_jobs_data = new_not_planned_job_df[jobs_dimensions].values.tolist()
        

        response = Response({
            'workers_dimensions': workers_dimensions,
            'workers_data': workers_data,
            'jobs_dimensions': jobs_dimensions,
            'planned_jobs_data': planned_jobs_data,
            'not_planned_jobs_data': not_planned_jobs_data, #not_planned_jobs_data,  
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(), 
            #TODO: worker_time [[day_start, day_end], [day_start, day_end]], office_hours{[day_start, day_end, day_start, day_end, ...] }.
        } )  
        import json
        # print(json.dumps(not_planned_jobs_data))
        print(datetime.now(), "worker_job_dataset_json: Finished.")
        return response

        # return Response({'received data': request.data, "duan":"qiyang"})

# planner_stats_per_day
@authentication_classes([authentication.SessionAuthentication, authentication.BasicAuthentication])
@permission_classes([permissions.IsAuthenticated]) 
class PlannerStatsPerDayJSONView(APIView):
    '''
    mocklist = [['scheduled_start_timestamp', 'orig_tos_time_ratio', 'opti_tos_time_ratio'],
                ['2019-11-01T00:00:00', 1.45043258392073, 11.5755999160293],
                ['2019-11-04T00:00:00', 0.665228727521044, 1.69269599635237], 
        ] 
    '''
    def get_kpi_array(self, planner_code_list = ['orig','opti1day'], query_data=None): 
        kpi_query = '''
                    select scheduled_start_day, total_job_count, 
                            mean_on_site_service_time_ratio as {0}_tos_time_ratio, 
                            sum_total_travel_minute as {0}_total_travel_minute
                    from kpdata_stats_features_per_day psfpd 
                    where planner_code = '{0}'
                    order by scheduled_start_day  asc
                    '''.format(planner_code_list[0]) 

        jobloc = kplanner_db.read_sql( kpi_query )

        jobloc['scheduled_start_timestamp'] = jobloc.apply(lambda x:  
                                                        datetime.strptime(x['scheduled_start_day'], config.KANDBOX_DATE_FORMAT).isoformat()
                                                        , axis=1 )

        kpi_query = '''
                    select scheduled_start_day,  
                            mean_on_site_service_time_ratio as {0}_tos_time_ratio, 
                            sum_total_travel_minute as {0}_total_travel_minute
                    from kpdata_stats_features_per_day psfpd 
                    where planner_code = '{0}'
                    order by scheduled_start_day  asc
                    '''.format(planner_code_list[1]) 

        jobloc_new = kplanner_db.read_sql( kpi_query )

        jobloc = jobloc.merge(jobloc_new, how='inner', left_on='scheduled_start_day', right_on='scheduled_start_day')

        colum_list = ['scheduled_start_timestamp', 'total_job_count' \
            ,'orig_tos_time_ratio',  'orig_total_travel_minute' \
            ,'opti1day_tos_time_ratio',  'opti1day_total_travel_minute' ]
        val_list = jobloc[colum_list].values.tolist()

        val_list.insert(0, colum_list)
        return val_list

    def get(self, request, format=None): 
        query_data = request.query_params
        val_list = self.get_kpi_array(query_data = query_data)
        return Response({
            'query_data': query_data, 
            "kpi_array": val_list # self.mocklist
            })

    def post(self, request, format=None):
        query_data = request.data

        #start_time = datetime.strptime(query_data['start_date'], config.KANDBOX_DATE_FORMAT)  
        #end_time = datetime.strptime(query_data['end_date'], config.KANDBOX_DATE_FORMAT)  

        val_list = self.get_kpi_array(query_data = query_data)

        response = Response({
            'query_data': query_data, 
            'kpi_array': val_list, #self.mocklist,
            'result': 'ok',
            #'start_time': start_time.isoformat(),
            #'end_time': end_time.isoformat(), 
        } )  
        return response



#  
@authentication_classes([authentication.SessionAuthentication, authentication.BasicAuthentication])
@permission_classes([permissions.IsAuthenticated]) 
class CommitRLChangesJSONView(APIView): 
    def post(self, request, format=None): 
        changed_jobs = request.data

        for job in changed_jobs:

            
            start_datetime = datetime.utcfromtimestamp( job['scheduled_start_datetime'] / 1000)
            job['scheduled_start_datetime'] = start_datetime
            job['last_update_by'] = 'web'
            #TODO
            job['scheduled_travel_prev_code'] = '__HOME'
            job['scheduled_travel_minutes_before'] = 0
            kplanner_db.update_single_job(job)
            
        return Response({
            'result': 'OK' 
            })
 






                                                                                                                                                    

#  
@authentication_classes([authentication.SessionAuthentication, authentication.BasicAuthentication])
@permission_classes([permissions.IsAuthenticated]) 
class GymEnvStepJSONView(APIView): 
    def get(self, request, format=None): 
        # query_data = request.query_params 
        curr_job_code = rl_env.jobs[rl_env.current_job_i]['job_code']

        result_list = []


        actions = rl_agent.predict_action_list(job_code = curr_job_code)
        # for index, action in enumerate(actions):
        action=actions[0]
        a_dict = rl_env.decode_action_into_dict(action)
        observation, reward, done, info = rl_env.step(action)  

        job_code = rl_env.jobs[rl_env.current_job_i]['job_code']

        return Response({
            'prev_job_code': curr_job_code, 
            'job_code': job_code, 
            "action_dict": a_dict,
            'observation': observation, 
            'reward': reward, 
            'done': done, 
            'info': info,
            'current_observed_worker_list': rl_env.current_observed_worker_list,
            })
 



#  
@authentication_classes([authentication.SessionAuthentication, authentication.BasicAuthentication])
@permission_classes([permissions.IsAuthenticated]) 
class SingleJobDropCheckJSONView(APIView):
    '''
    single_job_drop_check.json

    RESULT is [-1,1]
    result = {
        "result": 0.5, 
        "travel_time": 30,
            result['scheduled_travel_prev_code'] =  '_HOME'
            result['scheduled_travel_minutes_before'] =  0
        "messages": [
            {'score': -0.3, 'message': 'not in working hour'} ,
            {'score': -0.3, 'message': 'Conflict with others'} ,
        ]
    } 

    Input: 
    _dropRecord = {
                categoryIndex: 1,
                timeArrival: cursorData[0],
                timeDeparture: cursorData[0] + _draggingTimeLength,
                travelMinutes: 0 ,
                jobCode:
            }
    '''
    result_json = {
        "result": 'OK', 
        "score": '0.5', 
        "travel_time": 30,
        "messages": [
            [ -0.3, 'not in working hour'],
            {'score': -0.3, 'message': 'Conflict with others'} ,
        ]
    } 
    def get(self, request, format=None): 
        query_data = request.query_params 
        return Response({
            'query_data': query_data, 
            "result": self.result_json # self.mocklist
            })
 

    def post(self, request, format=None):


        query_data = request.data
        job_code = query_data['jobCode']
        # worker_index = query_data['categoryIndex']
        worker_code = query_data['workerCode']
        
        arrival_seconds = query_data['timeArrival'] / 1000
        new_datetime = datetime.utcfromtimestamp(arrival_seconds)
        new_mintues = ( arrival_seconds / 60)  % (24*60) 
        result = self.result_json.copy()
        result['messages'] = []

        # new_datetime = datetime.datetime.strptime("2008-09-03T20:56:35.450686Z", "%Y-%m-%dT%H:%M:%S.%fZ")
        if  worker_code not in  rl_env.workers_dict.keys():

            result['result'] = 'Error'
            result['messages'].append([-1, 'Did not find worker by code: ' + worker_code])
            response = Response(result)  
            return response

        orig_job_i  =  rl_env.current_job_i 
        rl_env.current_job_i  = rl_env.jobs_dict[job_code]['job_index']
        a_dict = {
            'scheduled_worker_code': worker_code, # rl_env.workers[worker_index]['worker_code'],
            'scheduled_start_day': 0,
            'scheduled_start_minutes': new_mintues,
            'scheduled_duration_minutes': 30,
            'scheduled_related_worker_code':[]
            }
        action = rl_env.code_dict_into_action(a_dict)
        # Check for all external business rules.

        for rule in rl_env.rule_set.action_rule_list:
            a_dict = rl_env.decode_action_into_dict(action)
            rule_checked = rule.evalute_action_normal(env = rl_env, action_dict = a_dict)
            
            if rule_checked['score'] == -1:
                result['result'] = 'Warning'
                result['messages'].append([-1, rule_checked['message']])
            else:
                result['messages'].append([rule_checked['score'], rule_checked['message']])
        '''
        travel_checked = rl_env.rule_set.sufficient_travel_reward.evalute_action_normal(rl_env, action, job_i = rl_env.jobs_dict[job_code]['job_index'] )
        prev_job_index =  travel_checked['prev_job_index'] 
        if prev_job_index is not None:
            result['scheduled_travel_prev_code'] =  rl_env.jobs[prev_job_index]['job_code']
            result['scheduled_travel_minutes_before'] =  travel_checked['prev_travel_time']  
        else:
            result['scheduled_travel_prev_code'] =  '_HOME'
            result['scheduled_travel_minutes_before'] =  0
        print("I am checking job at time: ", a_dict['scheduled_start_minutes'], "prev node: ", result['scheduled_travel_prev_code'])

        if travel_checked['score'] == -1:
            result['result'] = 'Error'
            result['messages'].append([-1, travel_checked['message']])
        '''
        
        
        rl_env.current_job_i = orig_job_i

        '''
        # if job_code.split("_")[-1] == 'FS':
        if query_data['categoryIndex'] < 2:
            self.result_json['result'] = 'Warning'
            self.result_json['travel_time'] = 50
        if query_data['categoryIndex'] >3:
            self.result_json['result'] = 'OK'
            self.result_json['travel_time'] = 10
        '''
        response = Response(result)  
        return response


@authentication_classes([authentication.SessionAuthentication, authentication.BasicAuthentication])
@permission_classes([permissions.IsAuthenticated]) 
class GetSlotsSingleJobJSONView(APIView):
    '''
    Input: 
    _dropRecord = {
                startDay: '2019',
                jobCode: '1234-FS'
            }

    RESULT is [-1,1]
    result = [  
        {'score': -0.3, 'message': 'not in working hour'} ,
        {'score': -0.3, 'message': 'Conflict with others'} ,
        ]


    '''
    
    def post(self, request, format=None):
        query_data = request.data
        job_code = query_data['jobCode']
        start_day = query_data['startDay']
        result_list = []

        start_datetime = datetime.strptime(start_day, config.KANDBOX_DATE_FORMAT)  
        
        # controlled comparison 2020-04-23 11:53:46
        from .admin import current_rl_heur_planner
        other_actions = current_rl_heur_planner['planner_agent'].predict_action_list(job_code = job_code)
        b_dict = current_rl_heur_planner['planner_env'].decode_action_into_dict( other_actions[0])

        #


        actions = rl_agent.predict_action_list(job_code = job_code)
        for index, action in enumerate(actions):
            a_dict = rl_env.decode_action_into_dict(action)

            scheduled_start_datetime = start_datetime + timedelta (minutes = a_dict['assigned_start_day_n_minutes'] )     
            scheduled_start_datetime_js = int(time.mktime(scheduled_start_datetime.timetuple()) * 1000) 
            a_dict['js_start_time'] =   scheduled_start_datetime_js

            a_dict['score'] = 5-index
            result_list.append(a_dict)

        response = Response(result_list)  
        return response

    def get(self, request, format=None): 
        #query_data = request.data
        result_list = []
        # job_code = query_data['jobCode']
        job_code = self.kwargs.get('jobCode')
        start_day = self.kwargs.get('startDay') 

        return "can not get parameter"

class JobQuerySerializer(serializers.Serializer):
    start_date = serializers.CharField(max_length=8)
    end_date = serializers.CharField(max_length=8)
    planner_code = serializers.CharField(max_length=100)
    # source_system_code = serializers.CharField(max_length=100) 
    game_code = serializers.CharField(max_length=100) 
    new_job_code = serializers.CharField(max_length=100) 
    worker_list = serializers.CharField(max_length=100) 


    def validate_title(self, value):
        """
        Check that the blog post is about Django.
        """
        if 'django' not in value.lower():
            raise serializers.ValidationError("Blog post is not about Django")
        return value