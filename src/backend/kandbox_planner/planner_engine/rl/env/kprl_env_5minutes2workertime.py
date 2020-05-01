'''
This is right after migrating last V2 env. refer to xls design file. -- Entrada_v2
/Users/qiyang/Documents/qduan/git/work_git/field_service_robot/doc/dispatch_ai_model_design.xlsx


step 1: move rules out of env definition.
step 2: Then I will change network layout to multiple input (cnn + dense)
https://www.pyimagesearch.com/2019/02/04/keras-multiple-inputs-and-mixed-data/
/Users/qiyang/Downloads/Houses-dataset

https://medium.com/datadriveninvestor/dual-input-cnn-with-keras-1e6d458cd979

'''

# This version works on top of json input and produce json out
# Observation: each worker has multiple working_time=days, then divided by slots, each slot with start and end time, 


import gym
from gym import error, spaces, utils
from gym.utils import seeding

from six import StringIO, b
import sys
import numpy as np 
import random
import math 
from operator import truediv # add

import kandbox_planner.util.planner_date_util  as date_util

#  

# each technicians has NBR_SLOT_PER_TECH time slots avaialble for dispatching customer visits
# each time slot is (start_time, end_time, Last task location X, Y)  -> (int, int, Float, Float) 
# X, Y Current Location of each agent accord to his last task

MAX_NBR_WORKERS = 6 
NBR_FEATURE_WORKERS = MAX_NBR_WORKERS * 1 # features for each worker, like history of serving gps, prferred time, etc.
NBR_FEATURE_CUR_JOB_n_OVERALL = 32 # features about current job.


NBR_DAYS = 1 # 10
WORK_TIME_UNIT_MINUTES = 5 # Minimal unit of time to schedule is 5 minutes interval.
NORMALIZE_DENOMINATOR_DURATION  = 36 # Max length of job duration are 3 hours = 180 = 36*5 minutes

NBR_FEATURE_PER_WORK_TIME_UNIT = 4  # (available_flag, occupied_flag, gps_x, gps_y)
NBR_WORK_TIME_UNIT_PER_DAY = math.ceil(24*60/WORK_TIME_UNIT_MINUTES) # For 5 minutes, everyday there are 288 time units
TIME_SLOT_LENGTH_5MINUTES = 5


NBR_WORK_TIME_UNIT_PER_TECH = NBR_DAYS * NBR_WORK_TIME_UNIT_PER_DAY

NBR_FEATURE_PER_TECH = NBR_FEATURE_PER_WORK_TIME_UNIT * ( NBR_WORK_TIME_UNIT_PER_TECH +  2 ) # Starting and end location.



# MAX_ASSIGNED_TIME_SLOT_PER_DAY =  5
# MAX_WORKING_TIME_DURATION = 60*6
# NBR_FEATURE_PER_TECH = all dispatched time slots (start time, end time, gps x y) +
# all working_time slot statistics  (only free duration)
# worker statistics (home gps)



# https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
  """
  Calculate the great circle distance between two points 
  on the earth (specified in decimal degrees)
  """
  # convert decimal degrees to radians 
  lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

  # haversine formula 
  dlon = lon2 - lon1 
  dlat = lat2 - lat1 
  a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
  c = 2 * asin(sqrt(a)) 
  r = 6371 # Radius of earth in kilometers. Use 3956 for miles
  return c * r


# haversine( 0, 51.5, -77.1,  38.8)  = 5918.185064088763  // From London to Arlington 

def get_travel_time_2locations(loc_1, loc_2):
  # distance = haversine(loc_1[0] , loc_1[1] , loc_2[0], loc_2[1]) 
  y_1,x_1= loc_1[0] ,loc_1[1]
  y_2,x_2= loc_2[0], loc_2[1] 

  delay_time = ( abs(int(x_1) - int(x_2)) / 20 ) + \
                ( abs(int(y_1) - int(y_2)) / 20 )
  # print(delay_time)
  return int(delay_time)

X_MIN = 0
X_MAX = 100 
Y_MIN = 0
Y_MAX = 100


def get_normalized_location(loc): 
  # distance = haversine(loc_1[0] , loc_1[1] , loc_2[0], loc_2[1]) 
  x = ( loc[0] - X_MIN ) / (X_MAX - X_MIN)
  y = ( loc[1] - Y_MIN ) / (Y_MAX - Y_MIN)
 
  return x,y



