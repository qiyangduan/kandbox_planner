import random
import numpy as np



class HeuristicAgentSingleJobByHistory:
    env = None
    trained_model = None
    MAX_EPOCHS = 30
    nbr_of_actions = 4


    def __init__(self, env = None,trained_model=None, MAX_EPOCHS=30, nbr_of_actions = None):     
        self.env = env
        self.MAX_EPOCHS = MAX_EPOCHS
        self.trained_model = trained_model
        if nbr_of_actions:
            self.nbr_of_actions = nbr_of_actions

    def load_model(self, filename):
        pass

    
    def train_model(self, training_data=None, model_path = None):
        return

    def _check_for_action_on_free_slots(self, curr_worker_code, curr_job): 
        curr_loc = curr_job['job_gps']
        for day_i in range(len(self.env.workers_dict[curr_worker_code]['free_time_slots'])):
            for free_time_slot in self.env.workers_dict[curr_worker_code]['free_time_slots'][day_i]:
                if free_time_slot[2] == 'HOME':
                    start_loc = self.env.workers_dict[curr_worker_code] ['home_gps']
                elif free_time_slot[2] == 'JOB':
                    start_loc = self.env.jobs[free_time_slot[3]] ['job_gps']
                else:
                    print("wrong start point!!!!")
                    return []

                if free_time_slot[4] == 'HOME':
                    end_loc = self.env.workers_dict[curr_worker_code] ['home_gps']
                elif free_time_slot[4] == 'JOB':
                    end_loc = self.env.jobs[free_time_slot[5]] ['job_gps']
                else:
                    print("wrong start point!!!!")
                    return []


                prev_travel_time = self.env.travel_router.get_travel_minutes_2locations(start_loc, curr_loc)
                next_travel_time = self.env.travel_router.get_travel_minutes_2locations(curr_loc, end_loc)
                travel_time = prev_travel_time + next_travel_time

                if free_time_slot[1] - free_time_slot[0] > travel_time + curr_job['requested_duration_minutes']: #TODO scheduled
                    n = np.zeros(len(self.env.workers_dict) + 4 )
                    n[self.env.workers_dict[curr_worker_code]['worker_index'] ] = 1 
                    n[-4] = curr_job['requested_duration_minutes']   
                    n[-3] = day_i   # ['actual_start_minutes'] / 1600 # 288
                    n[-2] = free_time_slot[0] + prev_travel_time   # ['actual_start_minutes'] / 1600 # 288
                    n[-1] = 1 # ['shared_worker_count']  
                    return n
        return []

    def predict_action_list( self, job_code = None, observation = None):
        actions = []
        env = self.env

        if job_code is None:
            job_i = env.current_job_i
        else:
            job_i = env.jobs_dict[job_code]['job_index']

        curr_job = self.env.jobs[job_i]
        workers_to_check = []
        workers_to_check.append(curr_job['requested_worker_code'])



        # {'Duan': 4, 'Jim': 1, 'Tom': 4} --> {'Duan': 4, 'Jim': 1, 'Tom': 4} 
        #  2020-04-09 08:43:37 Changed Dict to List, and removed # .items()
        hist_job_workers_ranked = [[k,v] for k, v in sorted(curr_job['job_historical_worker_service_dict'], key=lambda item: item[1], reverse=True)]
        for hist_worker_count in hist_job_workers_ranked:
            # print(hist_worker_count)
            curr_worker_code = hist_worker_count[0]
            workers_to_check.append(curr_worker_code)

        # action_count = 0
        for a_worker_code in hist_job_workers_ranked:
            if len(actions) >= self.nbr_of_actions:
                return actions

            action = self._check_for_action_on_free_slots(a_worker_code[0], curr_job)
            if len(action) > 0:
                actions.append(action)
                #action_count += 1

        return actions

    def predict_action( self, observation = None):
        actions = self.predict_action_list(observation = observation)
        if len(actions) > 0:
            return actions[0]

