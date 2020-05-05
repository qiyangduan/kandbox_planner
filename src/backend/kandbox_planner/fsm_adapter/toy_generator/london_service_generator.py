# https://stackoverflow.com/questions/19069701/python-requests-library-how-to-pass-authorization-header-with-single-token
# https://www.quora.com/How-can-I-make-an-API-call-with-basic-HTTP-authentication-using-Python

import requests
import pandas as pd
from kandbox_planner.fsm_adapter.kplanner_db_adapter import  KPlannerDBAdapter
from kandbox_planner.fsm_adapter.kplanner_api_adapter import  KPlannerAPIAdapter

from kandbox_planner.planner_engine.feature_calc import  KPlannerFeatureCalculator
from kandbox_planner.planner_engine.opti1day.opti1day_planner import  Opti1DayPlanner
from kandbox_planner.planner_engine.rl.all_rl_planners import  rl_run_all

kplanner_db = KPlannerDBAdapter() 

import os
kplanner_service_url =  os.getenv ('kplanner_service_url','http://127.0.0.1:8000')


kplanner_api = KPlannerAPIAdapter(service_url = kplanner_service_url)

import random

#    workers, workers_id_dict = kplanner_db.load_workers(start_day = start_day, nbr_days = nbr_days_in_batch) 
import kandbox_planner.util.planner_date_util  as date_util
# from kandbox_planner.planner_engine.toy_planner_optimizer.worker_order_gps_planner  import dispatch_jobs 

# Sample Basic Auth Url with login values as username and password


from datetime import datetime  
from datetime import timedelta  

from random import seed
from random import randint
# seed random number generator
seed(1978)
from pprint import pprint
# import config.settings.local as config

import kandbox_planner.config as config

KANDBOX_DATE_FORMAT = config.KANDBOX_DATE_FORMAT # '%Y%m%d'


JOB_GPS_LIST = [ 
        [ '51.447250,-0.189370', '11 Garratt Ln, London SW18 4AQ'],
        [ '51.456250,-0.201050', 'The Pumphouse, Lebanon Rd, London SW18 1RE'],
        [ '51.460870,-0.177520', 'St Johns Hill, Battersea, London SW11 2QP'],
        [ '51.511130,-0.122040', 'Davidson Building, London WC2E 7HA'],
        [ '51.422690,-0.202560', 'Unit 115 Centre Court, 4 Queens Road, Wimbledon, SW19 8YA'],
        [ '51.487630,-0.178230', 'Waterfront Dr, Fulham, London SW10 0QD'],
        [ '51.493350,-0.168370', '89 Sloane Ave, Chelsea, London SW3 3DX'],
        [ '51.5115480,0.001055268', 'Leamouth Road, Poplar, London	E14 0JG'],
        [ '51.4059354,-0.140786051', 'Rown Road, London	SW16 5JF'],
        [ '51.5081003,0.079313135', 'Atlantis Avenue, London	E16 2BF'],
        [ '51.433456,-0.167078571', '-0.16707857157978992:51.433456197551315'],
        [ '51.5079220,0.054734676', 'Royal Albert Way, London	E16 2QU'],
        [ '51.4853844,0.009171047', 'Vanbrugh Hill, Greenwich	SE10 0DGs'],
        [ '51.50744689,0.065910331', 'Docklands Campus, University Way, London	E16 2RD'],
        [ '51.31248841,-0.147364031', 'Cane Hill, Coulsdon, South Croydon	CR5 3YL'],
    ]

WORKER_GPS_LIST = [
         ['51.44627780733451,-0.1960066034365281'   ,'-0.1960066034365281:51.44627780733451']
        ,['51.50874451583848,-0.1232015238018501'  ,'-0.12320152380185012:51.50874451583848']
        ,['51.43884800126409,-0.1727406536075019'   ,'-0.1727406536075019:51.43884800126409']
        ,['51.45238536979151,-0.1455964578957485'  ,'-0.14559645789574854:51.45238536979151'] 
        ,['51.53156334,0.076215309', 'Barking Creative Industries Quarter, Abbey Road, Barking	IG11 7BT']
        ,['51.50986116,0.071279704', 'Gallions Roundabout, Royal Docks Road, London	E16 7AB']
    ]


