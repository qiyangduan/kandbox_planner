'''
This is right after migrating last V2 env. refer to xls design file. -- Entrada_v2
/Users/qiyang/Documents/qduan/git/work_git/field_service_robot/doc/dispatch_ai_model_design.xlsx


step 1: move rules out of env definition.
step 2: Then I will change network layout to multiple input (cnn + dense)
https://www.pyimagesearch.com/2019/02/04/keras-multiple-inputs-and-mixed-data/
/Users/qiyang/Downloads/Houses-dataset

https://medium.com/datadriveninvestor/dual-input-cnn-with-keras-1e6d458cd979


adapted from kprl_env_v2_merged_timeslot.py
'''

# This version works on top of json input and produce json out
# Observation: each worker has multiple working_time=days, then divided by slots, each slot with start and end time, 

import gym
from gym import spaces

import sys
import numpy as np 
import random
import math  
import kandbox_planner.util.planner_date_util  as date_util
from datetime import datetime, timedelta

#from collections import OrderedDict

from kandbox_planner.util.travel_time  import  HaversineTravelTime  

from kandbox_planner.planner_engine.rl.env.kprl_reward_function import  kprl_rule_set
 
from kandbox_planner.fsm_adapter.kplanner_db_adapter import  KPlannerDBAdapter 
import pandas as pd
# For each task [ [start, end], gps[x,y], duration_left]
# for each agent [gps-x,y   task(start_time_with_travel   end_time)]

