# https://stackoverflow.com/questions/19069701/python-requests-library-how-to-pass-authorization-header-with-single-token
# https://www.quora.com/How-can-I-make-an-API-call-with-basic-HTTP-authentication-using-Python

import requests
import pandas as pd
# from kandbox_planner.fsm_adapter.kplanner_db_adapter import  KPlannerDBAdapter
# kplanner_db = KPlannerDBAdapter() 

#    workers, workers_id_dict = kplanner_db.load_workers(start_day = start_day, nbr_days = nbr_days_in_batch) 
import kandbox_planner.util.planner_date_util  as date_util


from datetime import datetime  
from datetime import timedelta  

from pprint import pprint
import kandbox_planner.config as config
# KANDBOX_DATE_FORMAT = config.KANDBOX_DATE_FORMAT # "%Y%m%d"

class KPlannerAPIAdapter:
    # access_token = 0
    def __init__(self):      
        # Create your connection.
        # TODO: use same config.
        self.access_token = self.get_access_token(login_info = {"username": "admin", "password": "admin", "provider": "db"})
        pass




    def insert_all_workers(self, worker_list):
        url = "http://127.0.0.1:8000/kpdata/workers/" 

        for myobj in worker_list:
            #print(myobj)
            response = requests.post(url, json=myobj, headers={'Content-Type':'application/json',
                    'Authorization': 'Token {}'.format(self.access_token)}
                )

            # Convert JSON to dict and print
            print(response.json())

    def delete_all_workers(self):
        url = "http://127.0.0.1:8000/kpdata/workers/"  
        response = requests.get(url,  headers={'Content-Type':'application/json',
                    'Authorization': 'Token {}'.format(self.access_token)}
                )
        resp_json = response.json()
        # Convert JSON to dict and print
        # print(resp_json)
        if len(resp_json ) < 1:
            print("it is already empty!")
            return

        for worker in resp_json :
            print('deleting worker: ',worker) 
            url = "http://127.0.0.1:8000/kpdata/workers/" + str(worker['worker_code']) + ""
            #print(url)
            response = requests.delete(url,  headers={ 
                    'Authorization': 'Token {}'.format(self.access_token)}
                )
            print(response.text )



    def select_all_orders___TODO(current_day=None):
        url = "http://localhost:5000/api/v1/workorder"
        if current_day is not None:
            url = 'http://localhost:5000/api/v1/workorder/?q=(filters:!((col:requested_start_date,opr:eq,value:{})),order_columns:order_code,order_direction:desc)' \
                .format(datetime.strftime(current_day,config.KANDBOX_DATE_FORMAT))
            # ,columns:!(order_code,name,planning_status,requested_start_date,scheduled_start_time,geo_latitude,geo_longitude,fixed_date_time_flag,requested_start_time,requested_duration_minutes)
            print(url)
        response = requests.get(url,  headers={'Content-Type':'application/json',
                    'Authorization': 'Token {}'.format(self.access_token)}
                )
        resp_json = response.json()
        
        return(resp_json)

    def select_orders_by_workers_TODO(workers=[]):
        url = "http://localhost:5000/api/v1/workorder"
        response = requests.get(url,  headers={'Content-Type':'application/json',
                    'Authorization': 'Token {}'.format(self.access_token)}
                )
        resp_json = response.json()
        
        return(resp_json)

    def insert_all_orders(self, jobs_list):
        url = "http://127.0.0.1:8000/kpdata/jobs/" 
        for myobj in jobs_list:
            # print('adding order: ',order)  
            response = requests.post(url, json=myobj, headers={'Content-Type':'application/json',
                    'Authorization': 'Token {}'.format(self.access_token)}
                )
            # print(response)
            # Convert JSON to dict and print
            print(response.json())
            
    

    def delete_all_orders(self):
        url = "http://127.0.0.1:8000/kpdata/jobs/"   # http://localhost:5000/api/v1/workorder/1"
        response = requests.get(url,  headers={'Content-Type':'application/json',
                    'Authorization': 'Token {}'.format(self.access_token)}
                )
        resp_json = response.json()
            # Convert JSON to dict and print
        # print(resp_json)
        if len(resp_json)  < 1:
            print("it is already empty!")
            return

        for worker in resp_json :
            print('deleting order: ',worker) 
            url = "http://127.0.0.1:8000/kpdata/jobs/" + str(worker['job_code']) + ""
            print(url)
            response = requests.delete(url,  headers={ 
                    'Authorization': 'Token {}'.format(self.access_token)}
                )
            print(response.text )


    '''
    def dispatch_all_generated_orders___(self,GENERATOR_START_DATE, TRAINING_DAYS, max_exe_time):
        from kandbox_planner.fsm_adapter.kplanner_db_adapter import  KPlannerDBAdapter
        kplanner_db = KPlannerDBAdapter() 
        nbr_days_in_batch = 1

        for day_i in range(TRAINING_DAYS) : #GENERATOR_RANGE):
            current_day = GENERATOR_START_DATE + timedelta(days=day_i) 
            workers, workers_id_dict = kplanner_db.load_transformed_workers(start_day = current_day, nbr_days = nbr_days_in_batch) 

            jobs_orig = kplanner_db.load_jobs_original( workers_id_dict , start_day = current_day, nbr_days = 1)

            if len(jobs_orig) < 1:
                print("it is empty, nothing to dispatch!")
                return
            # _EMP = ['3:4', '12:5', '21:4','4:55', '12:50', '21:50' ]
            _EMP = []
            for ii, e in enumerate(workers):
                _EMP.append("{}:{}".format(e['geo_latitude'], e['geo_longitude']))   

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
            print({'loaded day':current_day, "job count": len(current_shifts)}) # , 'shift':current_shifts, 'emp': _EMP})
            worker_day = dispatch_jobs(shifts= current_shifts, emps = _EMP, max_exe_time=max_exe_time)
            if len(worker_day) < 1:
                print("no data returned!")
                return 
                #save_one_day_dispatched_orders(worker_day, workers, kplanner_db)

            job_list = []
            for w_i in range(len(worker_day)):
                for task in worker_day[w_i][:-1]:
                    task_id = task[0]  # + 1
                    worker_code = workers[w_i] ['worker_code']
                    # updated_order =  {} # latest_order_dict[id]
                    job_list.append ({  
                        "job_code": current_shifts[task_id][6], 
                        "planning_status": "V", 
                        "scheduled_worker_code": worker_code,
                        "scheduled_start_day": datetime.strftime(current_day,config.KANDBOX_DATE_FORMAT),
                        "scheduled_start_minutes": task[1]  ,
                        "scheduled_duration_minutes":  task[2]  ,  
                        } ) 
                    ' ''
                        "actual_worker_code": worker_code,
                        "actual_start_day": datetime.strptime(current_day,KANDBOX_DATE_FORMAT),
                        "actual_start_minutes":  task[1] , 
                        "actual_duration_minutes": task[2] ,  
                        ' ''
            job_df = pd.DataFrame(job_list)
            job_df['planner_code'] = 'opti'
            job_df['effective_from_date'] = datetime.now()
            
            kplanner_db.save_schedued_jobs(job_df)
    '''
    #def save_one_day_dispatched_orders(worker_day, workers, kplanner_db ): 





    def get_access_token(self,login_info):
        # Get this one from web page, or request from admin user.
        
        return '27a46ebfec40d1c2079095837a5a93a831251ea8'

        
        url = "http://127.0.0.1:8000/kpdata/api-auth/login/"
        #print(login_info)
        response = requests.post(url, json=login_info,  headers={'Content-Type':'application/json'} )
        resp_json=response.json()
        print(resp_json) 
        #print(resp_json['access_token'])

        return resp_json['access_token']

        # = 0 # 
        



if __name__ == '__main__': 

    # /5 minutes
    # GPS fixed


    _SHIFTS =  [
        [0, 'FS', '7:12', 108, 60, 32],   [1, 'N', '8:3', 26, 68, 22],   [2, 'N', '06:4', 66, 121, 25], 
        [3, 'FS', '15:5', 20, 72, 12],    [4, 'N', '11:4', 133, 189, 16], [5, 'N', '13:2', 2, 19, 17], 
        [6, 'FS', '20:5', 91, 131, 34],   [7, 'N', '21:7', 8, 30, 52],   [8, 'FS', '3:45', 180, 190, 60], 
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

    #for i in range(10):
    #    print(get_normalized_location(i))

    GENERATOR_START_DATE =  datetime.strptime('20190101', config.KANDBOX_DATE_FORMAT )
    GENERATOR_RANGE = 5

    '''
    delete_all_workers()
    insert_all_workers(worker_list)

    delete_all_orders()
    generate_and_save_orders(GENERATOR_START_DATE =  GENERATOR_START_DATE, TRAINING_DAYS=GENERATOR_RANGE,  current_shifts = _SHIFTS,  worker_list = worker_list) # This genearte 450 orders 
    '''
    