def get_normalized_location(loc_i, JOB_GPS_LIST): 
  # distance = haversine(loc_1[0] , loc_1[1] , loc_2[0], loc_2[1]) 

    ll = loc_i % 15
  
    x =  JOB_GPS_LIST[ll][0].split(',')[1]
    y =  JOB_GPS_LIST[ll][0].split(',')[0]
    return '{}:{}'.format(x,y) 


def generate_and_save_one_day_orders(current_day, current_shifts,  worker_list ):
    current_shifts = _SHIFTS
    for index, shift in enumerate(current_shifts):
    # for shift in current_shifts:
        # [0, 'FS', '7:12', 108, 60, 32]
        shift[2] =  get_normalized_location(index, JOB_GPS_LIST) # '{}:{}'.format(x,y) x, y = randint(1, 99), randint(1, 99)
        shift[3] = randint(560, 1040)
        shift[5] = randint(4*5, 30*4)
    insert_all_orders(current_day = current_day, current_shifts = current_shifts,  worker_list = worker_list)


def generate_and_save_orders(GENERATOR_START_DATE , GENERATOR_END_DATE, current_shifts , worker_list ):

    for day_i in range(9999):
        current_day = GENERATOR_START_DATE + timedelta(days=day_i) 
        if current_day >= GENERATOR_END_DATE:
            break
        generate_and_save_one_day_orders(current_day, current_shifts = current_shifts,  worker_list = worker_list)


def select_all_workers():
    url = 'http://localhost:5000/api/v1/worker?q=(columns:!(id,worker_code,name,active,service_area_code,geo_longitude,geo_latitude,working_time,level,birthday))'
    response = requests.get(url,  headers={'Content-Type':'application/json',
                'Authorization': 'Token {}'.format(access_token)}
            )
    resp_json = response.json() 

    return(resp_json)

    if resp_json['count'] < 1:
        print('it is already empty!')
        return []




def insert_all_workers(worker_list):
    # url = '{}/kpdata/workers/'.format(kplanner_service_url)
    index = 0
    list_to_insert = []
    for worker in worker_list:
        gps = get_normalized_location(index, WORKER_GPS_LIST)

        print('adding worker: ',worker, gps) 
        
        index += 1
        myobj =  {
            'worker_code': worker[1],
            'name': '{}-{}'.format(worker[1],worker[0]),
            # 'birthday': '2000-10-25',
            'skills': '[1]',
            'geo_latitude': gps.split(':')[1],
            'geo_longitude': gps.split(':')[0],
            'weekly_working_minutes': '[ [0, 0], [480, 1140],[480, 1140],[480, 1140],[480, 1140],[480, 1140],  [0, 0]]'
            # 'level': 0,
            
            }
        
        list_to_insert.append(myobj)
    kplanner_api.insert_all_workers(list_to_insert)



def delete_all_workers():

    kplanner_api.delete_all_workers()
    return

    url = '{}/kpdata/workers/'.format(kplanner_service_url)
    response = requests.get(url,  headers={'Content-Type':'application/json',
                'Authorization': 'Token {}'.format(access_token)}
            )
    resp_json = response.json()
        # Convert JSON to dict and print
    # print(resp_json)
    if len(resp_json ) < 1:
        print('it is already empty!')
        return

    for worker in resp_json :
        print('deleting worker: ',worker) 
        url = '{}/kpdata/workers/'.format(kplanner_service_url) + str(worker['worker_code']) + ''
        #print(url)
        response = requests.delete(url,  headers={ 
                'Authorization': 'Token {}'.format(access_token)}
            )
        print(response.text )



