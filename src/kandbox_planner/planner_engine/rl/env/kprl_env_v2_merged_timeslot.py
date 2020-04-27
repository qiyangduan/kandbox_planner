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
from operator import truediv # add

import kandbox_planner.util.planner_date_util  as date_util



#  

# each technicians has NBR_SLOT_PER_TECH time slots avaialble for dispatching customer visits
# each time slot is (start_time, end_time, Last task location X, Y)  -> (int, int, Float, Float) 
# X, Y Current Location of each agent accord to his last task
NBR_WORK_TIME_SLOT_PER_TECH = 1 # 10
NBR_FEATURE_PER_WORK_SLOT = 4
MAX_ASSIGNED_TIME_SLOT_PER_DAY =  5

MAX_WORKING_TIME_DURATION = 60*6
# NBR_FEATURE_PER_TECH = all dispatched time slots (start time, end time, gps x y) +
# all working_time slot statistics  (only free duration)
# worker statistics (home gps)

NBR_FEATURE_PER_TECH = NBR_WORK_TIME_SLOT_PER_TECH*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT \
           + NBR_WORK_TIME_SLOT_PER_TECH \
           + 4
 
NBR_FEATURE_VIST_n_OVERALL = 32
'''

max_nbr_of_working_time_per_worker=3
max_nbr_of_worker = 4
max_total_duration = 0 # 25
'''




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

  delay_time = ( abs(int(x_1) - int(x_2)) / 12 ) + \
                ( abs(int(y_1) - int(y_2)) / 5 )
  # print(delay_time)
  return int(delay_time)



# For each task [ [start, end], gps[x,y], duration_left]
# for each agent [gps-x,y   task(start_time_with_travel   end_time)]