class KPlannerHistoryAffinityTopNGMMEnv(gym.Env):
  """
    Has the following members 
    Action should be compatible with GYM, then it should be either categorical or numerical. No dictionary.
  # action['worker_code'],
  # action['start_day_i'],
  # action['start_minutes'] or action['insert_job_i'] 

    New design of actions are: 
    [
      vector of worker1_prob, worker2_prob (for N workers),
      start_day_i, job_start_minutes, shared_worker_count (shared = 1..M)
    ]

  # Benefit of using start_minutes is that I can use start minutes to find insert job i
  # but it is bigger value space for algorithm to decide.
  """
  metadata = {'render.modes': ['human']} 
  config = {
    'run_mode' : 'normal', # 'replay' for replay Planned jobs, where allows conflicts. "normal" for training new jobs and predict.
    'planner_code' : 'hist_affinity',
    'allow_overtime' : False,
    #
    'nbr_of_observed_workers':6,
    'nbr_of_days_planning_window':2,
    'data_start_day':'20191105',
    #

    'minutes_per_day':60*24,
    # 'reversible' : True, # if yes, I can revert one step back.
    'max_nbr_of_jobs_per_day_worker': 25,
    # 'rule_set':kprl_rule_set,
  }

  def __init__(self, workers=None, jobs=None, env_config = None, from_db=True):     
    # each worker is a list of dict, internally transform to : 
    # dictionary ojbect, {job_code: { id , active, level,  gps: [x, y], total_free_duration, free_time_slots: [start, end], },... }

    if env_config:
      for x in env_config.keys():
        self.config[x]  = env_config[x]

    if 'data_end_day' in self.config.keys():
      self.config['nbr_of_days_planning_window'] = date_util.days_between_2_day_string(start_day=self.config['data_start_day'], end_day=self.config['data_end_day'])

    self.kplanner_db = KPlannerDBAdapter()
  
    if from_db:
      workers, workers_id_dict = self.kplanner_db.load_transformed_workers (start_day = self.config['data_start_day']) # ['result'] , nbr_days = self.config['nbr_of_days_planning_window']
      jobs = self.kplanner_db.load_transformed_jobs_current( start_day = self.config['data_start_day'], nbr_days = self.config['nbr_of_days_planning_window'])

    self.workers = workers
    self.jobs = jobs  # list of dict


    self.workers_dict = {} # Dictionary of dict
    self.jobs_dict = {} # Dictionary of dict
    # jobs = sorted(jobs_raw, key = lambda job: job['planning_status'])

    self.travel_router = HaversineTravelTime(travel_speed=60)
    self.rule_set = kprl_rule_set

    self._set_spaces()

    if len(self.jobs) < 1:
      print("No Jobs.")
      return
    self.reset()


  def reset(self, shuffle_jobs=False):
    self.current_job_i = 0
    self.current_observed_worker_list = self._get_sorted_worker_code_list(self.current_job_i)
    self.total_travel_time = 0
    self.total_assigned_job_duration = 0 


    for ji, x in enumerate(self.workers):
      self.workers_dict[x["worker_code"]]  = x   
      x["worker_index"]  = ji   


    for ji, job in enumerate(self.jobs):
      self.jobs_dict[job["job_code"]]  = job  
      job["job_index"] = ji
      job["assigned_workers"] = [] #[ {worker_code_1,}  {worker_code_2}  {worker 3 }]   -- start_minutes,  end_minutes


    for w in self.workers_dict.keys():
      # List of jobs assigned to each worker. Each one is { job_index: job_i, "travel_minutes", }   -- "start", "end" 
      # For now, do not consider different start/end for different workers. 
      self.workers_dict[w]["assigned_jobs"] = []  
      # total_free_duration, 
      # free_time_slots: for everyday, [[start_minutes, end_minutes, start_position_type, start_code, gps_end]]. When there is FS, it cut off one day into two slots
 
      self.workers_dict[w]['free_time_slots']  = [] 
      
      # NOT DEFAULT list(map(lambda x: [[x[0], x[1], 'HOME', None, 'HOME', None ]], self.workers_dict[w]['working_minutes']))
      # This time I make free time same as assigned job, all linearly flattened for all days.
      for day_i in range(self.config['nbr_of_days_planning_window']):  
        if True: # [0,0] is also appendded. self.workers_dict[w]['working_minutes'][day_i][0] < self.workers_dict[w]['working_minutes'][day_i][1] :
          # self.workers_dict[w]['free_time_slots'].append([self.workers_dict[w]['working_minutes'][day_i][0] + (day_i * self.config['minutes_per_day']), self.workers_dict[w]['working_minutes'][day_i][1]  + (day_i * self.config['minutes_per_day']), 'HOME', None, 'HOME', None ])
          self.workers_dict[w]['free_time_slots'].append(
            [
                [   self.workers_dict[w]['working_minutes'][day_i][0], 
                    self.workers_dict[w]['working_minutes'][day_i][1], 
                    'HOME', None, 'HOME', None 
                ]
            ])

    if shuffle_jobs:
      random.shuffle(self.jobs)


    return self._get_observation()

  def step(self, action ):
    # action [1, 0, 0 ]. One hot coding, 1 means this worker take the job.


    add_result, info = self._add_current_job_to_worker(action)  
    # print("Adding job {}--{} to Worker {}-{} , result: {}...".format(self.current_job_i - 1, self.jobs[self.current_job_i - 1]['job_code'],action['worker_code'],action['start_minutes'],add_result ))
    done = info['done']
    
    if add_result == False:
        # done = True
        info['message'] = 'error'
        #reward = self._get_reward() # 0
    # break
    else:
      info['message'] = 'ok'
      if self.current_job_i == len(self.jobs ) :
        done = True
        print('No more unplanned jobs, done. internal error? never be here!')
        #reward = self._get_reward() # 1
    reward = self._get_reward()
    obs = self._get_observation()
    return (obs, reward, done, info)


  def render(self, mode='human'):
    pass

  def _commit_changed_jobs(self): 
    jobs = self.kplanner_db._convert_df_day_minutes_to_datetime( jobs_df= pd.DataFrame(self.get_solution_json()))

    # for job in jobs:
    for index, job in jobs.iterrows():
      if job['changed_flag'] == 1:
        #TODO
        job['last_update_by'] = 'rl_heur'
        self.kplanner_db.update_single_job(job)
        self.jobs_dict[job['job_code']]['changed_flag'] = 0
        print('Saved job {} to DB.', job['job_code'])


  def get_solution_json(self): 
    job_solution=[] 
    inplanning_job_index_list = []
    shared_prev_jobs = {}
    for worker_code in  self.workers_dict.keys():
      pre_job_code = '__HOME'
      # for work_time_i in  range(len( self.workers_dict[worker_code]['assigned_jobs'] ) ): # nth assigned job time unit.  
      for assigned_job in   self.workers_dict[worker_code]['assigned_jobs'] :
        # print(work_time_i)
        job_index = assigned_job ['job_index']

        start_time_minute = self.jobs[job_index]['assigned_start_minutes']

        if len(self.jobs[job_index]['assigned_workers']) < 1:
          print("Wierd, why no worker?")
          continue
        # Only single worker jobs are collected in this loop. 
        if len(self.jobs[job_index]['assigned_workers']) == 1:
          #changed flag is moved to step()


          self.jobs[job_index]['scheduled_share_status'] = 'N'
          self.jobs[job_index]['scheduled_start_minutes'] = start_time_minute % self.config['minutes_per_day']
          self.jobs[job_index]['scheduled_start_day'] = date_util.add_days_2_day_string(k_day = self.config['data_start_day'], days = math.floor( start_time_minute / self.config['minutes_per_day'] ) )
          self.jobs[job_index]['requested_start_day'] = self.jobs[job_index]['requested_start_day']  #  date_util.add_days_2_day_string(k_day = self.config['data_start_day'], days =  self.jobs[job_index]['requested_start_day'] )
          self.jobs[job_index]['scheduled_worker_code'] = self.jobs[job_index]['assigned_workers'][0]
          self.jobs[job_index]['scheduled_travel_prev_code'] = pre_job_code
          self.jobs[job_index]['scheduled_travel_minutes_before'] = assigned_job['travel_minutes']
          self.jobs[job_index]['scheduled_duration_minutes'] = self.jobs[job_index]['requested_duration_minutes']

          if (self.jobs[job_index]['job_code'] == '0424-20-FS')   :
            print('pause for debug')

          job_solution.append(self.jobs[job_index])
          inplanning_job_index_list.append(job_index)

        if len(self.jobs[job_index]['assigned_workers']) > 1:
          for worker_code in self.jobs[job_index]['assigned_workers']:
            shared_prev_jobs[(worker_code, job_index)] = pre_job_code

        pre_job_code = self.jobs[job_index]['job_code']
        
    # This loop collects Only multiple workers (shared) jobs. 
    for job_index, job in  enumerate(self.jobs):
      if job['job_code'] == '89206950_1_MT_2_11':
        print('pause for debug')
      if len(self.jobs[job_index]['assigned_workers']) <= 1:
        continue 

      # 2020-04-23 14:27:44
      # Staring Here ['assigned_workers'] > 1, which means those are secondary technicians.
      # Very likely, it won't go down from hre
      print('warning, jobs are not picked up from works ...')
      inplanning_job_index_list.append(job_index)
      for a_index, worker_code in  enumerate(self.jobs[job_index]['assigned_workers']): 
        curr_job = self.jobs[job_index].copy()
        #if curr_job['planning_status'] == 'U':
        #  curr_job['planning_status'] = 'I'
        #  curr_job['changed_flag'] = 1  

        curr_job['requested_start_day'] = curr_job['requested_start_day']  #  date_util.add_days_2_day_string(k_day = self.config['data_start_day'], days =  curr_job['requested_start_day'] )
        curr_job['scheduled_worker_code'] = curr_job['assigned_workers'][a_index]
        curr_job['scheduled_duration_minutes'] = curr_job['scheduled_duration_minutes']

        start_time_minute = self.jobs[job_index]['assigned_start_minutes']
        curr_job['scheduled_start_minutes'] = start_time_minute % self.config['minutes_per_day']
        curr_job['scheduled_start_day'] = date_util.add_days_2_day_string(k_day = self.config['data_start_day'], days = math.floor( start_time_minute / self.config['minutes_per_day'] ) )

        if a_index == 0:
          curr_job['scheduled_share_status'] = 'P'
        else:
          curr_job['scheduled_share_status'] = 'S'
          curr_job['job_code'] = '{}___{}_{}'.format( curr_job['job_code'] ,  curr_job['scheduled_share_status'] ,  curr_job['scheduled_worker_code'] )



        curr_pre_job_code = shared_prev_jobs[(worker_code, job_index)] 
        if  curr_pre_job_code == '__HOME':
          curr_job['scheduled_travel_prev_code'] = None
          curr_job['scheduled_travel_minutes_before'] = 0
        else:
          curr_job['scheduled_travel_prev_code'] = curr_pre_job_code
          curr_job['scheduled_travel_minutes_before'] = self._get_travel_time_2jobs(job_index, self.jobs_dict[curr_pre_job_code]['job_index'])
        # self.workers_dict[worker_code]['assigned_jobs'] [work_time_i] ['travel_minutes']

        if (curr_job['job_code'] == '0424-20-FS')   :
          print('pause for debug')


        job_solution.append(curr_job)



    for job_index, job in  enumerate(self.jobs):
      if job_index in inplanning_job_index_list:
        continue
      self.jobs[job_index]['planning_status'] = 'U'
      self.jobs[job_index]['scheduled_start_minutes'] = self.jobs[job_index]['requested_start_minutes']
      self.jobs[job_index]['scheduled_start_day'] = self.jobs[job_index]['requested_start_day']  # date_util.add_days_2_day_string(k_day = self.config['data_start_day'], days = self.jobs[job_index]['requested_start_day'] )
      self.jobs[job_index]['requested_start_day'] = self.jobs[job_index]['requested_start_day']  # date_util.add_days_2_day_string(k_day = self.config['data_start_day'], days =  self.jobs[job_index]['requested_start_day'] )
      self.jobs[job_index]['scheduled_duration_minutes'] = self.jobs[job_index]['requested_duration_minutes']
      self.jobs[job_index]['scheduled_worker_code'] = self.jobs[job_index]['requested_worker_code']
      self.jobs[job_index]['scheduled_travel_prev_code'] = '__HOME'
      self.jobs[job_index]['scheduled_travel_minutes_before'] = 0

      job_solution.append(self.jobs[job_index])



    return job_solution


  def close(self):
    pass



  # **---------------------------------------------------------------------------- 
  # ## Extended functions
  # **---------------------------------------------------------------------------- 

  def replay_env(self):
      if len(self.jobs) < 1:
        return
      # I P U   (x[1], x[2])
      sorted_jobs = sorted(self.jobs, key = lambda job: (job['planning_status'], job['job_code']))
      self.jobs=sorted_jobs
      observation = self.reset(shuffle_jobs=False) 
      self.config['run_mode'] = 'replay'
      # previous_observation = self._get_observation() 
      for step_index in range(0,len(self.jobs)): 
        if self.current_job_i >= len(self.jobs):
          break
        if self.jobs[self.current_job_i]['planning_status'] not in ['I','P','C']:
          print('Replayed until first U-status, self.current_job_i = ', self.current_job_i)
          return observation 
          # break
        action = self.gen_action_from_one_job(  self.jobs[self.current_job_i] )
        action_dict = self.decode_action_into_dict(action)
        if (action_dict['assigned_start_day_n_minutes'] < 0) | \
           (action_dict['assigned_start_day_n_minutes'] > self.config['nbr_of_days_planning_window'] * 24*60 ):
           # Skip this one for replay
           self.current_job_i +=1
           continue
        observation, reward, done, info = self.step(action) 
        previous_observation = observation
        if  info=='error':
          print('Error game replay got error, but it will continue: {}, steps: {}, info: {}, current_job_i: {} '.format(\
              '?', step_index,  info, self.current_job_i  ))
          self.current_job_i +=1
        if done :
          print('Game replay got message done, but it will continue: {}, steps: {}, info: {}, current_job_i: {} '.format(\
                '?', step_index,  info, self.current_job_i  ))
          # break
          self.current_job_i +=1
      print('Replayed until an unknown situation, please investigate. self.current_job_i = ', self.current_job_i)
      return observation 
      
  

  def add_job(self, new_job):
    # I assume it is Unplanned for now, 2020-04-24 07:22:53. 
    # No replay
    if new_job['job_code']  in self.jobs_dict.keys():
      print('error, job already existed: ', new_job['job_code'] )
    else:
      self.jobs.append(new_job) 
      job_index = len(self.jobs)-1
      new_job["job_index"] = job_index
      new_job["assigned_workers"] = [] #[ {worker_code_1,}  {worker_code_2}  {worker 3 }]   -- start_minutes,  end_minutes

      self.jobs_dict[new_job["job_code"]]  = new_job  

  # ***************************************************************
  # # Internal functions
  # ***************************************************************

  def _set_spaces(self): 
    '''
    self.observation_space = spaces.Dict({ 
      # spaces.Tuple(x,y)
      "assignment.start_longitude": spaces.Box(low=-1.0, high=1, shape=(self.config['nbr_of_observed_workers'], self.config['nbr_of_days_planning_window']), dtype=np.float32), 
      "assignment.start_latitude": spaces.Box(low=50, high=53, shape=(self.config['nbr_of_observed_workers'], self.config['nbr_of_days_planning_window']), dtype=np.float32), 
      "assignment.max_available_working_slot_duration": spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(self.config['nbr_of_observed_workers'], self.config['nbr_of_days_planning_window']), dtype=np.float32), 
      # "job.features": spaces.Box( (, spaces.Discrete(2),) ),
      "job.requested_duration_minutes": spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(1,), dtype=np.float32), 
      "job.mandatory_minutes_minmax_flag": spaces.Discrete(2), 
      "job.requested_start_minutes": spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(1,), dtype=np.float32), 
      
      #"job.preferred_minutes_minmax_flag": spaces.Discrete(2), 
      # "job.requested_start_max_minutes": spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(1,), dtype=np.float32), 
      })

    self.action_space = spaces.Dict({ 
      # spaces.Tuple(x,y)
      "worker_day_score": spaces.Box(low=-1.0, high=1, shape=(self.config['nbr_of_observed_workers'], self.config['nbr_of_days_planning_window']), dtype=np.float32), 
      "scheduled_start_minutes": spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(1,), dtype=np.float32), 
      "scheduled_duration_minutes": spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(1,), dtype=np.float32), 
      "nbr_of_scheduled_workers": spaces.Box(low=0, high=self.config['nbr_of_observed_workers'], shape=(1,), dtype=np.float32), 
      })
   self.action_space = spaces.Tuple((
      # * self.config['nbr_of_days_planning_window']
      spaces.Box(low=0, high=1, shape=(self.config['nbr_of_observed_workers'],), dtype=np.float32), 
      spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(1,), dtype=np.float32),  # Duration
      spaces.Box(low=0, high=self.config['nbr_of_days_planning_window'], shape=(1,), dtype=np.float32),  #day_i
      spaces.Box(low=0, high=self.config['minutes_per_day'], shape=(1,), dtype=np.float32), 
      spaces.Box(low=0, high=self.config['nbr_of_observed_workers'], shape=(1,), dtype=np.float32), 
      ))
 
     '''

    self.observation_space = spaces.Tuple( ( 
      spaces.Box(low=-1, high=1, shape=(self.config['nbr_of_observed_workers']*self.config['nbr_of_days_planning_window'], ), dtype=np.float32), 
      spaces.Box(low=50, high=53, shape=(self.config['nbr_of_observed_workers']*self.config['nbr_of_days_planning_window'],), dtype=np.float32), 
      spaces.Box(low=-1, high=1, shape=(self.config['nbr_of_observed_workers']*self.config['nbr_of_days_planning_window'], ), dtype=np.float32), 
      spaces.Box(low=50, high=53, shape=(self.config['nbr_of_observed_workers']*self.config['nbr_of_days_planning_window'],), dtype=np.float32), 
      spaces.Box(low=-1, high=1, shape=(self.config['nbr_of_observed_workers']*self.config['nbr_of_days_planning_window'], ), dtype=np.float32), 
      spaces.Box(low=50, high=53, shape=(self.config['nbr_of_observed_workers']*self.config['nbr_of_days_planning_window'],), dtype=np.float32), 
      #
      #f_nbr_of_jobs,                                     
      spaces.Box(low=0, high=self.config['max_nbr_of_jobs_per_day_worker']+1, shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                                   
      #f_total_travel_minutes,                            
      spaces.Box(low=0, high=self.config['minutes_per_day']*self.config['nbr_of_days_planning_window'], shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                        
      #f_first_job_start_minutes,                         
      spaces.Box(low=0, high=self.config['minutes_per_day']*self.config['nbr_of_days_planning_window'], shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                             
      #f_total_occupied_duration,                         
      spaces.Box(low=0, high=self.config['minutes_per_day']*self.config['nbr_of_days_planning_window'], shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                         
      #f_total_unoccupied_duration,                       
      spaces.Box(low=0, high=self.config['minutes_per_day']*self.config['nbr_of_days_planning_window'], shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                           
      #                                                  
      #f_max_available_working_slot_duration,             
      spaces.Box(low=0, high=self.config['minutes_per_day']*1, shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                                     
      #f_max_available_working_slot_start,                
      spaces.Box(low=0, high=self.config['minutes_per_day']*self.config['nbr_of_days_planning_window'], shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                                  
      #f_max_available_working_slot_end,                  
      spaces.Box(low=0, high=self.config['minutes_per_day']*self.config['nbr_of_days_planning_window'], shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                         
      #f_max_unoccupied_rest_slot_duration,               
      spaces.Box(low=0, high=self.config['minutes_per_day']*1, shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                             
      #f_total_available_working_slot_duration,           
      spaces.Box(low=0, high=self.config['minutes_per_day']*1, shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                                
      #f_min_available_working_slot_duration,             spaces.Box(low=0, high=self.config['minutes_per_day']*1, shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                              
      #f_min_available_working_slot_start,                spaces.Box(low=0, high=self.config['minutes_per_day']*self.config['nbr_of_days_planning_window'], shape=(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'],), dtype=np.float32),                            
      #f_min_available_working_slot_end,                                            

      spaces.Discrete(2), 
      spaces.Box(low=0, high=self.config['minutes_per_day']+1, shape=(1,), dtype=np.float32), 
      # Maximum 8 hours
      spaces.Box(low=0, high=self.config['minutes_per_day']/3, shape=(1,), dtype=np.float32),  
      ))

    action_low = np.zeros(self.config['nbr_of_observed_workers'] + 4 )
    action_high = np.ones(self.config['nbr_of_observed_workers'] + 4 )
    #action_low[0:self.config['nbr_of_observed_workers']] = 0
    #action_high[0:self.config['nbr_of_observed_workers']] = 1

    action_high[self.config['nbr_of_observed_workers']+0] = self.config['minutes_per_day']
    action_high[self.config['nbr_of_observed_workers']+1] = self.config['nbr_of_days_planning_window']
    action_high[self.config['nbr_of_observed_workers']+2] = self.config['minutes_per_day']
    action_high[self.config['nbr_of_observed_workers']+3] = 2

    self.action_space = spaces.Box(low=action_low, high=action_high, dtype=np.float32)
    
  def _get_travel_time_2jobs(self, job_index_1, job_index_2): 
    return self.travel_router.get_travel_minutes_2locations(
      [self.jobs[job_index_1]['geo_longitude'], self.jobs[job_index_1]['geo_latitude']] ,
      [self.jobs[job_index_2]['geo_longitude'], self.jobs[job_index_2]['geo_latitude']]
    )

  def _get_sorted_worker_code_list(self, job_index):
    #TODO
    return list(self.workers_dict.keys())[0:self.config['nbr_of_observed_workers']]

  def _check_current_job_to_worker(self, a_dict) : # worker_index, working_time_index):
    # a_dict = self.decode_action_into_dict(action)
    # max_i = np.argmax(action[0:len(self.workers_dict)])
    action_day =  a_dict['scheduled_start_day']
    job_start_time =  a_dict['assigned_start_day_n_minutes']
    if job_start_time < 0:
      return False, {'internal_error': {'score':-1,'message': 'job_start_time < 0'}}
    if job_start_time > self.config['nbr_of_days_planning_window'] * self.config['minutes_per_day']:
      return False, {'internal_error': {'score':-1,'message': "job_start_time > self.config['nbr_of_days_planning_window'] * self.config['minutes_per_day']"}}

    # TODO Redundant
    if action_day >= self.config['nbr_of_days_planning_window']:
      return False, {'internal_error': {'score':-1,'message':"action_day >= self.config['nbr_of_days_planning_window']"}}

    bool_score = True
    all_results = {}
    for worker_code in  [ a_dict['scheduled_worker_code'] ] +  a_dict['scheduled_related_worker_code'] :
      if worker_code not in  self.workers_dict.keys():
        return False, {'internal_error': {'score':-1,'message': 'worker_code={} not in  self.workers_dict.keys()'.format(worker_code)}}

      # Check for all external business rules.
      for rule in self.rule_set.action_rule_list:
        result = rule.evalute_action_normal(env=self, action_dict = a_dict)
        all_results[rule.rule_code] = result
        if result['score'] == -1:
          bool_score = False

      #2020-04-12 12:35:58 Merged into previous one.
      '''
      travel_check_result = self.rule_set.sufficient_travel_reward.evalute_action_normal(env = self, action = action)
      if travel_check_result['score'] == -1:
        return False
      '''
    return bool_score, all_results


  def _cut_off_free_time_slot(self, 
    worker_code =  None,
    action_day = None,
    start_minutes = None, 
    end_minutes=None, 
    travel_minutes =  None,
    prev_job = None
    ) : 

    if prev_job is not None:
      prev_type = 'JOB'
      prev_job_index = prev_job['job_index']
      
    else:
      prev_type = 'HOME'
      prev_job_index = None
  
    # if worker_code== 'Harry': '0423-3-N
    if self.jobs[self.current_job_i]['job_code']== '0423-3-N': 
        print('pause for debug')

    if action_day >= self.config['nbr_of_days_planning_window']:
      return False # , {'internal_error': {'score':-1,'message':"action_day >= self.config['nbr_of_days_planning_window']"}}

    new_free_slot_i = -1
    satisfied = True
    # self.config['run_mode']
    # print(worker_code, self.workers_dict[worker_code]['free_time_slots'])
    for fi, free_slot in enumerate(self.workers_dict[worker_code]['free_time_slots'][action_day]):
      joined_period = date_util.clip_time_period(free_slot, [start_minutes - travel_minutes, end_minutes])
      # if ( free_slot[0] <= start_minutes - travel_minutes ) &  ( end_minutes <= free_slot[1]):
      if len(joined_period) > 1:
        # This free slot is intersecting with job period
        new_free_slot_i = fi
        if (start_minutes - travel_minutes < free_slot[0] ) | (end_minutes > free_slot[1] ):
          # This joined_period is larger than the current free_slot in either start or end.
          if self.config['run_mode'] != 'replay':
            return False
        else:
          # This joined_period is completely inside the current free_slot, so leave it to next processing
          break
        
        #Now the free_slot is only partially intersecting with job, either from front or back.
        prev_free_slot = self.workers_dict[worker_code]['free_time_slots'][action_day].pop(new_free_slot_i)
        # in case this free_slot is exactly the job duration
        if (start_minutes - travel_minutes == free_slot[0] ) & (end_minutes == free_slot[1] ):
          return True
        # Now at least one part of job_period is not in the current free_slot 
        satisfied = False
        if (start_minutes - travel_minutes <= free_slot[0] ) & (end_minutes >= free_slot[1] ):
          # Now this joined_period is superset of the current free_slot, then no insertion back any slot. It is simply pop-ed
          continue
        if (start_minutes - travel_minutes < free_slot[0] )  & (end_minutes < free_slot[1] ):
          self.workers_dict[worker_code]['free_time_slots'][action_day].insert(new_free_slot_i,
            [
              end_minutes,
              prev_free_slot[1],
              prev_type,
              prev_job_index,
              prev_free_slot[4],
              prev_free_slot[5],
            ]
          )
        elif (start_minutes - travel_minutes >= free_slot[0] )  & (end_minutes > free_slot[1] ):
          self.workers_dict[worker_code]['free_time_slots'][action_day].insert(new_free_slot_i,
            [
              prev_free_slot[0],
              start_minutes - travel_minutes,
              prev_free_slot[2],
              prev_free_slot[3],
              prev_type,
              prev_job_index,
            ]
          )



        # break 
    
    # self.config['run_mode'] 
    if new_free_slot_i < 0:
      return False
    if not satisfied:
      return False


    prev_free_slot = self.workers_dict[worker_code]['free_time_slots'][action_day].pop(new_free_slot_i)

    if ((self.config['run_mode'] == 'replay' )  | (self.jobs[self.current_job_i]['job_type'] == 'FS' )) \
      & (start_minutes != prev_free_slot[0]):
      # Split original pre_free_slot into two, minus the occupied slot


      # Now I insert second part, so that in the list, next time i insert in same place, it will be pushsed to 2nd.
      self.workers_dict[worker_code]['free_time_slots'][action_day].insert(new_free_slot_i,
        [
          start_minutes + self.jobs[self.current_job_i]['requested_duration_minutes'] ,
          prev_free_slot[1],
          'JOB',
          self.jobs[self.current_job_i]['job_index'],
          prev_free_slot[4],
          prev_free_slot[5],
        ]
      )
      # Now I insert first part !!!
      self.workers_dict[worker_code]['free_time_slots'][action_day].insert(new_free_slot_i,
        [
          prev_free_slot[0],
          start_minutes - travel_minutes,
          prev_free_slot[2],
          prev_free_slot[3],
          'JOB',
          self.jobs[self.current_job_i]['job_index'],
          #prev_type,
          #prev_job_index,
        ]
      )


    else:
      self.workers_dict[worker_code]['free_time_slots'][action_day].insert(new_free_slot_i,
        [
          start_minutes + self.jobs[self.current_job_i]['requested_duration_minutes'] ,
          prev_free_slot[1],

          # prev_type,
          # prev_job_index,
          # 'HOME',
          # None
          'JOB',
          self.jobs[self.current_job_i]['job_index'],
          prev_free_slot[4],
          prev_free_slot[5],

        ]
      )
    return True


  def _add_current_job_to_worker(self, action) : 
    #TODO If there is not enough capacities without considering travel and time slot, reject it

    # info={'messages':[]}

    a_dict = self.decode_action_into_dict(action)

    check_rule_ok, info = self. _check_current_job_to_worker(a_dict)
    if (not check_rule_ok) & ( self.config['run_mode'] != 'replay' ):
      info['done']=False
      return False, info # {'message':'ok'}


    if(self.jobs[self.current_job_i]['job_code'] in ['EVT_BT96_1_TM_20200408_0']): #  1070610_1_TRBSB_2_12  '89098138_1_TRBS_2_39','1070610_1_PESTS_1_91',
      print('pause for debug')


    # max_i = np.argmax(action[0:len(self.workers_dict)])
    action_day =  a_dict['scheduled_start_day']
    job_start_time = action_day * self.config['minutes_per_day']  + a_dict['scheduled_start_minutes']


    # worker_code =  a_dict['scheduled_worker_code']
    all_workers = [a_dict['scheduled_worker_code']] + a_dict['scheduled_related_worker_code']
    for w_i, worker_code in enumerate(all_workers):

      prev_job = None
      next_job = None
      new_job_loc_i=0  

      for job_i in range(len(self.workers_dict[worker_code]['assigned_jobs'])):
        a_job = self.jobs[
            self.workers_dict[worker_code]['assigned_jobs'][job_i]['job_index']
          ]
        if a_job['assigned_start_minutes'] < job_start_time:
          prev_job = a_job
        if a_job['assigned_start_minutes'] > job_start_time: # can not be equal
          next_job = a_job
          break
        new_job_loc_i+=1
      
      if prev_job:
        travel_minutes = self._get_travel_time_2jobs(prev_job['job_index'], self.current_job_i)
      else:
        travel_minutes = 0

      # now I am ready to add this new job
      # ++++++++++++++++++++++++++++++++++
      # 1. cut off free time
      # 2. insert job to work's assigned_list
      # ++++++++++++++++++++++++++++++++++

      cut_free_time_slot_ok = self._cut_off_free_time_slot( 
        start_minutes = a_dict['scheduled_start_minutes'] , #job_start_time , 
        end_minutes= a_dict['scheduled_start_minutes'] + a_dict['scheduled_duration_minutes'],
        travel_minutes = travel_minutes,
        worker_code = worker_code,
        action_day = action_day,
        prev_job =prev_job
        ) 
    
      if (not cut_free_time_slot_ok) & ( self.config['run_mode'] != 'replay' ):
        return False, {'done':False,'internal_error': {'score':-1,'message':["worker_code={}, (not cut_free_time_slot_ok) & ( self.config['run_mode'] != 'replay' )".format(worker_code)]}}

      if self.current_job_i == 28:
        print('pause for debug')
      self.workers_dict[worker_code]['assigned_jobs'].insert(new_job_loc_i, {
          'job_index': self.current_job_i,\
          'travel_minutes':travel_minutes 
          } )
    #if self.current_job_i == 28:
    #  print("pause for debug:", job_start_time)
    if self.jobs[self.current_job_i]['planning_status'] == 'U':
      self.jobs[self.current_job_i]['planning_status'] = 'I'
      self.jobs[self.current_job_i]['changed_flag'] = 1  
    self.jobs[self.current_job_i]['assigned_workers'] = all_workers #TODO for shared.
    self.jobs[self.current_job_i]['assigned_start_minutes'] = job_start_time # could be accross several days.
    self.jobs[self.current_job_i]['scheduled_duration_minutes'] = a_dict['scheduled_duration_minutes']  #TODO for shared. action['scheduled_duration_minutes']

    if self.config['run_mode'] == 'replay' :

      self.current_job_i+=1
      has_next = (self.current_job_i < len(self.jobs))
    else:
      has_next = self._move_to_next_job()
    if has_next:
      info['done'] = False
    else:
      info['done'] = True

    return True,info

  def _move_to_next_job(self):
    self.current_job_i +=1
    #if self.current_job_i >= len(self.jobs):
    #  return True
    for step_i in range(len(self.jobs)):
      if self.current_job_i>=len(self.jobs):
        self.current_job_i = 0
      if self.jobs[self.current_job_i]['planning_status'] == 'U':
        return True
      self.current_job_i+=1

    return False

  def _get_reward(self):
    reward = self.current_job_i / len(self.jobs )  # + ( 1 - self.total_travel_time / 60)
    if reward == 1:
      reward = 10

    return reward

  def _get_observation(self):
    # return {'workers': self.workers_dict, 'jobs':self.jobs}
    # return [1,5,4,3]

    return self._get_observation_numerical()
 
  def _get_observation_numerical(self):
    # agent_vector is current observation.  
    obs_dict = {}

    # NBR_FEATURE_PER_TECH = 
    self.config['NBR_FEATURE_PER_TECH'] = 19
    #NBR_FEATURE_WORKER_ONLY = self.config['NBR_FEATURE_WORKER_ONLY']
    #NBR_FEATURE_CUR_JOB_n_OVERALL  = self.config['NBR_FEATURE_CUR_JOB_n_OVERALL'] 
    #NBR_WORK_TIME_SLOT_PER_DAY = self.config['NBR_FEATURE_CUR_JOB_n_OVERALL'] # 1

    self.current_observed_worker_list  = self._get_sorted_worker_code_list(self.current_job_i)
    
    curr_work_time_slots = [] # (map(lambda x: [x[0], x[1], 0, 0, 0, 0 ], self.workers[worker_index]['working_time']))

    agent_vector = np.zeros(self.config['NBR_FEATURE_PER_TECH'] *  self.config['nbr_of_days_planning_window'] * len(self.current_observed_worker_list) )

    o_start_longitude = np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'] )
    o_start_latitude = np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window']) 
    # o_max_available_working_slot_duration = np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window']) 
        
    o_end_longitude                          =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                                           
    o_end_latitude                           =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                
    o_average_longitude                      =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                      
    o_average_latitude                       =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                     
    #                                         = 
    o_nbr_of_jobs                            =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])              
    o_total_travel_minutes                   =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                        
    o_first_job_start_minutes                =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                           
    o_total_occupied_duration                =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                           
    o_total_unoccupied_duration              =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                             
    #                                         = 
    o_max_available_working_slot_duration    =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                                      
    o_max_available_working_slot_start       =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                                   
    o_max_available_working_slot_end         =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                                 
    o_max_unoccupied_rest_slot_duration      =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                                    
    o_total_available_working_slot_duration  =np.zeros(self.config['nbr_of_observed_workers']* self.config['nbr_of_days_planning_window'])                                       

    # + NBR_FEATURE_WORKER_ONLY + NBR_FEATURE_CUR_JOB_n_OVERALL ) # .tolist()

    # Firstly the assigned job stats
    for current_job_worker_index in range(len(self.current_observed_worker_list)): 
      # setup home (start,end) GPS
      # x,y = get_normalized_location(self.workers_dict[worker_index]['home_gps'])
      worker = self.workers_dict[self.current_observed_worker_list[current_job_worker_index]]
      worker_index = worker['worker_index']

      # assigned time slots for each worker in agent_vector  
      # curr_total_free_duration = self.workers_dict[worker_index]['total_free_duration'] 


      for day_i in range(self.config['nbr_of_days_planning_window'] ):

        work_time_span = worker['working_time'][day_i]

        # Features for this worker_day_assignment
        f_start_longlat = [worker['geo_longitude'], worker['geo_latitude']]
        f_end_longlat = [worker['geo_longitude'], worker['geo_latitude']]
        f_average_longlat = [worker['geo_longitude'], worker['geo_latitude']]

        f_nbr_of_jobs = 0
        f_total_travel_minutes = 0
        # I use 0--24 hours for each day. Do not accumulate.
        f_first_job_start_minutes = self.config['minutes_per_day'] 
        f_last_job_end_minutes = self.config['minutes_per_day'] # (day_i + 1) *  

        f_total_occupied_duration = 0 # Sum up from assigned_jobs
        f_total_unoccupied_duration = self.config['minutes_per_day']  * 1 # work_time_span[1] - work_time_span[0]

        # f_max_available_working_slot_duration = work_time_span[1] - work_time_span[0]
        f_max_available_working_slot_duration = 0
        f_max_available_working_slot_start = 0
        f_max_available_working_slot_end = 0

        f_min_available_working_slot_duration = 0 # config.KANDBOX_MAXINT
        f_min_available_working_slot_start = 0
        f_min_available_working_slot_end = 0


        f_max_unoccupied_rest_slot_duration = 0
        f_total_available_working_slot_duration = 0 # Sum up from free_slots



        last_job_end = day_i * self.config['minutes_per_day']

        for assigned_job_index_info in worker['assigned_jobs']: #TODO, performance, already sorted, not necessary to loop through all.
          the_job = self.jobs[assigned_job_index_info['job_index']]
          if  (the_job['assigned_start_minutes'] > day_i * self.config['minutes_per_day'] ) & \
              (the_job['assigned_start_minutes'] < (day_i + 1) * self.config['minutes_per_day'] ):
            # This job is assigned to this day.

            if f_first_job_start_minutes < the_job['assigned_start_minutes']:
              f_first_job_start_minutes =  the_job['assigned_start_minutes']  
              f_start_longlat = [the_job['geo_longitude'], the_job['geo_latitude']]  # 
            if the_job['assigned_start_minutes'] + the_job['scheduled_duration_minutes']  < f_last_job_end_minutes:
              f_last_job_end_minutes =  the_job['assigned_start_minutes'] + the_job['scheduled_duration_minutes']  
              f_end_longlat = [the_job['geo_longitude'], the_job['geo_latitude']]  # 
            
            f_average_longlat = [
              ((f_average_longlat[0] * f_nbr_of_jobs ) +  the_job['geo_longitude'] ) / (f_nbr_of_jobs+1),
              ((f_average_longlat[1] * f_nbr_of_jobs ) +  the_job['geo_latitude'] ) / (f_nbr_of_jobs+1),
            ]

            f_nbr_of_jobs +=1
            f_total_travel_minutes += assigned_job_index_info['travel_minutes']

            f_total_occupied_duration += the_job['scheduled_duration_minutes']
            f_total_unoccupied_duration -= the_job['scheduled_duration_minutes'] + assigned_job_index_info['travel_minutes']

            curr_rest_duration_before_job = the_job['assigned_start_minutes'] - assigned_job_index_info['travel_minutes'] - last_job_end
            if curr_rest_duration_before_job > f_max_unoccupied_rest_slot_duration: 
              f_max_unoccupied_rest_slot_duration = curr_rest_duration_before_job

        for a_free_slot in worker['free_time_slots'][day_i]: #TODO, performance, already sorted, not necessary to loop through all.
          f_total_available_working_slot_duration += a_free_slot[1] - a_free_slot[0]
          if a_free_slot[1] - a_free_slot[0] >  f_max_available_working_slot_duration:
            f_max_available_working_slot_duration =   a_free_slot[1] - a_free_slot[0]
            f_max_available_working_slot_start = a_free_slot[0]
            f_max_available_working_slot_end = a_free_slot[1] 

          if f_min_available_working_slot_duration == 0:
            f_min_available_working_slot_duration =   a_free_slot[1] - a_free_slot[0]
            f_min_available_working_slot_start = a_free_slot[0]
            f_min_available_working_slot_end = a_free_slot[1] 
          elif a_free_slot[1] - a_free_slot[0] <  f_min_available_working_slot_duration:
            f_min_available_working_slot_duration =   a_free_slot[1] - a_free_slot[0]
            f_min_available_working_slot_start = a_free_slot[0]
            f_min_available_working_slot_end = a_free_slot[1] 
        
        curr_worker_day_i = current_job_worker_index * self.config['nbr_of_days_planning_window'] + day_i 


        o_start_longitude [curr_worker_day_i]= f_start_longlat[0] # current_job_worker_index, day_i 
        o_start_latitude [curr_worker_day_i]=  f_start_longlat[1] 

        o_end_longitude                          [curr_worker_day_i]= f_end_longlat[0]                                                             
        o_end_latitude                           [curr_worker_day_i]= f_end_longlat[1]                                              
        o_average_longitude                      [curr_worker_day_i]= f_average_longlat[0]                                     
        o_average_latitude                       [curr_worker_day_i]= f_average_longlat[1]                           
        #                                                          
        o_nbr_of_jobs                            [curr_worker_day_i]= f_nbr_of_jobs                                                 
        o_total_travel_minutes                   [curr_worker_day_i]= f_total_travel_minutes                                                  
        o_first_job_start_minutes                [curr_worker_day_i]= f_first_job_start_minutes                                                  
        o_total_occupied_duration                [curr_worker_day_i]= f_total_occupied_duration                                                  
        o_total_unoccupied_duration              [curr_worker_day_i]= f_total_unoccupied_duration                                                  
        #                                             
        o_max_available_working_slot_duration    [curr_worker_day_i]= f_max_available_working_slot_duration                           
        o_max_available_working_slot_start       [curr_worker_day_i]= f_max_available_working_slot_start                                          
        o_max_available_working_slot_end         [curr_worker_day_i]= f_max_available_working_slot_end                                        
        o_max_unoccupied_rest_slot_duration      [curr_worker_day_i]= f_max_unoccupied_rest_slot_duration                                    
        o_total_available_working_slot_duration  [curr_worker_day_i]= f_total_available_working_slot_duration                                        



        agent_vector[ current_job_worker_index * self.config['NBR_FEATURE_PER_TECH'] * self.config['nbr_of_days_planning_window'] 
                        + day_i * self.config['NBR_FEATURE_PER_TECH'] :
                      current_job_worker_index * self.config['NBR_FEATURE_PER_TECH'] * self.config['nbr_of_days_planning_window']
                        + (day_i+1) * self.config['NBR_FEATURE_PER_TECH'] 
                  ] =  [ 
          f_start_longlat[0], f_start_longlat[1], f_end_longlat[0], f_end_longlat[1], f_average_longlat[0], 
          f_average_longlat[1],  f_nbr_of_jobs, f_total_travel_minutes, f_first_job_start_minutes, 
          f_total_occupied_duration, f_total_unoccupied_duration, f_max_available_working_slot_duration, f_max_available_working_slot_start, f_max_available_working_slot_end,
          f_min_available_working_slot_duration, f_min_available_working_slot_start, f_min_available_working_slot_end, f_max_unoccupied_rest_slot_duration, f_total_available_working_slot_duration
        ]
    
      # worker_feature_begin_offset = NBR_FEATURE_PER_TECH*worker_index + NBR_DAYS*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_WORK_TIME_SLOT_PER_DAY + NBR_DAYS 
      # agent_vector[ worker_feature_begin_offset + 2] = curr_total_free_duration
      # agent_vector[worker_feature_begin_offset + 3] = curr_max_free_slot_duration
    
    '''
    # Secondary all worker statistics
    for current_job_worker_index in self.current_observed_worker_list: 
      # setup home (start,end) GPS
      # x,y = get_normalized_location(self.workers_dict[worker_index]['home_gps'])
      worker = self.workers_dict[self.current_observed_worker_list[current_job_worker_index]]

      worker_index = worker['worker_index']
      agent_vector[NBR_FEATURE_PER_TECH*worker_index   + 0: \
                   NBR_FEATURE_PER_TECH*worker_index + NBR_WORK_TIME_SLOT_PER_DAY] \
          =  [ 0, 0 , worker['geo_longitude'] , worker['geo_latitude'] ]
      agent_vector[NBR_FEATURE_PER_TECH*(worker_index+1) - 4: \
                   NBR_FEATURE_PER_TECH*(worker_index+1) - 0 ] \
          =  [ 0, 0 , x,y]

    for worker_index in range(len(self.workers_dict)): 
      # Historical customer visit GPS Gaussian , Sigma, Gamma, 2 DIMENSIONAL 
      # and others 4
      agent_vector[len(self.workers_dict)*NBR_FEATURE_PER_TECH + worker_index] \
        = self.workers_dict[worker_index]['level'] / 5
    '''
    #Thirdly  the job statistics


    # Now append the visit information AS THE 2nd half.
    # job_feature_start_index = len(self.workers_dict)*NBR_FEATURE_PER_TECH + NBR_FEATURE_WORKER_ONLY
    

    if self.current_job_i >= len(self.jobs ) :
      new_job_i = len(self.jobs )  - 1
    else:
      new_job_i = self.current_job_i

    # obs_dict['worker_job_assignment_matrix'] = agent_vector
    obs_dict['assignment.start_longitude'] =  o_start_longitude
    obs_dict['assignment.start_latitude'] =  o_start_latitude
    obs_dict['assignment.max_available_working_slot_duration'] =  o_max_available_working_slot_duration

    # obs_dict['job.features'] = np.zeroes(3)
    # obs_dict['job.mandatory_minutes_minmax_flag'] = np.zeros(1)
    obs_dict['job.mandatory_minutes_minmax_flag'] =  self.jobs[new_job_i]['mandatory_minutes_minmax_flag']  
    obs_dict['job.requested_start_minutes']  = np.zeros(1)
    obs_dict['job.requested_start_minutes'][0] =  self.jobs[new_job_i]['requested_start_minutes']  
    obs_dict['job.requested_duration_minutes'] = np.zeros(1)
    obs_dict['job.requested_duration_minutes'][0] =  self.jobs[new_job_i]['requested_duration_minutes']  

    obs_tuple = (
      o_start_longitude,
      o_start_latitude,
      o_end_longitude,
      o_end_latitude,
      o_average_longitude,
      o_average_latitude,
      #
      o_nbr_of_jobs,
      o_total_travel_minutes, 
      o_first_job_start_minutes, 
      o_total_occupied_duration, 
      o_total_unoccupied_duration, 
      #
      o_max_available_working_slot_duration, 
      o_max_available_working_slot_start, 
      o_max_available_working_slot_end, 
      o_max_unoccupied_rest_slot_duration, 
      o_total_available_working_slot_duration,
      #
      self.jobs[new_job_i]['mandatory_minutes_minmax_flag'],
      obs_dict['job.requested_start_minutes'],
      obs_dict['job.requested_duration_minutes'] 
    )

    '''
f_start_longlat[0], f_start_longlat[1], f_end_longlat[0], f_end_longlat[1], f_average_longlat[0], 
          f_average_longlat[1],  f_nbr_of_jobs, f_total_travel_minutes, f_first_job_start_minutes, 
          f_total_occupied_duration, f_total_unoccupied_duration, f_max_available_working_slot_duration, f_max_available_working_slot_start, f_max_available_working_slot_end,
          f_min_available_working_slot_duration, f_min_available_working_slot_start, f_min_available_working_slot_end, f_max_unoccupied_rest_slot_duration, f_total_available_working_slot_duration
       
    '''


    '''
    visit_vector = list(range(5))
    # Location of the new job is added to the end of agent_vector.   
    visit_vector[0] = self.jobs[self.current_job_i]['requested_duration_minutes']  
    
    visit_vector[1] = self.jobs[self.current_job_i]['mandatory_minutes_minmax_flag'] 
    # visit_vector[2] = self.jobs[self.current_job_i]['preferred_minutes_minmax_flag'] 
    visit_vector[3] = self.jobs[self.current_job_i]['requested_start_minutes']  
    visit_vector[4] = self.jobs[self.current_job_i]['requested_start_minutes']  
    '''

      # obs_dict['job.requested_start_max_minutes'] =  self.jobs[self.current_job_i]['requested_start_minutes']  

      #agent_vector[job_feature_start_index +3] = self.jobs[self.current_job_i]['expected_job_day'] / 30  
      #agent_vector[job_feature_start_index +4] = self.jobs[self.current_job_i]['tolerated_day_min']  /10
      #agent_vector[job_feature_start_index +5] = self.jobs[self.current_job_i]['tolerated_day_max']  /10

      #visit_vector[ 5] = 0 # self.jobs[self.current_job_i]['customer_level']  
      #visit_vector[ 6] = 0 # self.jobs[self.current_job_i]['product_level']  

    # obs_dict['current_job_vector'] = visit_vector

    # Finished looping through all workers
    return obs_tuple# OrderedDict(obs_dict)

  def _save_to_db(self, game_sequence = 1):

    if self.kplanner_db is None:
      print( "not loaded from DB!")
      return 

    result_json = self.get_solution_json()


    solution_df_all = pd.DataFrame(result_json)
    solution_df = solution_df_all[['job_code', 'job_type', 'location_code', 'scheduled_share_status',
      'geo_longitude', 'geo_latitude',  'planning_status', 'scheduled_worker_code', 'requested_start_day',
      'scheduled_start_minutes', 'scheduled_start_day','scheduled_duration_minutes',
      'scheduled_travel_prev_code', 'scheduled_travel_minutes_before']].copy()

    curr_game_code = '{}-{}-{}'.format(self.config['planner_code'], self.config['data_start_day'], game_sequence ) 
    #solution_df['game_code'] = curr_game_code
    game_info = {
          'planner_code': self.config['planner_code'],
          'game_code': curr_game_code,
      }


    self.kplanner_db.save_schedued_jobs(solution_df, game_info)
    self.kplanner_db.save_game_info(game_code=curr_game_code
              , planner_code=self.config['planner_code']
              , data_start_day = self.config['data_start_day']
              , data_end_day = date_util.add_days_2_day_string(k_day=self.config['data_start_day'], days = self.config['nbr_of_days_planning_window'])
    )
              


  def code_dict_into_action(self, a_dict):
    n = np.zeros(len(self.workers) + 4 )
    worker_index = self.workers_dict[a_dict['scheduled_worker_code']]['worker_index']
    n[worker_index ] = 1
    n[-4] = a_dict['scheduled_duration_minutes']  #  * self.env.config['minutes_per_day']  + 
    n[-3] = a_dict['scheduled_start_day']  #  * self.env.config['minutes_per_day']  + 
    n[-2] = a_dict['scheduled_start_minutes'] # / 1600 # 288
    n[-1] = len(a_dict['scheduled_related_worker_code']) + 1 # / 200 # 60 - shared count
 
    return n

  def decode_action_into_dict(self, action):
    '''
    action[0].shape=self.config['nbr_of_observed_workers']
    for iii in range(1,5):
      action[iii].shape=1
    new_act = list(action[0]) + list(action[1])  + list(action[2])  + list(action[3])  + list(action[4]) 
    ''' 
    new_act = action.copy()
    max_i = np.argmax(new_act[0:len(self.workers)])
    worker_code = self.workers[max_i]['worker_code']
    action_day = int(new_act[-3])
    job_start_time = action_day * self.config['minutes_per_day'] + new_act[-2] # days * 1440 + minutes
    shared_count = int(new_act[-1])
    scheduled_related_worker_code=[]
    for i in range(1,shared_count):
      new_act[max_i] = 0
      max_i = np.argmax(new_act[0:len(self.workers)])
      scheduled_related_worker_code.append(self.workers[max_i]['worker_code'])


    a_dict = {
      'scheduled_worker_code': worker_code,
      'scheduled_related_worker_code':scheduled_related_worker_code,
      'scheduled_start_day': action_day,
      'scheduled_start_minutes': new_act[-2],
      'assigned_start_day_n_minutes': job_start_time,
      'scheduled_duration_minutes': new_act[-4],
    }
    

    return a_dict



  def gen_action_from_one_job(self, one_job):
    return self.gen_action_from_actual_job(one_job)

  def gen_action_from_actual_job(self, one_job):
    if one_job is None:
      one_job = self.jobs[self.current_job_i]
    
    n = np.zeros(len(self.workers) + 4 )
    n[one_job['actual_worker_index']  ] = 1
    related_worker_count = 0
    if   one_job['scheduled_share_status'] == 'P':
      related_worker_count = len(one_job['scheduled_related_worker_code'])
      for worker_code in one_job['scheduled_related_worker_code'] :
        n[  self.workers_dict[worker_code]['worker_index']  ] = 1
    n[-4] = one_job['requested_duration_minutes']  #  * self.env.config['minutes_per_day']  + 
    n[-3] = one_job['actual_job_day']  #  * self.env.config['minutes_per_day']  + 
    n[-2] = one_job['actual_start_minutes'] # / 1600 # 288
    n[-1] = related_worker_count + 1 # 1 # / 200 # 60 - shared count
    return n


if __name__ == '__main__':
  
  env = KPlannerHistoryAffinityTopNGMMEnv(from_db=True, env_config={'data_start_day':'20200421'})
  o = env._get_observation_numerical()
  # print(o)
  if  env.observation_space.contains(o):
    print("Env is Good.".format(1, 1))


  from kandbox_planner.planner_engine.rl.agent.kprl_agent_heuristic_single_job_history import HeuristicAgentSingleJobByHistory
  # env = KPlannerHistoryAffinityTopNGMMEnv()
  from kandbox_planner.planner_engine.rl.agent.kprl_agent_history_affinity_random import KPRLAgentRandomGuess4HistoryAffinity
  from kandbox_planner.planner_engine.rl.agent.kprl_agent_rllib_ppo import KPRLAgentAgentRLLibPPO

  # model_agent = HeuristicAgentSingleJobByHistory(env = env)
  model_agent = KPRLAgentRandomGuess4HistoryAffinity(env = env)

  for _test_i in range(1):
    env.reset(shuffle_jobs=False)
    observation = env._get_observation()
    # print("Prediction Game: {}, started ...".format(game_index))
    for step_index in range(len(env.jobs)):
      #if step_index == 3:
      # print("debug step_index: {}".format(step_index))
      if '10019770|65|PESTS|19/08/19' in str(env.jobs[env.current_job_i]['job_id']):
        print('pause')

      '''
      if 'planning_status' in env.jobs[env.current_job_i].keys() and env.jobs[env.current_job_i]['planning_status'] == 'P':
        action = env.gen_action_from_planned_job(one_job = env.jobs[env.current_job_i] ) 
        print("job ({}) is recovered from P status".format(env.jobs[env.current_job_i]['job_code']))
      else:
        action = model_agent.predict_action(observation= observation ) # [0]
      '''
      action = env.action_space.sample()

      if not env.action_space.contains(action):
        print("Action is in bad format. Space: {}, action: {}".format(env.action_space, action))

      if  (action is None) or (len(action) <1):
          print("Failed to get prediction for job ({}) ".format(env.jobs[env.current_job_i]['job_id']))
          break
      
      observation, reward, done, info = env.step(action)  
      if  not env.observation_space.contains(observation):
        print("Observation is Bad.", observation)

      # pprint(env.render_action(action))
      # 
      if done:
        print('all done, reward:', reward)
        break
     
    env.kplanner_db.purge_planner_job_status(planner_code=env.config['planner_code'],start_date = '20191101', end_date = '20191201' )
    env._save_to_db(game_sequence= 201 + _test_i)


  model_agent = KPRLAgentAgentRLLibPPO(env=env, env_class=KPlannerHistoryAffinityTopNGMMEnv)

  _path = model_agent.train_model(model_path='/Users/qiyang/ray_results/PPO_KPlannerHistoryAffinityTopNGMMEnv_2020-03-11-agent')
  print(_path)
  # _path = '/Users/qiyang/ray_results/PPO_KPlannerHistoryAffinityTopNGMMEnv_2020-03-11-agent/checkpoint_20/checkpoint-20'
  model_agent.load_model(model_path=_path)

  game_rewards = []
  for _ in range(1):
      obs = env.reset()
      done = False

      cumulative_reward = 0
      while not done:
          action = model_agent.predict_action(obs)
          a_dict=env.decode_action_into_dict(action)
          obs, reward, done, results = env.step(action)
          cumulative_reward += reward
      print(cumulative_reward)
      game_rewards += [cumulative_reward]
  print('game_rewards:', game_rewards)
  env._save_to_db(game_sequence= 404)

  exit(0)


  '''
  import gym
  from gym import spaces
  import numpy as np
  import ray
  from ray.rllib.agents.ppo import PPOTrainer, DEFAULT_CONFIG

  ray.init(ignore_reinit_error=True, log_to_driver=False)

  trainer_config = DEFAULT_CONFIG.copy()
  trainer_config['num_workers'] = 0
  trainer_config["train_batch_size"] = 40
  trainer_config["sgd_minibatch_size"] = 10
  trainer_config["num_sgd_iter"] = 10
  trainer = PPOTrainer(trainer_config, KPlannerHistoryAffinityTopNGMMEnv)

  if False:
    for i in range(2):
        print("Training iteration {} ...".format(i))
        trainer.train()

    path = trainer.save()
    print("model checkpoint saved at:", path)
  else:
    path = '/Users/qiyang/ray_results/PPO_KPlannerHistoryAffinityTopNGMMEnv_2020-03-11_09-28-3152d4vg7d/checkpoint_2/checkpoint-2'
  
  trainer.restore(path)
  '''

  