def select_all_orders(current_day=None):

    return 
    url = 'http://localhost:5000/api/v1/workorder'
    if current_day is not None:
        url = 'http://localhost:5000/api/v1/workorder/?q=(filters:!((col:requested_start_date,opr:eq,value:{})),order_columns:order_code,order_direction:desc)' \
            .format(datetime.strftime(current_day,KANDBOX_DATE_FORMAT))
        # ,columns:!(order_code,name,planning_status,requested_start_date,scheduled_start_time,geo_latitude,geo_longitude,fixed_date_time_flag,requested_start_time,requested_duration_minutes)
        print(url)
    response = requests.get(url,  headers={'Content-Type':'application/json',
                'Authorization': 'Token {}'.format(access_token)}
            )
    resp_json = response.json()
    
    return(resp_json)

def select_orders_by_workers_TODO(workers=[]):
    url = 'http://localhost:5000/api/v1/workorder'
    response = requests.get(url,  headers={'Content-Type':'application/json',
                'Authorization': 'Token {}'.format(access_token)}
            )
    resp_json = response.json()
    
    return(resp_json)


def insert_all_orders(current_day, current_shifts, worker_list): 
    list_to_insert = []
    for order in current_shifts:
        # print('adding order: ',order) 
        # [100, 'FS', '06:00', 18, 60, 32]
        myobj =  { 
            'job_code': '{}-{}-{}'.format(datetime.strftime(current_day, '%m%d'), order[0],order[1]),  
            'job_type':order[1],
            'mandatory_minutes_minmax_flag': 1 if order[1] == 'FS' else 0, 
            'requested_start_min_minutes' : order[3],
            'requested_start_max_minutes' : order[3],
            'location_code': '{}-{}'.format( order[0],order[1]), 
            'geo_latitude': order[2].split(':')[1],
            'geo_longitude': order[2].split(':')[0],
            'requested_min_level': 0, 
            'planning_status': 'U', 
            'scheduled_duration_minutes': order[5] ,
            'requested_duration_minutes': order[5] ,
            #'requested_start_day':  datetime.strftime(current_day, KANDBOX_DATE_FORMAT), 
            #'scheduled_start_day':  datetime.strftime(current_day, KANDBOX_DATE_FORMAT), # '2019-10-29 '  ,
            #'actual_start_date':  datetime.strftime(current_day, KANDBOX_DATE_FORMAT), # '2019-10-29 '  ,
            #'requested_start_minutes':  order[3]   ,  # + ':00'
            #'scheduled_start_minutes':  order[3]  ,  # + ':00'
            'requested_start_datetime':  datetime.strftime(current_day + timedelta(minutes=order[3]),  "%Y-%m-%dT%H:%M:%S"), 
            'scheduled_start_datetime':  datetime.strftime(current_day + timedelta(minutes=order[3]),  "%Y-%m-%dT%H:%M:%S"), 
            'scheduled_worker_code': '{}/kpdata/workers/{}/'.format(kplanner_service_url, worker_list [ random.randint(0, 5) ][1]),   
            'requested_worker_code': '{}/kpdata/workers/{}/'.format(kplanner_service_url, worker_list [ random.randint(0, 5) ][1]),   
              }
        list_to_insert.append(myobj)
    
    kplanner_api.insert_all_orders(list_to_insert)
        



def save_RL_dispatched_orders_one_day(solution_json): 
    # print(worker_day)
    # {'duration': 100, 'job_id': '0-FS', 'fixed_schudule': {'fs_indicator': 'FT', 'fixed_minute_time_slot': [148.0, 148.0]}, 'job_gps': [57.0, 98.0], 'history_job_worker_count': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'history_minute_start_time': 0, 'tolerated_day_min': 0, 'tolerated_day_max': 0, 'expected_job_day': 0, 'expected_job_day_orig': 0, 'actual_job_worker': None, 'actual_job_day': 1, 'actual_job_start_minute': 148, 'actual_job_duration': 20}, 
    for task in  solution_json : 
            task_id = task['job_id']  # + 1
            worker_id = task['VisitOwner_worker_id']
            url = 'http://localhost:5000/api/v1/workorder/'  + str(task_id) 
            start_time_minute = task['start_time_minute'] 
            updated_order =  {} # latest_order_dict[id]
            updated_order.update ({ 
                'planning_status': 'I', 
                'scheduled_worker_rel': worker_id,
                'actual_worker_rel': worker_id,
                'scheduled_start_time': date_util.minutes_to_time_string( start_time_minute ),
                'actual_start_time': date_util.minutes_to_time_string( start_time_minute ),
                'scheduled_duration_minutes':  task['duration'] , 
                'actual_duration_minutes': task['duration'] , 
              } )
            print(updated_order)
            response = requests.put(url, json=updated_order, headers={'Content-Type':'application/json',
                'Authorization': 'Token {}'.format(access_token)}   )

            # Convert JSON to dict and print
            print(response.text)