class DispatchV2Env(gym.Env):
  """
    Has the following members 
  """
  metadata = {'render.modes': ['human']} 

  config = {
    'run_mode' : 'train',
    'env_code' : 'merged_slot_v2',
    'game_code' : 'merged_slot_v2_',
    'allow_overtime' : False,
    'data_start_day':'20191108',
    'nbr_of_days':1,
    'minutes_per_day':60*24,
    'reversible' : True, 
  }

  def __init__(self, workers=None, jobs=None, env_config = None,  run_mode = 'train', allow_overtime = False, max_nbr_of_worker = None):     
    # , max_nbr_of_working_time_per_worker = 10
    # each worker [{ id , active, level,  gps: [x, y], total_free_duration, free_time_slots: [start, end], }]
    self.workers = workers 
    if env_config:
      for x in env_config.keys():
        self.config[x]  = env_config[x]

    if max_nbr_of_worker is None:
      self.max_nbr_of_worker = len(self.workers)
    else:
      #NBR_AGENT = 6
      #self.max_nbr_of_worker = NBR_AGENT

      self.max_nbr_of_worker = max_nbr_of_worker

    #if max_nbr_of_working_time_per_worker is None:
    #  self.max_nbr_of_working_time_per_worker = len(self.jobs)
    #else:
    
    # self.max_nbr_of_working_time_per_worker = NBR_WORK_TIME_SLOT_PER_TECH
    self.allow_overtime = allow_overtime
    self.run_mode = run_mode #  'train' for training, 'predict' for prediction new dataset.
    # each job [{ duration, gps: [x, y], fixed_schudule: [indicator, fixed_start, fixed_start], level }]
    self.jobs = jobs 
    self.JOB_COUNT = len(self.jobs ) 
    
    self.current_job_i = 0
    self.total_travel_time = 0
    self.total_assigned_job_duration = 0
    self.worker_jobs = [] # List of jobs assigned to each worker. Each one is [* 4 ]

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
    #  print(' error ')
      info =  'ok'
      if self.current_job_i == self.JOB_COUNT:
        done = True
        reward = self._get_reward() # 1
 
    obs = self._get_observation()
    return (obs, reward, done, info)

  def reset(self, shuffle_jobs=False):
    self.current_job_i = 0
    self.worker_ids = {}
    self.total_travel_time = 0
    self.total_assigned_job_duration = 0
    self.worker_jobs = [] # List of jobs assigned to each worker. Each one is [* 4 ]
    self.WORKER_COUNT = len(self.workers)
    
    if shuffle_jobs :
      random.shuffle(self.jobs)
    for worker_index in range(len(self.workers)):
      self.worker_ids[self.workers[worker_index]['worker_code']] = worker_index  # no used...
      self.workers[worker_index]['assigned_time_slots'] = []
      
      self.worker_jobs.append([]) # corresponding to self.workers[worker_index]['assigned_time_slots'] 

      if len(self.workers[worker_index]['working_time']) > 0 : 
        # TRUNCATE per model days
        self.workers[worker_index]['working_time'] = self.workers[worker_index]['working_time'][0:NBR_WORK_TIME_SLOT_PER_TECH]

        self.workers[worker_index]['free_time_slots']  = \
          list(map(lambda x: [x[0], x[1], 0, 0, 0, 0 ], self.workers[worker_index]['working_time']))
        # self.workers[worker_index]['assigned_time_slots'].append([])
        self.workers[worker_index]['assigned_time_slots'] = \
          list(map(lambda x:[], self.workers[worker_index]['working_time']))

        self.workers[worker_index]['worker_jobs']  = \
          list(map(lambda x:[], self.workers[worker_index]['working_time']))

        self.workers[worker_index]['total_free_duration']  = \
          sum(list(map(lambda x:x[1]-x[0], self.workers[worker_index]['free_time_slots'])))
        # IT is an array, each working_time slot has a max.
        self.workers[worker_index]['max_free_slot_duration']  = \
          max(list(map(lambda x:x[1]-x[0], self.workers[worker_index]['free_time_slots'])))
    
    return self._get_observation()

  def render(self, mode='human'):
    outfile = StringIO() if mode == 'ansi' else sys.stdout
    if self.current_job_i < self.JOB_COUNT:
      outfile.write(' '.join([ 'total: {}, '.format(len(self.jobs)),    'Next job:','{ curr=', str(self.current_job_i), ', dur=' , str( self.jobs[self.current_job_i]['duration']  )  \
         ,', gps=' , str( self.jobs[self.current_job_i]['job_gps']  ) , '}'  \
        , 'travel: ', str(self.total_travel_time), 'total_dur: ', str(self.total_assigned_job_duration),'\n' ]))
    else:
      outfile.write(' '.join([  'No next jobs ...'  \
        , 'travel: ', str(self.total_travel_time), 'total_dur: ', str(self.total_assigned_job_duration), '\n' ]) )

    for worker_index in range(len(self.worker_jobs)):
      job_count = 0
      job_list = list(map(lambda x:  x[0:2]  , self.workers[worker_index]['working_time']))
      for work_time_i in range(  len(self.workers[worker_index] ['assigned_time_slots'] ) ):  
        for time_slot_i in range(  len(self.workers[worker_index] ['assigned_time_slots'][work_time_i] ) ):
          job_list[work_time_i].append( \
               [ 'D-{}'.format(work_time_i), float('%.2f'% (self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [0] )), \
                 float('%.2f'% (self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [1] )), \
                 self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [4] 
            ]) 
          job_count += len(self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [4] )
          # print(work_time_i, time_slot_i)
          # I assume that all assigned_time_slots are ordered ascendingly, same as working_time
          # loop through 

      outfile.write(' '.join([     
        'Worker({:>1}): job_count({:>2})'.format(worker_index, job_count), '--->'.join([str(x) for x in  job_list])
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
        start_time_minute = start_time_minute + self.jobs[prev_job]['duration'] + travel_time  
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
    '''
      Worker(0): job_count(25) 
      [360, 1800, ['D-0', 1351.0, 1428.33, [0]], ['D-0', 1218.0, 1264.22, [40]], ['D-0', 1258.0, 1350.11, [68]]]
      --->[360, 1800, ['D-1', 1353.0, 1428.56, [36]], ['D-1', 1259.0, 1347.06, [49]]]
      --->[360, 1800, ['D-2', 755.0, 778.83, [21]], ['D-2', 810.0, 843.78, [59]], ['D-2', 755.0, 778.83, [67]]]
      --->[360, 1800, ['D-3', 1199.0, 1252.17, [63]], ['D-3', 1283.0, 1333.33, [70]]] 
          '''

    for  worker_index in range (len(self.workers)):
      for work_time_i in  range (len(self.workers[worker_index]['assigned_time_slots'])): # nth day.
        for assigned_i in range (len(self.workers[worker_index]['assigned_time_slots'][work_time_i])):
          
          start_minutes = 0
          prev_job = -1
          start_time_minute = self.workers[worker_index]['assigned_time_slots'][work_time_i][assigned_i][0]
          for assigned_job_j in range (len(self.workers[worker_index]['assigned_time_slots'][work_time_i][assigned_i][4])):
            # First find a possible time slot to insert into :
            job_index = self.workers[worker_index]['assigned_time_slots'][work_time_i][assigned_i][4][assigned_job_j]
            if assigned_job_j == 0:
              travel_time = 0
              # prev_job = job_index
              start_time_minute = self.workers[worker_index]['assigned_time_slots'][work_time_i][assigned_i][0]
            else:
              travel_time = get_travel_time_2locations(self.jobs[job_index]['job_gps'], self.jobs[prev_job]['job_gps'])
              start_time_minute = start_time_minute + self.jobs[prev_job]['duration'] + travel_time  
            
            one_job =  {
              'job_code': self.jobs[job_index]['job_id'],
              'job_type': self.jobs[job_index]['job_type'],
              "planning_status": "I", 
              "location_code": self.jobs[job_index]['location_code']  ,
              "geo_longitude": self.jobs[job_index]['geo_longitude']  ,
              "geo_latitude": self.jobs[job_index]['geo_latitude']  ,
              "requested_start_day":  date_util.add_days_2_day_string (self.config['data_start_day'], self.jobs[job_index]['requested_start_day_sequence'] )    ,

              "scheduled_worker_code": self.workers[worker_index]['worker_code'],
              "scheduled_start_day":  date_util.add_days_2_day_string (self.config['data_start_day'], work_time_i)    ,
              "scheduled_start_minutes":  start_time_minute,
              "scheduled_share_status":  'N'  ,

              #TODO
              "scheduled_duration_minutes": self.jobs[job_index]['requested_duration_minutes'],
              "scheduled_travel_minutes": 0 ,   #TODO, lookup previous one.

  
              'scheduled_travel_prev_code': self.jobs[prev_job] ['job_code'], 
              'scheduled_travel_minutes_before' : self._get_travel_time_2jobs(prev_job,job_index ),
              }

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
        if slot[1]-slot[0] < job['duration'] :
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




  # def _get_time_slot_intersection(self, worker_index, found_working_hour_index):

  def _add_current_job_to_worker_FT(self, worker_index, found_working_hour_index,predicted_action_start_time):
      # first find which time_slot to attach to
      # found_working_hour_index : is the n-th days to place the job.

      fixed_minute_time_slot = [self.jobs[self.current_job_i ]['fixed_schudule']['fixed_minute_time_slot'] [0] \
           , self.jobs[self.current_job_i ]['fixed_schudule']['fixed_minute_time_slot'] [1 ]  -  self.jobs[self.current_job_i ]['duration']  ]
      # good_time_slot_start_minute 
      if fixed_minute_time_slot[1] < fixed_minute_time_slot[0] and fixed_minute_time_slot[1] < 4*60:
        fixed_minute_time_slot[1] = fixed_minute_time_slot[1]  + (24*60)
      real_start_time = None
      if self.run_mode == 'train':
        action_job_start_time = predicted_action_start_time
      elif self.run_mode == 'predict':
        action_job_start_time  = predicted_action_start_time
        right_time_fixed=False
        if not ( fixed_minute_time_slot[0] < predicted_action_start_time <  fixed_minute_time_slot[1]):

          # This seems to be wrong!!! counting on next adjustment.2019-08-18 18:44:02
          # todo
          for time_slot_i in range (len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index])):
                # First find a possible time slot to insert into :
            if self._check_all_start_time_within_range (\
                      assigned_time_start =  self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [0]\
                      ,job_list_orig = self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [4].copy()\
                      ,new_job = self.current_job_i) :  
                  ####### this mean action time is in range of this assigned_time_slot.
                  action_job_start_time = ( self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [0] \
                                        + self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [1] ) / 2  
                  right_time_fixed = True

        if not ( fixed_minute_time_slot[0] < action_job_start_time <  fixed_minute_time_slot[1]):  
          action_job_start_time = fixed_minute_time_slot[0] # (fixed_minute_time_slot[1] + fixed_minute_time_slot[0] ) / 2 
      else:
        print('illegal run_mode')
        return False

      #if self.jobs[self.current_job_i]['job_seq'] == 55:
      #  print('job 55')
      if len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index]) < 1:
        # impossible? 
        if len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index]) >= MAX_ASSIGNED_TIME_SLOT_PER_DAY:
            print('Reached MAX_ASSIGNED_TIME_SLOT_PER_DAY job:{}, worker:{} ...'.format(self.current_job_i, worker_index ))
            return False

        self.workers[worker_index]['assigned_time_slots'][found_working_hour_index].append([  \
                action_job_start_time, # fixed_minute_time_slot[0],
                action_job_start_time  + self.jobs[self.current_job_i ]['duration'],  # fixed_minute_time_slot[0],
                self.jobs[self.current_job_i ]['job_gps'][0], 
                self.jobs[self.current_job_i ]['job_gps'][1], 
                  [self.current_job_i],
                0
                ])

        if (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][0][0] < 0):
          print('found negative start time and and i can not reject this time, SYSTEM ERROR')
           

        self.total_travel_time += 0
        self.current_job_i  +=  1
        return True

      '''
      possible_attach_time_slots = []
      for time_slot_i in range (len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index])):
          # First find a possible time slot to insert into :
        if (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [0] \
            >  fixed_minute_time_slot[1] + self.jobs[self.current_job_i ]['duration'] ) \
            or (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [1] \
            <  fixed_minute_time_slot[0] ):
            continue ####### this mean action time is out of range of this assigned_time_slot.

        possible_attach_time_slots.append(time_slot_i)
      '''
      possible_attach_time_slots = []
      for time_slot_i in range (len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index])):
        # First find a possible time slot to insert into :
        
        if   (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [0] \
              >  fixed_minute_time_slot[0] + self.jobs[self.current_job_i ]['duration'] ) \
          or (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [1] \
              <  fixed_minute_time_slot[1] \
            ): 
            possible_attach_time_slots.append(time_slot_i)
        '''
        if   (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [0] \
              <  action_job_start_time  < \
              self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [1]   \
            ): 
        '''
          


      if len(possible_attach_time_slots) < 1: # len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index]) < 1:
        # there is no existing a simply assigned_time_slot overlapping with this one. create the assigned_time_slot.
        if len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index]) >= MAX_ASSIGNED_TIME_SLOT_PER_DAY:
            print('Reached MAX_ASSIGNED_TIME_SLOT_PER_DAY job:{}, worker:{} ...'.format(self.current_job_i, worker_index ))
            return False
        # Insert a new assigned_time_slot to  
        insert_loc_i = 0
        for time_slot_j in range (len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index])):
          if action_job_start_time < self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [0]  :
            self.workers[worker_index]['assigned_time_slots'][found_working_hour_index].insert(0,[  \
                action_job_start_time, # fixed_minute_time_slot[0],
                action_job_start_time  + self.jobs[self.current_job_i ]['duration'],  # fixed_minute_time_slot[0],
                self.jobs[self.current_job_i ]['job_gps'][0], 
                self.jobs[self.current_job_i ]['job_gps'][1], 
                  [self.current_job_i],
                0
                ])
            self.total_travel_time += 0
            self.current_job_i  +=  1
            return True      
        # return True
        self.workers[worker_index]['assigned_time_slots'][found_working_hour_index].append([  \
                action_job_start_time, # fixed_minute_time_slot[0],
                action_job_start_time  + self.jobs[self.current_job_i ]['duration'],  # fixed_minute_time_slot[0],
                self.jobs[self.current_job_i ]['job_gps'][0], 
                self.jobs[self.current_job_i ]['job_gps'][1], 
                  [self.current_job_i],
                0
                ])
        if (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][0][0] < 0):
          print('found negative start time')
        self.total_travel_time += 0
        self.current_job_i  +=  1
        return True
              

      else:
        # i will try to attach the job to one of existing assigned_time_slot depending on travel time.
        tentative_travel_times = np.zeros(len(possible_attach_time_slots) * 2)

        for time_slot_i in range (len(possible_attach_time_slots)):
          # calculate distance to first job in this assigned time slot.
          current_loc = self.jobs[  self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][possible_attach_time_slots[time_slot_i]][4][0] \
            ]['job_gps'] 
          travel_time = get_travel_time_2locations(current_loc, self.jobs[self.current_job_i ]['job_gps'])
          # ## 2019-08-18 13:15:16 -- I will consider only appending to session. Not inserting to beginning.
          tentative_travel_times[time_slot_i*2] = 999999999# travel_time

          # calculate distance to last job in this assigned time slot.
          current_loc = self.jobs[  self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][possible_attach_time_slots[time_slot_i]][4][-1] \
            ]['job_gps'] 
          travel_time = get_travel_time_2locations(current_loc, self.jobs[self.current_job_i ]['job_gps'])
          tentative_travel_times[time_slot_i*2+1] = travel_time
          '''
          if not self._check_all_start_time_within_range (\
                      assigned_time_start =  self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [0]\
                      ,job_list_orig = self.workers[worker_index]['assigned_time_slots'][found_working_hour_index] [time_slot_i] [4].copy()\
                      ,new_job = self.current_job_i):
              tentative_travel_times[time_slot_i*2+1] = 999999999
'''
        # if flexible time:
        min_i = np.argmin(tentative_travel_times)
        if tentative_travel_times[min_i] == 999999999:
          return False

        time_slot_to_attach = possible_attach_time_slots[int(min_i/2) ]
        travel_time = tentative_travel_times[min_i]

        free_slot_durations = self._get_free_slot_durations(worker_index)
        if free_slot_durations[found_working_hour_index] - self.jobs[self.current_job_i ]['duration'] - travel_time < 0:
          # self.workers[worker_index]['working_time'][found_working_hour_index] [1] - self.workers[worker_index]['working_time'][found_working_hour_index] [0]) :
          # print("flexible job: no enough free time")
          if not self.allow_overtime:
            return False
        

        # if the job list end time is larger than customer period , put it to beginning.
        if  min_i % 2 == 0 or   fixed_minute_time_slot[1]   <  self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][1] + self.jobs[self.current_job_i ]['duration']: 
          #if (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_i][0] - self.jobs[self.current_job_i ]['duration']  - travel_time < self.workers[worker_index]['working_time'][found_working_hour_index] [0]) :
          #  return False
          # insert before current timeslot
          print("attaching to begining, because better serve it before.")
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][0] \
              -= self.jobs[self.current_job_i ]['duration']  + travel_time
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][4].insert(0,self.current_job_i)

          # insert to beginning
        else:
          #if  (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_i][1] + self.jobs[self.current_job_i ]['duration'] + travel_time > self.workers[worker_index]['working_time'][found_working_hour_index] [1]) :
          #   return False
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][1] \
              += self.jobs[self.current_job_i ]['duration']  + travel_time
          # append to end of existing visit
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][4].append(self.current_job_i)
        
        if (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][0][0] < 0):
          print('found negative start time - 2')
        
        
        self.total_travel_time += travel_time
        self.current_job_i  +=  1
        return True 
      return False






  def _add_current_job_to_worker(self, action) : # worker_index, working_time_index):
    # If there is not enough capacities without considering travel and time slot, reject it
    #if  self.jobs[self.current_job_i ]['duration'] > self.workers[worker_index]['max_free_slot_duration']:
    #  return False 
    #action [time_slot_i] = 1
    #for i in range(len(action) - 3):
    #  if action[i] == 1:
    max_i = np.argmax(action[0:self.WORKER_COUNT * NBR_WORK_TIME_SLOT_PER_TECH])
    worker_index = int(max_i/NBR_WORK_TIME_SLOT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)
    working_time_index = int(max_i % NBR_WORK_TIME_SLOT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)
    action_job_start_time = action[-2] * 1600
    action_job_duration = action[-1] * 200


    if worker_index >= len(self.workers):
      return False 
    if working_time_index >= len(self.workers[worker_index]['working_time']):
      print("larger than max working time index")
      return False

    if ( action_job_start_time < 0 ) or  (action_job_start_time > 1800):
      print("invalid time <0 or >1800")
      # return False

    # If the start time does not fall in working hour, reject it.
    found_working_hour_index = -1

    free_slot_durations = self._get_free_slot_durations(worker_index)
    if  free_slot_durations[working_time_index] > self.jobs[self.current_job_i ]['duration'] :
      # no more room in this time slot
      # print("no more room in this time slot")
      found_working_hour_index = working_time_index  #'''   '''
    '''else:
      if working_time_index > 0:
        if free_slot_durations[working_time_index -1 ] > self.jobs[self.current_job_i ]['duration']  :
          found_working_hour_index = working_time_index - 1
      elif working_time_index < len(self.workers[worker_index]['working_time']) - 1:
        if free_slot_durations[working_time_index + 1 ] > self.jobs[self.current_job_i ]['duration']  :
          found_working_hour_index = working_time_index + 1
    '''

    # The followoing is to make sure that the worker/time selected should have total duration less than a threshold.
    found_time_slot_flag = False
    

    if self.run_mode == 'predict':
      new_action = action.copy()
      for r_i in range(0, self.WORKER_COUNT * NBR_WORK_TIME_SLOT_PER_TECH): # len(self.workers)):
        work_duration_slots = self._get_work_duration_slots(worker_index)
        if ( work_duration_slots[working_time_index] + self.jobs[self.current_job_i ]['duration'] < MAX_WORKING_TIME_DURATION ):
          # no more room in this time slot
          # print("no more room in this time slot")
          found_working_hour_index = working_time_index  #'''   '''
          found_time_slot_flag = True
          break
        action[worker_index * NBR_WORK_TIME_SLOT_PER_TECH + working_time_index ] = 0
        max_i = np.argmax(action[0:self.WORKER_COUNT * NBR_WORK_TIME_SLOT_PER_TECH])
        worker_index = int(max_i/NBR_WORK_TIME_SLOT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)
        working_time_index = int(max_i % NBR_WORK_TIME_SLOT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)

      if not found_time_slot_flag:
        print("no slots < MAX_WORKING_TIME_DURATION, durig prediction, return false")
        return False


      if found_working_hour_index < 0:
          if  self.allow_overtime:
            found_working_hour_index = 0
          else:
            print("! self.allow_overtime, return false")
            return False

    travel_time = 0


    if self.jobs[self.current_job_i ]['job_type']== 'FS' :   
        # WRONG!!! TODO
        fs_start_minutes = (self.jobs[self.current_job_i ]['requested_start_day_sequence'] * 24*60 ) + self.jobs[self.current_job_i ]['requested_start_minutes']  

        appended_flag = False
        prev_time_slot_end_time = self.workers[worker_index]['working_time'][found_working_hour_index][0]
        for ts_i in range (len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index])):
          if self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][ts_i][0] <=fs_start_minutes  <= self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][ts_i][1] + self.jobs[self.current_job_i ]['duration']:
            print("fs conflict with existing time sloft.")
            return False
          
          if prev_time_slot_end_time <= fs_start_minutes  <= self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][ts_i][0]:
            # appended_start_time = self.workers[worker_index]['working_time'][found_working_hour_index][0] 
            self.workers[worker_index]['assigned_time_slots'][found_working_hour_index].insert(ts_i, [  \
                  fs_start_minutes,
                  fs_start_minutes+ self.jobs[self.current_job_i ]['duration'],
                  self.jobs[self.current_job_i ]['job_gps'][0], 
                  self.jobs[self.current_job_i ]['job_gps'][1], 
                   [self.current_job_i],
                  1
                  ])
            appended_flag = True
            self.total_travel_time += 0
            self.current_job_i  +=  1
            #break
            #return True
          prev_time_slot_end_time = self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][ts_i][1] 
        if not appended_flag:
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index].append([  \
                  fs_start_minutes,
                  fs_start_minutes+ self.jobs[self.current_job_i ]['duration'],
                  self.jobs[self.current_job_i ]['job_gps'][0], 
                  self.jobs[self.current_job_i ]['job_gps'][1], 
                    [self.current_job_i],
                  1
                  ])
          self.total_travel_time += 0
          self.current_job_i  +=  1
          return True
    elif self.jobs[self.current_job_i ]['job_type']  == 'FT' :     
        # 'fixed_schudule': {'fs_indicator': 'FT', 'fixed_minute_time_slot': [468, 1376]}, 
        
        return self._add_current_job_to_worker_FT( worker_index, found_working_hour_index,action_job_start_time)
        # 

    elif self.jobs[self.current_job_i ]['job_type'] == 'N' : 
      # first find which time_slot to attach to
      if len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index]) < 1:
        self.workers[worker_index]['assigned_time_slots'][found_working_hour_index].append([  \
                self.workers[worker_index]['working_time'][found_working_hour_index] [0],
                self.workers[worker_index]['working_time'][found_working_hour_index] [0] + self.jobs[self.current_job_i ]['duration'],
                self.jobs[self.current_job_i ]['job_gps'][0], 
                self.jobs[self.current_job_i ]['job_gps'][1], 
                  [self.current_job_i],
                0
                ])
        self.total_travel_time += 0
        self.current_job_i  +=  1
        return True
        # return True
      else:
        tentative_travel_times = np.zeros(len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index]) * 2)

        for time_slot_i in range (len(self.workers[worker_index]['assigned_time_slots'][found_working_hour_index])):
          # calculate distance to first job in this assigned time slot.
          current_loc = self.jobs[  self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_i][4][0] \
            ]['job_gps'] 
          travel_time = get_travel_time_2locations(current_loc, self.jobs[self.current_job_i ]['job_gps'])
          tentative_travel_times[time_slot_i*2] = travel_time

          # calculate distance to last job in this assigned time slot.
          current_loc = self.jobs[  self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_i][4][-1] \
            ]['job_gps'] 
          travel_time = get_travel_time_2locations(current_loc, self.jobs[self.current_job_i ]['job_gps'])
          tentative_travel_times[time_slot_i*2+1] = travel_time

        # if flexible time:
        min_i = np.argmin(tentative_travel_times)
        time_slot_to_attach = int(min_i/2)
        travel_time = tentative_travel_times[min_i]

        if free_slot_durations[found_working_hour_index] - self.jobs[self.current_job_i ]['duration'] - travel_time < 0:
          # self.workers[worker_index]['working_time'][found_working_hour_index] [1] - self.workers[worker_index]['working_time'][found_working_hour_index] [0]) :
          print("flexible job: no enough free time")
          return False

        if  min_i % 2 == 0: 
          #if (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_i][0] - self.jobs[self.current_job_i ]['duration']  - travel_time < self.workers[worker_index]['working_time'][found_working_hour_index] [0]) :
          #  return False
          # insert before current timeslot
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][0] -= self.jobs[self.current_job_i ]['duration']  + travel_time
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][4].insert(0,self.current_job_i)

          # If this assigned time slot is pushed out of head of working_time, adjust back to working time range. 
          if self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][0] < self.workers[worker_index]['working_time'][found_working_hour_index] [0]:
            self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][1]  +=  \
              self.workers[worker_index]['working_time'][found_working_hour_index] [0] - self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][0]
            self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][0]  = self.workers[worker_index]['working_time'][found_working_hour_index] [0]
          
          # insert to beginning
        else:
          #if  (self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_i][1] + self.jobs[self.current_job_i ]['duration'] + travel_time > self.workers[worker_index]['working_time'][found_working_hour_index] [1]) :
          #   return False
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][1] += self.jobs[self.current_job_i ]['duration']  + travel_time
          # append to end of existing visit
          self.workers[worker_index]['assigned_time_slots'][found_working_hour_index][time_slot_to_attach][4].append(self.current_job_i)
        self.total_travel_time += travel_time
        self.current_job_i  +=  1
        return True 
    else:
        print('wrong fs_indicator value.')
        return False
    print('reached end of execution . return False. ...')
    return False

  def _get_reward(self):
    reward = self.current_job_i / self.JOB_COUNT # + ( 1 - self.total_travel_time / 60)

    return reward


  def _get_work_duration_slots(self, worker_index):      
      work_slot_durations = list(map(lambda x: 0 , self.workers[worker_index]['working_time']))

      for work_time_i in range(  len(self.workers[worker_index] ['assigned_time_slots'] ) ): 
        for time_slot_i in range(  len(self.workers[worker_index] ['assigned_time_slots'][work_time_i] ) ):
          # I assume that all assigned_time_slots are ordered ascendingly, same as working_time
          # loop through 
          work_slot_durations [work_time_i ] +=  self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [1]  \
                                               - self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [0] 
                        
      return work_slot_durations

  def _get_free_slot_durations(self, worker_index):      
      free_slot_durations = list(map(lambda x:  x[1] - x[0]  , self.workers[worker_index]['working_time']))

      for work_time_i in range(  len(self.workers[worker_index] ['assigned_time_slots'] ) ): 
        for time_slot_i in range(  len(self.workers[worker_index] ['assigned_time_slots'][work_time_i] ) ):
          # I assume that all assigned_time_slots are ordered ascendingly, same as working_time
          # loop through 
          free_slot_durations [work_time_i ] -=  self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [1]  \
                                               - self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [0] 
                        
      return free_slot_durations
  def _get_observation(self):
    # agent_vector is current observation.  
    agent_vector = np.zeros(NBR_FEATURE_PER_TECH * self.WORKER_COUNT + NBR_FEATURE_VIST_n_OVERALL ) 

    # First all worker statistics
    for worker_index in range(len(self.workers)): 
      # assigned time slots for each worker in agent_vector  
      # curr_total_free_duration = self.workers[worker_index]['total_free_duration'] 

      # save (starttime, end time, gps x, gps y) for each assigned_time_slot

      for work_time_i in range(  len(self.workers[worker_index] ['assigned_time_slots'] ) ): 
        for time_slot_i in range(  len(self.workers[worker_index] ['assigned_time_slots'][work_time_i] ) ):
          agent_vector[NBR_FEATURE_PER_TECH*worker_index + work_time_i*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT  + time_slot_i*NBR_FEATURE_PER_WORK_SLOT + 0: \
                       NBR_FEATURE_PER_TECH*worker_index + work_time_i*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT  + time_slot_i*NBR_FEATURE_PER_WORK_SLOT + 4] \
            = list( map(truediv,  self.workers[worker_index] ['assigned_time_slots'][work_time_i][time_slot_i] [0:4], \
                                  [1800, 1800, 125, 35]
                  )) 
      '''  
      # Employee schedule - (start_time, end_time, break, overtime) 
      for work_time_i in range(  len(self.workers[worker_index] ['assigned_time_slots'] ) ): 
        agent_vector[NBR_FEATURE_PER_TECH*worker_index + NBR_WORK_TIME_SLOT_PER_TECH*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT + work_time_i*4 + 0: \
                     NBR_FEATURE_PER_TECH*worker_index + NBR_WORK_TIME_SLOT_PER_TECH*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT + work_time_i*4 + 2] \
            = self.workers[worker_index] ['working_time'] [work_time_i] [0:2] 
      '''
      # totoal free time for each work time slot . For example, 10 numbers for 10 days' job
      free_slot_durations = self._get_free_slot_durations(worker_index)
      MAX_FREE_DURATION_LIST = [x + 1000 for x in np.zeros(len(free_slot_durations)) ]
      # for work_time_i in range(  len(self.workers[worker_index] ['assigned_time_slots'] ) ): 
      agent_vector[NBR_FEATURE_PER_TECH*worker_index + NBR_WORK_TIME_SLOT_PER_TECH*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT + 0 : \
                   NBR_FEATURE_PER_TECH*worker_index + NBR_WORK_TIME_SLOT_PER_TECH*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT + ( 1 * NBR_WORK_TIME_SLOT_PER_TECH ) ]  \
             = list( map(truediv,  free_slot_durations  , MAX_FREE_DURATION_LIST )) 
      # curr_max_free_slot_duration = max(free_slot_durations)    

      worker_feature_begin_offset = NBR_FEATURE_PER_TECH*worker_index + NBR_WORK_TIME_SLOT_PER_TECH*MAX_ASSIGNED_TIME_SLOT_PER_DAY*NBR_FEATURE_PER_WORK_SLOT + NBR_WORK_TIME_SLOT_PER_TECH 
      # agent_vector[ worker_feature_begin_offset + 2] = curr_total_free_duration
      # agent_vector[worker_feature_begin_offset + 3] = curr_max_free_slot_duration

      # Home Location of the current worker  
      agent_vector[worker_feature_begin_offset +0] = self.workers[worker_index]['home_gps'][0] / 125
      agent_vector[worker_feature_begin_offset +1] = self.workers[worker_index]['home_gps'][1] / 35

      # Historical customer visit GPS Gaussian , Sigma, Gamma, 2 DIMENSIONAL 
      # 4
      # 
      agent_vector[worker_feature_begin_offset +2] \
        = self.workers[worker_index]['level'] 

    # Now append the visit information AS THE 2nd half.
    if self.current_job_i < self.JOB_COUNT:
      # Location of the new job is added to the end of agent_vector.   
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +0] = self.jobs[self.current_job_i]['duration']   / 800
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +1] = self.jobs[self.current_job_i]['job_gps'] [0] /125
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +2] = self.jobs[self.current_job_i]['job_gps'] [1] /35
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +3] = self.jobs[self.current_job_i]['requested_start_day_sequence'] / 30  
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +4] = self.jobs[self.current_job_i]['tolerated_day_min']  /10
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +5] = self.jobs[self.current_job_i]['tolerated_day_max']  /10


      #if self.jobs[self.current_job_i]['fixed_schudule']['fs_indicator'] == 'FT':
      if self.jobs[self.current_job_i]['job_type']  == 'FT':
          agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +6] = 1
          agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +7] = self.jobs[self.current_job_i]['fixed_schudule']['fixed_minute_time_slot'][0] /1800
          agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +8] = self.jobs[self.current_job_i]['fixed_schudule']['fixed_minute_time_slot'][1] /1800

      if self.jobs[self.current_job_i]['job_type']  == 'FS':
      #if self.jobs[self.current_job_i]['fixed_schudule']['fs_indicator'] == 'FS':
          agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +9] = 1
          agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +10] = 0# self.jobs[self.current_job_i]['fixed_schudule']['fs_start_time'] 

          agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +11] = 0# self.jobs[self.current_job_i]['fixed_schudule']['fixed_minute_time_slot'][1]



      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +12] = 0 # self.jobs[self.current_job_i]['qpms_z_indicator']  

      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +16] = 0 # self.jobs[self.current_job_i]['customer_level']  
      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +17] = 0 # self.jobs[self.current_job_i]['product_level']  

      agent_vector[self.WORKER_COUNT*NBR_FEATURE_PER_TECH +20: \
                   self.WORKER_COUNT*NBR_FEATURE_PER_TECH +20 + len(self.jobs[self.current_job_i]['history_job_worker_count'])] \
            =  list( map(truediv,  self.jobs[self.current_job_i]['history_job_worker_count'] , \
                                   [x + 50 for x in np.zeros( len(self.jobs[self.current_job_i]['history_job_worker_count'])   ) ] \
                ))

    # Finished looping through all workers
    return agent_vector

  def gen_action_from_one_job(self, one_job):
    n = np.zeros(len(self.workers)* NBR_WORK_TIME_SLOT_PER_TECH + 3 )

    n[one_job['actual_worker_index'] * NBR_WORK_TIME_SLOT_PER_TECH + one_job['actual_job_day'] ] = 1

    n[-2] = one_job['actual_start_minutes'] / 1600 # 288
    n[-1] = one_job['requested_duration_minutes'] / 200 # 60
    return n

  # **---------------------------------------------------------------------------- 
  # ## Extended functions
  # **---------------------------------------------------------------------------- 

  def replay_env(self):
    return self.reset()

  def render_action(self, action ):

    max_i = np.argmax(action[0:self.WORKER_COUNT * NBR_WORK_TIME_SLOT_PER_TECH])
    worker_index = int(max_i/NBR_WORK_TIME_SLOT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)
    working_time_index = int(max_i % NBR_WORK_TIME_SLOT_PER_TECH ) # self.max_nbr_of_working_time_per_worker)
    job_start_time = action[-2] * 1600
    action_job_duration = action[-1] * 200


    return  "worker: {}, start_time: ({})={}".format(worker_index, job_start_time, \
           date_util.minutes_to_time_string( job_start_time * 5  )   ) 





