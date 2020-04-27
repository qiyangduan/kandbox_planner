import numpy as np
import random
class KPRLAgentRandomGuess4HistoryAffinity:
    env = None
    trained_model = None

    action_size = 2

    def __init__(self, env = None):     
        self.env = env

    def _build_model(self, input_size, output_size):
        
        return None

    def load_model(self, filename):
        self.trained_model = None

    def train_model(self, training_data):
        return {'message':'void model for random guess'}


    def predict_action( self, observation = None):
        
        curr_job = self.env.jobs[self.env.current_job_i]
        worker_index = random.randint(0, self.env.config['nbr_of_observed_workers'] - 1)
        worker_np = np.zeros(len(self.env.workers)  )
        worker_np[worker_index ] = 1 

        duration = np.zeros(1  )
        duration[0] = curr_job['requested_duration_minutes']
        day_i = np.zeros(1  )
        day_i[0] = random.randint(0,  self.env.config['nbr_of_days_planning_window'] - 1) 
        requested_start_minutes = np.zeros(1  )
        requested_start_minutes[0] = curr_job['requested_start_minutes']  
        shared_worker_count = np.zeros(1  )
        shared_worker_count[0] = 1


        return (worker_np,
            duration,
            day_i,
            requested_start_minutes,
            shared_worker_count
        )
        '''
        n = np.zeros(len(self.env.workers) + 4 )
        
        day_i = random.randint(0,  self.env.config['nbr_of_days_planning_window'] - 1) 

        n[worker_index ] = 1 
        n[-4] = curr_job['requested_duration_minutes']  # ['actual_start_minutes'] / 1600 # 288
        n[-3] = day_i    # ['actual_start_minutes'] / 1600 # 288
        n[-2] = curr_job['requested_start_minutes']  
        n[-1] = 1 # ['shared_worker_count']  


        return n
        '''