def delete_all_orders():
    kplanner_api.delete_all_orders()
    return

    url = '{}/kpdata/jobs/'.format(kplanner_service_url)   # http://localhost:5000/api/v1/workorder/1'
    response = requests.get(url,  headers={'Content-Type':'application/json',
                'Authorization': 'Token {}'.format(access_token)}
            )
    resp_json = response.json()
        # Convert JSON to dict and print
    # print(resp_json)
    if len(resp_json)  < 1:
        print('it is already empty!')
        return

    for worker in resp_json :
        print('deleting order: ',worker) 
        url = '{}/kpdata/jobs/'.format(kplanner_service_url) + str(worker['job_code']) + ''
        print(url)
        response = requests.delete(url,  headers={ 
                'Authorization': 'Token {}'.format(access_token)}
            )
        print(response.text )


def dispatch_all_generated_orders(GENERATOR_START_DATE, TRAINING_DAYS, max_exe_time):

    kplanner_db = KPlannerDBAdapter() 
    nbr_days_in_batch = 1

    for day_i in range(TRAINING_DAYS) : #GENERATOR_RANGE):
        current_day = GENERATOR_START_DATE + timedelta(days=day_i) 
        workers, workers_id_dict = kplanner_db.load_transformed_workers(start_day = current_day, nbr_days = nbr_days_in_batch) 

        jobs_orig = kplanner_db.load_jobs_original( workers_id_dict , start_day = current_day, nbr_days = 1)

        if len(jobs_orig) < 1:
            print('it is empty, nothing to dispatch!')
            return
        # _EMP = ['3:4', '12:5', '21:4','4:55', '12:50', '21:50' ]
        _EMP = []
        for ii, e in enumerate(workers):
            _EMP.append('{}:{}'.format(e['geo_latitude'], e['geo_longitude']))   

        current_shifts=[]
        # [0, 'FS', '7:12', 108, 60, 32]
        latest_order_dict = {}
        for ii, order in  jobs_orig.iterrows():
            current_shifts.append([ii, \
                    order['job_type'] , \
                    '{}:{}'.format(order['geo_latitude'], order['geo_longitude']),\
                    int( (order['requested_start_minutes']) )  ,   # minutes_to_time_string\
                    0,  \
                    int(order['requested_duration_minutes']  ) , 
                    order['job_code']
                      ])
        print({'loaded day':current_day, 'job count': len(current_shifts)}) # , 'shift':current_shifts, 'emp': _EMP})
        worker_day = dispatch_jobs(shifts= current_shifts, emps = _EMP, max_exe_time=max_exe_time)
        if len(worker_day) < 1:
            print('no data returned!')
            return 
            #save_one_day_dispatched_orders(worker_day, workers, kplanner_db)

        job_list = []
        for w_i in range(len(worker_day)):
            for task in worker_day[w_i][:-1]:
                task_id = task[0]  # + 1
                worker_code = workers[w_i] ['worker_code']
                # updated_order =  {} # latest_order_dict[id]
                job_list.append ({  
                    'job_code': current_shifts[task_id][6], 
                    'planning_status': 'V', 
                    'scheduled_worker_code': worker_code,
                    'scheduled_start_day': datetime.strftime(current_day,KANDBOX_DATE_FORMAT),
                    'scheduled_start_minutes': task[1]  ,
                    'scheduled_duration_minutes':  task[2]  ,  
                    'scheduled_travel_minutes':  task[3]  ,  
                      } ) 
                '''
                    'actual_worker_code': worker_code,
                    'actual_start_day': datetime.strptime(current_day,KANDBOX_DATE_FORMAT),
                    'actual_start_minutes':  task[1] , 
                    'actual_duration_minutes': task[2] ,  '''
        job_df = pd.DataFrame(job_list)
        job_df['planner_code'] = 'opti'
        job_df['effective_from_date'] = datetime.now()
        
        game_info = {
                'planner_code': 'opti',
                'game_code': 'curr_game_code',
            }

        kplanner_db.save_schedued_jobs(job_df)