import tensorflow as tf
from tensorflow.keras.models   import   Sequential
from tensorflow.keras.layers     import Dense
from tensorflow.keras.optimizers import Adam


class DispatchV2DenseAgent:
    env = None
    trained_model = None
    MAX_EPOCHS = 30
    config={}
    def __init__(self, env = None,trained_model=None, MAX_EPOCHS=30, nbr_of_actions = 1):     
        self.env = env
        self.MAX_EPOCHS = MAX_EPOCHS
        self.trained_model = trained_model

    def load_model(self, filename):
        self.trained_model = tf.keras.models.load_model(filename)

    def _build_model(self, input_size, output_size):
        model = Sequential()
        model.add(Dense(512, input_dim=input_size, activation='relu'))
        model.add(Dense(256, activation='relu'))
        model.add(Dense(256, activation='relu'))
        model.add(Dense(256, activation='relu')) 

        model.add(Dense(output_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam())


        print(model.summary())
        return model


    def train_model(self, training_data, model_path = None):
        X = np.array([i[0] for i in training_data]).reshape(-1, len(training_data[0][0]))
        y = np.array([i[1] for i in training_data]).reshape(-1, len(training_data[0][1]))
        trained_model = self._build_model(input_size=len(X[0]), output_size=len(y[0]))

        trained_model.fit(X, y, epochs=self.MAX_EPOCHS)


        self.trained_model = trained_model
        trained_model.save(model_path) 

        return trained_model


    def predict_action( self, observation = None):
        action =  self.trained_model.predict(observation.reshape(-1, len(observation)))[0]
        return action


if __name__ == '__main__':
    # main()
    pass