# For each task [ [start, end], gps[x,y], duration_left]
# for each agent [gps-x,y   task(start_time_with_travel   end_time)]

class KPRL5Minutes2WorkerTime(gym.Env):
  """
    Has the following members 
  """
  metadata = {'render.modes': ['human']} 
  config={}
  def __init__(self, workers=None, jobs=None, env_config = None, run_mode = 'train', allow_overtime = False, max_nbr_of_worker = None):     
    # , max_nbr_of_working_time_per_worker = 10
    # each worker [{ id , active, level,  gps: [x, y], total_free_duration, free_time_slots: [start, end], }]
    self.workers = workers 
    if env_config:
      for x in env_config.keys():
        self.config[x]  = env_config[x]

    if max_nbr_of_worker is None:
      self.MAX_NBR_OF_WORKERS = len(self.workers)
    else:
      #NBR_AGENT = 6
      #self.max_nbr_of_worker = NBR_AGENT

      self.MAX_NBR_OF_WORKERS = max_nbr_of_worker

    #if max_nbr_of_working_time_per_worker is None:
    #  self.max_nbr_of_working_time_per_worker = len(self.jobs)
    #else:
    
    # self.max_nbr_of_working_time_per_worker = NBR_WORK_TIME_SLOT_PER_TECH
    self.allow_overtime = allow_overtime
    self.run_mode = run_mode #  'train' for training, 'predict' for prediction new dataset.
    # each job [{ duration, gps: [x, y], fixed_schudule: [indicator, fixed_start, fixed_start], level }]
    self.jobs = jobs 
    self.job_count = len(self.jobs ) 
    
    self.current_job_i = 0
    self.total_travel_time = 0
    self.total_assigned_job_duration = 0
    self.worker_assigned_jobs = [] # List of jobs assigned to each worker. ID is worker_ID=[] Each one is [* 3 ] {job_id, start, end, gps_lat, gps_lon}

    for job_index in range(len(self.jobs)):
      self.jobs[job_index]['requested_start_minutes'] = int ( self.jobs[job_index]['requested_start_minutes'] / TIME_SLOT_LENGTH_5MINUTES )
      self.jobs[job_index]['requested_duration_minutes'] = int (self.jobs[job_index]['requested_duration_minutes'] / TIME_SLOT_LENGTH_5MINUTES )
      self.jobs[job_index]['actual_start_minutes'] /= TIME_SLOT_LENGTH_5MINUTES

      if self.jobs[job_index]['requested_start_max_minutes'] is None:
        self.jobs[job_index]['requested_start_max_minutes'] = 0
        self.jobs[job_index]['requested_start_min_minutes'] = 0
        continue
      self.jobs[job_index]['requested_start_max_minutes'] /= TIME_SLOT_LENGTH_5MINUTES
      self.jobs[job_index]['requested_start_min_minutes'] /= TIME_SLOT_LENGTH_5MINUTES

    for worker_index in range(len(self.workers)):
      for time_slot_i in range(len(self.workers[worker_index]['working_time'])): 
        self.workers[worker_index]['working_time'][time_slot_i] = [
          int(self.workers[worker_index]['working_time'][time_slot_i][0] / TIME_SLOT_LENGTH_5MINUTES),
          int(self.workers[worker_index]['working_time'][time_slot_i][1] / TIME_SLOT_LENGTH_5MINUTES)
        ] 


    self.reset()



  def step(self, action ):
    # action [1, 0, 0 ]. One hot coding, 1 means this worker take the job.
    done = False
    info='ok'
    reward = self._get_reward()
    # if sum(action) == 1:
      # Single worker take the job


    add_result = self._add_current_job_to_worker(action) # worker_index = action_worker, working_time_index = action_working_time_index) 
    # print("Adding job {}--{} to Worker {}-{} , result: {}...".format(self.current_job_i - 1, self.jobs[self.current_job_i - 1]['job_id'],action_worker, action_working_time_index,add_result ))
    if add_result == False:
        #done = True
        info='error'
        reward = self._get_reward() # 0
    # break
    else:
      info =  'ok'
      if self.current_job_i == self.job_count:
        done = True
        reward = self._get_reward() # 1
 
    obs = self._get_observation()
    return (obs, reward, done, info)

  def reset(self, shuffle_jobs=False):
    self.current_job_i = 0
    # self.worker_ids = {}
    self.total_travel_time = 0
    self.total_assigned_job_duration = 0
    self.worker_assigned_jobs = list(map(lambda x:[], self.workers)) # List of jobs assigned to each worker. Each one is [* 3 ]
    self.WORKER_COUNT = len(self.workers)
    
    if shuffle_jobs :
      random.shuffle(self.jobs)

    self.worker_available_time_bitmap = np.zeros([len(self.workers), NBR_WORK_TIME_UNIT_PER_TECH]) # List of jobs assigned to each worker. ID is worker_ID=[] Each one is [* 3 ] {job_id, start, end, gps_lat, gps_lon}
    self.worker_occupied_time_bitmap = np.zeros([len(self.workers), NBR_WORK_TIME_UNIT_PER_TECH]) # List of jobs assigned to each worker. ID is worker_ID=[] Each one is [* 3 ] {job_id, start, end, gps_lat, gps_lon}
    

    for worker_index in range(len(self.workers)):
      # self.worker_ids[self.workers[worker_index]['id']] = worker_index  # no used...
      self.worker_assigned_jobs[worker_index] = []
      
      for time_slot in self.workers[worker_index]['working_time']: 
        for ti in range(time_slot[0], time_slot[1]):
          self.worker_available_time_bitmap[worker_index, ti] = 1
          

    return self._get_observation()

  def replay_env(self):
    return self.reset()

  def render(self, mode='human'):
    outfile = StringIO() if mode == 'ansi' else sys.stdout
    if self.current_job_i < self.job_count:
      outfile.write(' '.join([ 'total: {}, '.format(len(self.jobs)),    'Next job:','{ curr=', str(self.current_job_i), ', dur=' , str( self.jobs[self.current_job_i]['requested_duration_minutes']  )  \
         ,', gps=' , str( self.jobs[self.current_job_i]['job_gps']  ) , '}'  \
        , 'travel: ', str(self.total_travel_time), 'total_dur: ', str(self.total_assigned_job_duration),'\n' ]))
    else:
      outfile.write(' '.join([  'No next jobs ...'  \
        , 'travel: ', str(self.total_travel_time), 'total_dur: ', str(self.total_assigned_job_duration), '\n' ]) )

    for worker_id in  range(len(self.worker_assigned_jobs)):
      job_dur = 0
      job_list = []
      # , GPS:({},{})
      for a_job in self.worker_assigned_jobs[worker_id] :  
        job_list.append( 'job:{}, ({} - {})'.format( a_job['job_index']  ,  \
                 a_job['start_time'], \
                 a_job['end_time'] ) )
        job_dur += a_job['end_time'] -  a_job['start_time'] 

      outfile.write(' '.join([     
        'Worker({:>1}): job_duration({:>2})'.format(worker_id, job_dur), '->'.join([str(x) for x in  job_list])
        ,'\n'] ))


  def _check_all_start_time_within_range(self, assigned_time_start, job_list_orig, new_job):  # _get_start_time_jobs
    start_time_minute = assigned_time_start
    job_list = job_list_orig.copy()
    job_list.append(new_job)

    start_time_list=[] 
    prev_job = -10000000
    for assigned_job_j in range (len(job_list)):
      # First find a possible time slot to insert into :
      job_index = job_list[assigned_job_j]
      if assigned_job_j == 0:
        travel_time = 0
        start_time_minute = assigned_time_start
        prev_job = job_index
        
      else:
        travel_time = get_travel_time_2locations(self.jobs[job_index]['job_gps'], self.jobs[prev_job]['job_gps'])
        start_time_minute = start_time_minute + self.jobs[prev_job]['requested_duration_minutes'] + travel_time  
        prev_job = job_index


      start_time_list.append( start_time_minute )
     
    for ji in range(len(start_time_list)):
      if not( self.jobs[job_list[ji]]['fixed_schudule']['fixed_minute_time_slot'][0]  < start_time_list[ji] \
              < self.jobs[job_list[ji]]['fixed_schudule']['fixed_minute_time_slot'][1]
            ) :
        return False

    return True


  def get_solution_json(self): 
    job_solution=[] 
    for  worker_index in range (len(self.workers)):
      for work_time_i in  range (len(self.worker_assigned_jobs[worker_index])): # nth assigned job time unit.  
        job_index = self.worker_assigned_jobs[worker_index][work_time_i] ['job_index']
        start_time_minute = self.worker_assigned_jobs[worker_index][work_time_i] ['start_time']
        one_job =  {
          'job_code': self.jobs[job_index]['job_code'],
          'job_type': self.jobs[job_index]['job_type'],
          'location_code': self.jobs[job_index]['location_code'],
          'geo_longitude': self.jobs[job_index]['geo_longitude'],
          'geo_latitude': self.jobs[job_index]['geo_latitude'],
          'requested_start_day': self.jobs[job_index]['requested_start_day'],
          'scheduled_duration_minutes': self.jobs[job_index]['requested_duration_minutes'],


          'scheduled_start_day':  date_util.add_days_2_day_string(k_day=self.config['data_start_day'], days= work_time_i), # ?
          # 'planned_day': (datetime.strptime('2019-07-01',"%Y-%m-%d") +datetime.timedelta(days=time_slot_i))
          'scheduled_start_minutes' : start_time_minute, 
          'scheduled_worker_code': self.workers[worker_index]['worker_code'], # EmployeeCode  
          'planning_status': 'I', 
          "scheduled_share_status":  'N'  ,
          'scheduled_travel_minutes_before': 0,  
          'scheduled_travel_prev_code': '__HOME',   
          }

        a = ['job_code', 'job_type', 'location_code',
          'geo_longitude', 'geo_latitude',  'planning_status', 'scheduled_worker_code', 'requested_start_day',
          'scheduled_start_minutes', 'scheduled_start_day','scheduled_duration_minutes',
          'scheduled_travel_prev_code', 'scheduled_travel_minutes_before','scheduled_share_status']
        '''
        one_job =  {
          'job_id': self.jobs[job_index]['job_id'],
          'work_time_i':work_time_i,
          # 'planned_day': (datetime.strptime('2019-07-01',"%Y-%m-%d") +datetime.timedelta(days=time_slot_i))
          'start_time_minute' : start_time_minute,
          'requested_duration_minutes': self.jobs[job_index]['requested_duration_minutes'],
          'VisitOwner_EmployeeCode': self.workers[worker_index]['worker_code'], # EmployeeCode
          'VisitOwner_worker_id': str(self.workers[worker_index]['worker_id']), # id
          'BranchServiceAreaCode': self.workers[worker_index]['worker_code'], # BranchServiceAreaCode
          'Visit_Status': 'I', 
              "scheduled_share_status":  'N'  ,
          # 'Contract': self.jobs[job_index]['job_id'].split('|')[0],
          #'Premise': self.jobs[job_index]['job_id'].split('|')[1], 
          #'history_job_worker_count':self.jobs[job_index]['history_job_worker_count'], 
          #s'history_max_count_worker_id': str(np.argmax(self.jobs[job_index]['history_job_worker_count'])),
          'requested_start_day_sequence': self.jobs[job_index]['requested_start_day_sequence'],  
          }
          '''
          #start_time_minute = start_time_minute + 
        prev_job = job_index
        job_solution.append(one_job)
    return job_solution


  def close(self):
    pass

  # ***************************************************************
  # # Internal functions
  # ***************************************************************
  def _get_travel_time_2jobs(self, job_index_1, job_index_2):
    distance = abs(self.jobs[job_index_1]['job_gps'][0] - self.jobs[job_index_2]['job_gps'][0]) + \
               abs(self.jobs[job_index_1]['job_gps'][1] - self.jobs[job_index_2]['job_gps'][1]) 
    return distance/2


  def _get_best_fit_time_slot(self, worker_index, working_time_index, job_index):
    # return the index of which timeslot has closest GPS to current job. 
    curr_free_slot_list = self.workers[worker_index][working_time_index]
    curr_job = self.jobs[job_index]

    def _calculate_travel_time(slot, job):  # x is the free time slot, 
        if slot[1]-slot[0] < job['requested_duration_minutes'] :
          return -1
        if job['fixed_schudule']['fs_indicator']:
          # if slot[0] -- todo
          return -1
        travel_time_if_add_ahead =  get_travel_time_2locations(self.jobs[job_index]['job_gps'], [   
          slot[2], slot[3]
         ])
        return travel_time_if_add_ahead

    fit_travel_time =  list(map(lambda x:_calculate_travel_time(x), curr_free_slot_list))
    min_travel_i = fit_travel_time.index(min(fit_travel_time))
    return min_travel_i
    # if min_travel_i == len(curr_free_slot_list): # append to the end



  def _add_current_job_to_worker(self, action) : # worker_index, working_time_index):
    # If there is not enough capacities without considering travel and time slot, reject it
    #if  self.jobs[self.current_job_i ]['requested_duration_minutes'] > self.workers[worker_index]['max_free_slot_duration']:
    #  return False 
    #action [time_slot_i] = 1
    #for i in range(len(action) - 3):
    #  if action[i] == 1:
    # max_i = np.argmax(action[0:self.WORKER_COUNT * NBR_WORK_TIME_UNIT_PER_TECH])
    worker_index = int(action[0] * 6) # int(max_i/NBR_WORK_TIME_UNIT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)
    # worker_code = self.workers[worker_index]['worker_code']
    job_start_time = int(action[1]  * 288)#  int(max_i % NBR_WORK_TIME_UNIT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)
    #action_job_start_time = action[-2] * 1600
    #action_job_duration = action[-1] * 200
    if (worker_index < 0) | (worker_index > len(self.workers) ) :
      return False


    if  (job_start_time < 0) |  (job_start_time >= NBR_WORK_TIME_UNIT_PER_TECH):
      return False 

    # If the start time does not fall in working hour, reject it.
    found_working_hour_index = -1
    self.jobs[self.current_job_i ]['requested_duration_minutes']

  
    
    if  np.sum(self.worker_occupied_time_bitmap[worker_index, \
               job_start_time: job_start_time + int(self.jobs[self.current_job_i ]['requested_duration_minutes'] ) ] ) \
             > 0:
      # no more room in this time slot
      print("at least one time unit is occupied.")
      return False

    # The following is to make sure that the worker/time selected should have total duration less than a threshold.
    if  np.min(self.worker_available_time_bitmap[worker_index, \
               job_start_time: job_start_time + self.jobs[self.current_job_i ]['requested_duration_minutes'] ] ) \
             < 1:
      # no more room in this time slot
      print("Time unit start:{}, duration:{} are not all available: {}".format(job_start_time, self.jobs[self.current_job_i ]['requested_duration_minutes'], self.worker_available_time_bitmap[worker_index, \
               job_start_time: job_start_time + self.jobs[self.current_job_i ]['requested_duration_minutes'] ]))
      return False
    
    travel_time = 0

    prev_job = None
    next_job = None
    new_job_loc_i=0
    for a_job in self.worker_assigned_jobs[worker_index]:
      if a_job['start_time'] < job_start_time:
        prev_job = a_job
      if a_job['start_time'] > job_start_time: # can not be equal
        next_job = a_job
        break
      new_job_loc_i+=1
    
    if prev_job :
      if  get_travel_time_2locations(self.jobs[self.current_job_i   ]['job_gps'], \
                                   self.jobs[prev_job['job_index']]['job_gps'] ) \
          > job_start_time - prev_job['end_time']:
        # no more room in this time slot
        print("Not enough travel time from prev_job: {}, rejected.".format(prev_job['job_index']))
        return False
    
    if next_job :
      if  get_travel_time_2locations(self.jobs[self.current_job_i   ]['job_gps'], \
                                   self.jobs[next_job['job_index']]['job_gps'] ) \
          >  next_job['start_time'] - job_start_time - self.jobs[self.current_job_i   ]['requested_duration_minutes']:
        # no more room in this time slot
        print("Not enough travel time from next_job: {}, rejected.".format(next_job['job_index']))
        return False

    self.worker_occupied_time_bitmap[worker_index, \
               job_start_time: job_start_time + self.jobs[self.current_job_i ]['requested_duration_minutes'] ]  = 1
    
    self.worker_assigned_jobs[worker_index].insert(new_job_loc_i, {'job_index': self.current_job_i,\
        'start_time': job_start_time, \
        'end_time': job_start_time +  self.jobs[self.current_job_i]['requested_duration_minutes'] })

    self.current_job_i+=1
    return True


  def _get_reward(self):
    reward = self.current_job_i / self.job_count # + ( 1 - self.total_travel_time / 60)

    return reward


  def _get_work_duration_slots(self, worker_index):      
      work_slot_durations = list(map(lambda x: 0 , self.workers[worker_index]['working_time']))

      for work_time_i in range(  len(self.worker_assigned_jobs[worker_index] ) ): 
        for time_slot_i in range(  len(self.worker_assigned_jobs[worker_index][work_time_i] ) ):
          # I assume that all assigned_time_slots are ordered ascendingly, same as working_time
          # loop through 
          work_slot_durations [work_time_i ] +=  self.worker_assigned_jobs[worker_index][work_time_i][time_slot_i] [1]  \
                                               - self.worker_assigned_jobs[worker_index][work_time_i][time_slot_i] [0] 
                        
      return work_slot_durations

  def _get_free_slot_durations(self, worker_index):      
      free_slot_durations = list(map(lambda x:  x[1] - x[0]  , self.workers[worker_index]['working_time']))

      for work_time_i in range(  len(self.worker_assigned_jobs[worker_index] ) ): 
        for time_slot_i in range(  len(self.worker_assigned_jobs[worker_index][work_time_i] ) ):
          # I assume that all assigned_time_slots are ordered ascendingly, same as working_time
          # loop through 
          free_slot_durations [work_time_i ] -=  self.worker_assigned_jobs[worker_index][work_time_i][time_slot_i] [1]  \
                                               - self.worker_assigned_jobs[worker_index][work_time_i][time_slot_i] [0] 
                        
      return free_slot_durations
  def _get_observation(self):
    # agent_vector is current observation.  
    agent_vector = np.zeros(NBR_FEATURE_PER_TECH * self.WORKER_COUNT + NBR_FEATURE_WORKERS + NBR_FEATURE_CUR_JOB_n_OVERALL ) # .tolist()


    for worker_index in range(len(self.workers)): 
      # setup home (start,end) GPS
      x,y = get_normalized_location(self.workers[worker_index]['home_gps'])
      agent_vector[NBR_FEATURE_PER_TECH*worker_index   + 0: \
                   NBR_FEATURE_PER_TECH*worker_index + NBR_FEATURE_PER_WORK_TIME_UNIT] \
          =  [ 0, 0 , x,y]
      agent_vector[NBR_FEATURE_PER_TECH*(worker_index+1) - 4: \
                   NBR_FEATURE_PER_TECH*(worker_index+1) - 0 ] \
          =  [ 0, 0 , x,y]

    
      
    
    
    # First all worker statistics
    for worker_index in range(len(self.workers)): 
      # assigned time slots for each worker in agent_vector  
      # curr_total_free_duration = self.workers[worker_index]['total_free_duration'] 

      for work_time_span in  self.workers[worker_index]['working_time']:
        for time_point in range(work_time_span[0], work_time_span[1]): 
          # Set work hour available
          agent_vector[NBR_FEATURE_PER_TECH*worker_index + ( (time_point+1) *NBR_FEATURE_PER_WORK_TIME_UNIT ) + 0 ] = 1
          # self.worker_available_time_bitmap[work_time_i] = 1

      # save (starttime, end time, gps x, gps y) for each assigned_time_slot
      for a_job in self.worker_assigned_jobs[worker_index] :  
        x,y = get_normalized_location(self.jobs [ a_job['job_index'] ]  ['job_gps'])
        
        # zip it
        for time_point in range(a_job['start_time'] , a_job['end_time']  ): # Skip first reseved for HOME,  a_job[1] , a_job[2] 
          agent_vector[NBR_FEATURE_PER_TECH*worker_index + ( (time_point+1) *NBR_FEATURE_PER_WORK_TIME_UNIT ) + 1: \
                      NBR_FEATURE_PER_TECH*worker_index  + ( (time_point+1) *NBR_FEATURE_PER_WORK_TIME_UNIT ) + NBR_FEATURE_PER_WORK_TIME_UNIT] \
            =  [ # self.worker_available_time_bitmap[worker_index][time_point] ,
                 1, # self.worker_occupied_time_bitmap[worker_index][time_point] ,
                 x,y ]
  
      # worker_feature_begin_offset = NBR_FEATURE_PER_TECH*worker_index + NBR_DAYS*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_TIME_UNIT + NBR_DAYS 
      # agent_vector[ worker_feature_begin_offset + 2] = curr_total_free_duration
      # agent_vector[worker_feature_begin_offset + 3] = curr_max_free_slot_duration
 
    for worker_index in range(len(self.workers)): 
      # Historical customer visit GPS Gaussian , Sigma, Gamma, 2 DIMENSIONAL 
      # and others 4
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH + worker_index] \
        = self.workers[worker_index]['level'] / 5

    # Now append the visit information AS THE 2nd half.
    job_feature_start_index = self.WORKER_COUNT*NBR_FEATURE_PER_TECH + NBR_FEATURE_WORKERS
    if self.current_job_i < self.job_count:
      # Location of the new job is added to the end of agent_vector.   
      agent_vector[ +0] = self.jobs[self.current_job_i]['requested_duration_minutes']   / NORMALIZE_DENOMINATOR_DURATION
      x,y = get_normalized_location(self.jobs[self.current_job_i]['job_gps'] )
      agent_vector[job_feature_start_index +1:job_feature_start_index + 3] = [x,y]  
      agent_vector[job_feature_start_index +3] = self.jobs[self.current_job_i]['requested_start_day_sequence'] / 30  
      agent_vector[job_feature_start_index +4] = self.jobs[self.current_job_i]['tolerated_day_min']  /10
      agent_vector[job_feature_start_index +5] = self.jobs[self.current_job_i]['tolerated_day_max']  /10


      # if self.jobs[self.current_job_i]['fixed_schudule']['fs_indicator'] == 'FT':
      if self.jobs[self.current_job_i ]['job_type']== 'FT':
          agent_vector[job_feature_start_index +6] = 1
          agent_vector[job_feature_start_index +7] = self.jobs[self.current_job_i]['requested_start_max_minutes']  /NBR_WORK_TIME_UNIT_PER_TECH
          agent_vector[job_feature_start_index +8] = self.jobs[self.current_job_i]['requested_start_min_minutes'] /NBR_WORK_TIME_UNIT_PER_TECH

      # if self.jobs[self.current_job_i]['fixed_schudule']['fs_indicator'] == 'FS':
      if self.jobs[self.current_job_i ]['job_type']== 'FS':
          agent_vector[job_feature_start_index +9] = 1
          agent_vector[job_feature_start_index +10] = self.jobs[self.current_job_i]['requested_start_max_minutes']  /NBR_WORK_TIME_UNIT_PER_TECH   # self.jobs[self.current_job_i]['fixed_schudule']['fs_start_time'] 

          agent_vector[job_feature_start_index +11] = self.jobs[self.current_job_i]['requested_start_min_minutes'] /NBR_WORK_TIME_UNIT_PER_TECH   # self.jobs[self.current_job_i]['fixed_schudule']['fixed_minute_time_slot'][1]

      agent_vector[job_feature_start_index +12] = 0 # self.jobs[self.current_job_i]['qpms_z_indicator']  
      agent_vector[job_feature_start_index +16] = 0 # self.jobs[self.current_job_i]['customer_level']  
      agent_vector[job_feature_start_index +17] = 0 # self.jobs[self.current_job_i]['product_level']  

      agent_vector[job_feature_start_index +20: \
                   job_feature_start_index +20 + len(self.jobs[self.current_job_i]['history_job_worker_count'])] \
            =  list( map(truediv,  self.jobs[self.current_job_i]['history_job_worker_count'] , \
                                   [x + 50 for x in np.zeros( len(self.jobs[self.current_job_i]['history_job_worker_count'])   ) ] \
                ))

    # Finished looping through all workers
    return agent_vector




  '''
  def gen_action_from_planned_job(self, one_job):
      n = np.zeros(2)
      n[0] = one_job['expected_job_worker'] / 6
      n[1] = ( one_job['requested_start_day_sequence'] * NBR_WORK_TIME_UNIT_PER_DAY + \
            int(one_job['expected_job_start_minute']  )   ) / 288

      return n
  '''
  def gen_action_from_one_job(self, one_job):
      n = np.zeros(2)
      n[0] = one_job['actual_worker_index'] / 6
      n[1] = ( one_job['actual_job_day'] * NBR_WORK_TIME_UNIT_PER_DAY + \
            int(one_job['actual_start_minutes']  )   ) / 288

      return n

  def render_action(self, action ):

    worker_index = int(action[0] * 6)  
    job_start_time = int(action[1]  * 288)#  int(max_i % NBR_WORK_TIME_UNIT_PER_TECH ) # 
    return  "worker: {}, start_time: ({})={}".format(worker_index, job_start_time, \
           date_util.minutes_to_time_string( job_start_time * WORK_TIME_UNIT_MINUTES )   ) 




if __name__ == '__main__':
    # main()
    pass