#def save_one_day_dispatched_orders(worker_day, workers, kplanner_db ): 




import xmlrpc.client

url = 'http://localhost:8069'
# db =  'local_demo_1'
db = 'odoodb1'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
# print(common.version())



def move_workers_to_odoo(): 
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    worker_result = select_all_workers()
    odoo_worker_dict = {}
    for ii, worker in enumerate(worker_result['result']):
        worker_id = worker_result['ids'][ii]
        id = models.execute_kw(db, uid, password, 'fsm.person', 'create', [{
            'name': 'K-Planner-{}'.format(worker_id),
            'fsm_person': True,
            'ref':worker_id,
            'mobile':'GPS:{}-{},worker_code:{} '.format(worker['geo_latitude'],worker['geo_longitude'],worker['worker_code'])  
        }])
        odoo_worker_dict[worker_id] = id
    print(odoo_worker_dict)
    # print(p)

def move_orders_to_odoo(): 
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    # GENERATOR_START_DATE = GENERATOR_START_DATE
    for day_i in range(61,62) : #GENERATOR_RANGE):
        current_day = GENERATOR_START_DATE + timedelta(days=day_i) 
        a_result = select_all_orders(current_day) # =datetime.strptime('20190103',KANDBOX_DATE_FORMAT))
        odoo_worker_dict = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11}
        for ii, o in enumerate(a_result['result']):
            order_id = a_result['ids'][ii]
            # (order_code,name,planning_status,requested_start_date,scheduled_start_time,geo_latitude,geo_longitude,fixed_date_time_flag,requested_start_time,requested_duration_minutes
            id = models.execute_kw(db, uid, password, 'fsm.order', 'create', [{
                'name': '{}-({})-({}:{})-K'.format(o['name'], order_id, o['geo_latitude'], o['geo_longitude']),
                'team_id': 1,
                'location_id':1,
                'company_id':1,
                'description': 'requested_start_time:{},'.format(o['requested_start_time']),
                'person_id':odoo_worker_dict[   o['scheduled_worker_rel']['id']   ],
                'scheduled_date_start': datetime.strftime( datetime.strptime(o['scheduled_start_date'],KANDBOX_DATE_FORMAT) + \
                                                        timedelta(minutes=date_util.time_string_hhmm_to_minutes(o['scheduled_start_time'])) \
                                                        , '%Y-%m-%d %H:%M:%S'), 
                'scheduled_duration':o['requested_duration_minutes']/60, # o['scheduled_duration_minutes']/60,

            }])
            
            # print(id)
    # print(p)


if __name__ == '__main__': 

    import sys
    
    if len(sys.argv) < 2:
        print('I need 1 parameters: python _this_.py token')

    token = sys.argv[1] 
    print(token)
    # token = '6161871e78b90219ade283fd3971219f66e6ed01'

    kplanner_api.access_token = token

    _SHIFTS =  [
        [0, 'FS', '7:12', 108, 60, 32],   [1, 'N', '8:3', 26, 68, 22],   [2, 'N', '06:4', 66, 121, 25], 
        [3, 'N', '15:5', 20, 72, 12],    [4, 'N', '11:4', 133, 189, 16], [5, 'N', '13:2', 2, 19, 17], 
        [6, 'N', '20:5', 91, 131, 34],   [7, 'N', '21:7', 8, 30, 52],   [8, 'FS', '3:45', 180, 190, 60], 
        [9, 'N', '5:49', 38, 80, 22],   [10, 'FS', '14:54', 43, 90, 37],  [11, 'N', '13:60', 169, 169, 25], 
        [12, 'FS', '19:55', 218, 215, 37], [13, 'N', '20:59', 196, 234, 38],[14, 'N', '20:48', 235, 248, 13]
    ]

    _EMP = ['-0.1960066034365281:51.44627780733451'
        ,'-0.12320152380185012:51.50874451583848'
        ,'-0.1727406536075019:51.43884800126409'
        ,'-0.14559645789574854:51.45238536979151'
        ,'-0.1944764936594672:51.479491652786834'
        ,'-0.16707857157978992:51.433456197551315'
    ]

    # worker_day =[[[1, 55, 22], [7, 82, 52], ['sink']], [[0, 108, 32], [2, 143, 25], [9, 174, 22], ['sink']], [[3, 20, 12], [5, 35, 17], [4, 55, 16], [6, 91, 34], ['sink']], [[8, 180, 60], ['sink']], [[11, 146, 25], [12, 218, 37], [14, 258, 13], ['sink']], [[10, 43, 37], [13, 84, 38], ['sink']]]


    people = ('Tom', 'Mike', 'Harry', 'Slim', 'Jim','Duan')
    worker_list = [[wi, people[wi], _EMP[wi]] for wi in  range(len(people))]




    ss = config.KANDBOX_TEST_START_DAY
    ee =  config.KANDBOX_TEST_END_DAY
    GENERATOR_START_DATE =  datetime.strptime(ss, KANDBOX_DATE_FORMAT )
    GENERATOR_END_DATE =  datetime.strptime(ee, KANDBOX_DATE_FORMAT )


    # exit(0)
    '''
    '''

    kplanner_db.purge_all_workers_jobs()

    insert_all_workers(worker_list)
    generate_and_save_orders(GENERATOR_START_DATE =  GENERATOR_START_DATE, GENERATOR_END_DATE=GENERATOR_END_DATE,  current_shifts = _SHIFTS,  worker_list = worker_list) # This genearte 450 orders 

    opti = Opti1DayPlanner( max_exec_time = config.KANDBOX_OPTI1DAY_EXEC_SECONDS) # 0*60*24
    # opti.kplanner_db.purge_planner_job_status(planner_code=opti.planner_code,start_date = ss, end_date = ee )
    res = opti.dispatch_jobs( start_date = config.KANDBOX_TEST_OPTI1DAY_START_DAY, end_date = config.KANDBOX_TEST_OPTI1DAY_END_DAY )
    # pprint(res)


    kfc = KPlannerFeatureCalculator()

    # Copy orig to status table and add travel.
    # kfc.add_travel_time_to_orig_job_status(planner_code = 'orig', start_day = ss, end_day =  ee)

    kfc.calc_planner_travel_time_statistics(planner_code = 'orig', start_day = ss, end_day =  ee)
    kfc.calc_planner_travel_time_statistics(planner_code = 'opti1day', start_day = ss, end_day =  ee)
    print("Started location feature calc ...")
    kfc.calc_job_location_history_features(planner_code = 'opti1day', start_day = ss, end_day =  ee)


    rl_run_all(batch_name = 'dispatch_v2_1', train_again = True, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 0, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    rl_run_all(batch_name = 'dispatch_v2_1', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 3, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)

    rl_run_all(batch_name = '5minutes_dense_1', train_again = True, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 0, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    rl_run_all(batch_name = '5minutes_dense_1', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 3, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)

    rl_run_all(batch_name = '5minutescnn_dense_1', train_again = True, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 0, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    rl_run_all(batch_name = '5minutescnn_dense_1', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 3, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)

    rl_run_all(batch_name = 'dispatch_v2_1', train_again = True, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 0, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    rl_run_all(batch_name = 'dispatch_v2_1', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 3, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)

    rl_run_all(batch_name = 'rl_heur', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 2, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)


    exit(0)
