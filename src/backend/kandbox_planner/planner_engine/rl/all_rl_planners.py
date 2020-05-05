'''
This is ************* step 1: move rules out of env definition.
refer to xls design file. 
/Users/qiyang/Documents/qduan/git/work_git/field_service_robot/doc/dispatch_ai_model_design.xlsx
-- Entrada_v2


step 2: Then I will change network layout to multiple input (cnn + dense)
https://www.pyimagesearch.com/2019/02/04/keras-multiple-inputs-and-mixed-data/
/Users/qiyang/Downloads/Houses-dataset

https://medium.com/datadriveninvestor/dual-input-cnn-with-keras-1e6d458cd979

'''
import itertools
import pickle 
import json
import numpy as np 
import random
import gym
import glob

import pandas as pd
# import sys
from pathlib import Path 
from pprint import pprint

import kandbox_planner.util.planner_date_util  as date_util
from kandbox_planner.fsm_adapter.kplanner_db_adapter import KPlannerDBAdapter 
kplanner_db = KPlannerDBAdapter()

from datetime import datetime  
from datetime import timedelta  
from datetime import date




import kandbox_planner.config as config

save_training_data = True

from kandbox_planner.planner_engine.rl.env.kprl_env_5minutes2workertime  import  KPRL5Minutes2WorkerTime 
from kandbox_planner.planner_engine.rl.agent.kprl_env_5minutes2workertime_agent  import KPRLDenseAgent, KPRLRandomGuessAgent
from kandbox_planner.planner_engine.rl.agent.kprl_env_5minutes2workertime_cnnagent  import KPRLCNNDenseAgent  

from kandbox_planner.planner_engine.rl.env.kprl_env_v2_merged_timeslot import DispatchV2Env, DispatchV2DenseAgent

#from kandbox_planner.planner_engine.toy_planner_rl.envs.kprl_env_with_history import KPlannerEnvWithHistory
#from kandbox_planner.planner_engine.toy_planner_rl.envs.kprl_agent_heuristic_single_job_history import HeuristicAgentSingleJobByHistory


from kandbox_planner.planner_engine.rl.env.kprl_env_rllib_history_affinity import KPlannerHistoryAffinityTopNGMMEnv
from kandbox_planner.planner_engine.rl.agent.kprl_agent_heuristic_single_job_history import HeuristicAgentSingleJobByHistory


kp_models = { 
  "5minutescnn_dense_1": { 
          "planner_env_class": KPRL5Minutes2WorkerTime,
          "planner_agent_class": KPRLCNNDenseAgent,
          },
  "5minutes_dense_1": { 
          "planner_env_class": KPRL5Minutes2WorkerTime,
          "planner_agent_class": KPRLDenseAgent,
          },
  "rl_random_1": { 
          "planner_env_class": KPRL5Minutes2WorkerTime,
          "planner_agent_class": KPRLRandomGuessAgent,
          },
  "dispatch_v2_1": { 
          "planner_env_class": DispatchV2Env,
          "planner_agent_class": DispatchV2DenseAgent,
          },
  "rl_heur": { 
          "planner_env_class": KPlannerHistoryAffinityTopNGMMEnv,
          "planner_agent_class": HeuristicAgentSingleJobByHistory,
          },
}


# batch_name = "5minutescnn_dense_1"
working_dir = config.KANDBOX_TEST_WORKING_DIR
# print("working_dir Path:", working_dir)   





#goal_steps = 1
score_requirement = 60
#goal_steps = 500


nbr_testing_days = 2


reward_requirement = 0.85 # 1.45 # 0.95 


MAX_PICKLE_DUMP_LENGHT = 20000

# training_data_start = '2019-01-01'
# training_data_end = '2019-01-11'



def training_data_permutation_preparation(batch_name, GENERATOR_START_DATE, TRAINING_DAYS,intial_games ):
    training_data = []
    # current_day = kplanner_db.GENERATOR_START_DATE
    
    # print("worker id to index: ", workers_id_dict)

    for day_i in  range( 0, TRAINING_DAYS ): #TODO~
      current_day = GENERATOR_START_DATE + timedelta(days=day_i) 
      current_day_str = datetime.strftime(current_day, config.KANDBOX_DATE_FORMAT)
      workers, workers_id_dict = kplanner_db.load_transformed_workers(start_day = current_day_str) # ['result'] , nbr_days = 1
      # print("getting data for: ", current_day)
      #k_order = kplanner_db.select_all_orders(current_day = current_day)
      #jobs = transform_orders(k_order, workers_id_dict = workers_id_dict)
      jobs = kplanner_db.load_transformed_jobs_from_status(workers_id_dict = workers_id_dict, start_day = current_day_str, nbr_days = 1)

      #print('doing date: {}, # of workers in training_data: {}'.format(training_data_start,len(workers)))
      #continue
      # , allow_overtime=True,  max_nbr_of_worker = len(workers)
      training_data_replay_one_day(batch_name, workers, jobs,  training_data,intial_games)
      print('finished one replay for date: {}, # of actions in training_data: {}'.format(current_day,len(training_data)))

    return training_data




def change_list_move_sunday_to_end( jobs, ji_list):
  return ji_list
  
  for ji in ji_list:
    if jobs[ji]['actual_job_day_weekday'] == 6: # This is sunday
      ji_list.remove(ji)
      ji_list.append(ji)
  return ji_list

def training_data_replay_one_day(batch_name, workers, jobs,   training_data, intial_games):
    # training_data = []
    accepted_scores = []
    accepted_rewards = []
    #list_of_index = list(range(0,len(jobs)))
    #list_of_index_permuted = list(itertools.permutations(list_of_index)  )
    #list_of_jobs_permuted = [] # list(itertools.permutations(jobs) )
    # print(len(list_of_index_permuted))
    # -- can not print 11,978,571,669,969,900,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000,000
    i=0 

    # random.shuffle(jobs)
    # max_nbr_of_worker =  len(workers)  

    
    # map(lambda x: , mylis)
    # [item.upper() for item in mylis]
    
    for i in range(0,intial_games): 
        score = 0 
        reward = 0
        game_memory = []
        ji_list = random.sample(range(0,len(jobs)), len(jobs))
        #TODO , remove from training.s
        ji_list = change_list_move_sunday_to_end(jobs, ji_list)
        game_jobs = [jobs[ji].copy() for ji in ji_list] # 

        # Shuffle workers and redefine job_code
        worker_shuffle_list = random.sample(range(0,len(workers)), len(workers))
        # print("Game {} is using shuffle list: {}".format(i, worker_shuffle_list))
        game_workers = [workers[wji].copy() for wji in worker_shuffle_list] # 

        # worker_shuffle_list_reverse_index = [ worker_shuffle_list.index(wj) for wj  in worker_shuffle_list]
        for job_seq_i in range(0,len(jobs)):
          game_jobs[job_seq_i]['actual_worker_index'] = worker_shuffle_list.index(game_jobs[job_seq_i]['actual_worker_index'])
          game_jobs[job_seq_i]['history_job_worker_count'] = [ game_jobs[job_seq_i]['history_job_worker_count'][wj] for wj  in worker_shuffle_list]  
        
        choices = []
        # shuffled workers 
        #env.workers = game_workers
        #env.jobs = game_jobs
        env = kp_models[batch_name]['planner_env_class'](workers=game_workers, jobs=game_jobs)
        env.reset()

        env.reset(shuffle_jobs=False) 
        previous_observation = env._get_observation() # []
        for step_index in range(len(game_jobs)):
            #print('games: {}, steps: {}, score: {}, reward: {}, info: {}, current_job: {}'.format(\
            #    game_index, step_index, score, reward,1, env.current_job_i))        
            # print([game_jobs[step_index ]['job_seq']    ] )    
            action = env.gen_action_from_one_job(  game_jobs[step_index] )
             
            # action = act[step_index]
            #if step_index == 40:
            #  print("step == pasue")
            observation, reward, done, info = env.step(action) 
            if len(previous_observation) > 0:
                game_memory.append([previous_observation, action, [w['worker_code'] for w in game_workers] ]  )

            previous_observation = observation
            score += reward  
            if done or info=='error':
              #print('Finished game: {}, steps: {}, score: {}, reward: {}, info: {}, current_job: {}, max_job_#: {}'.format(\
              #  i, step_index, score, reward,info, env.current_job_i, len(game_jobs)))
              # env.render()
              break
    

        # print(i, 'game choices: ', choices)
        if  True: # reward > reward_requirement : #  and info=='ok'
            #print('games: {}, steps: {}, score: {}, reward: {}, info: {}, current_job: {}'.format(\
            #     i, step_index, score, reward,1, env.current_job_i))    
            # env.render()
            #print_observation (observation)
            #print(env.get_solution_json())

        #if score >= score_requirement or reward > reward_requirement:
            # print('steps: {}, score: {}, reward: {}, info: {}'.format(step_index, score, reward,info))
            accepted_scores.append(reward) # not score
            for data in game_memory:
                training_data.append(data[:])

    # return training_data
 

# ================================================================================


# ================================================================================


def run_rl_over_batch(rl_env_name = None, env_config = None, prev_planner_code=None, prev_game_code=None):
  start_time = datetime.strptime(env_config['data_start_day'], config.KANDBOX_DATE_FORMAT)  
  

  worker_df  = kplanner_db.load_worker_status_df(
                game_code  = prev_game_code+'_i',
                worker_list = []
                )
  jobs_df  = kplanner_db.load_job_status_df(
                game_code  = prev_game_code,
                planner_code = prev_planner_code,
                start_day = env_config['data_start_day'], 
                end_day = date_util.add_days_2_day_string(k_day=  env_config['data_start_day'], days=30),
                order_by= None # ' job_code '
                )
  transformed_workers, workers_id_dict = kplanner_db._transform_workers(k_workers=worker_df, start_date=start_time)
  transformed_jobs = kplanner_db._transform_jobs(jobs=jobs_df, start_date=start_time)
  if len(transformed_jobs) < 1:
    print('nothing to work on !')
    return

  env = kp_models[rl_env_name]['planner_env_class'](workers=transformed_workers, jobs=transformed_jobs, env_config=env_config, from_db=False)
  
  model_agent = kp_models[rl_env_name]['planner_agent_class'](env=env,nbr_of_actions = 2)
  # model_agent.load_model(filename = "{}/trained_model_{}_model.h5".format(working_dir, rl_env_name))
  # 

  observation = env.replay_env()
  env.config['run_mode'] = 'predict'

  print(datetime.now(), "Finished env replay" )

  step_result_flag = 0
  for step_index in range(len(env.jobs)):
    #if step_index == 3:
    # print("debug step_index: {}".format(step_index))
    if env.current_job_i >= len(env.jobs):
      continue
    if env.jobs[env.current_job_i]['job_code'] in ['1016439_1_TRBSB_2_13' ]:
      print('pause for debug')

    if 'job_status' in env.jobs[env.current_job_i].keys() and ( env.jobs[env.current_job_i]['job_status'] in ['P','I'] ):
      # action = env.gen_action_from_scheduled_job(one_job = env.jobs[env.current_job_i] ) 
      print("job ({}) is skipped for {} status".format(env.jobs[env.current_job_i]['job_code'],  env.jobs[env.current_job_i]['job_status']))
      env.current_job_i +=1
      continue
    
    else:
      action = model_agent.predict_action(observation= observation ) # [0]
      step_result_flag+=1
      # action = adjust_action_for_sunday (action)

    # action = gen_random_action()
    if  (action is None) or (len(action) <1):
      print("Failed to get prediction for job ({}) ".format(env.jobs[env.current_job_i]['job_code']))
      return
      break
    observation, reward, done, info = env.step(action)  
    # pprint(env.render_action(action))
    # 
    if done : # or info=='error':
      adict = env.decode_action_into_dict(action)
      print("Final Error for action step {}, current_job _i : {}, action: {}. Done".format(step_index, env.current_job_i ,adict ))  
      # failed_jobs.append([step_index, env.current_job_i]) # , env.jobs[env.current_job_i]
      # print(env.get_solution_json())
      # print_observation (observation)
      # print("action: ", action)
      # env.render()
      break
      info['action'] = adict
      env.jobs[env.current_job_i]['error_message'] = json.dumps(info)
      env.current_job_i +=1
      continue

  #if len(step_result_flag) > 0:
  #  continue
  print("Dispatch Done: action job_count: {} ".format( (step_result_flag) )) 
  # env.render()
  result_json = env.get_solution_json()

  solution_df_all = pd.DataFrame(result_json)
  solution_df = solution_df_all[['job_code', 'job_type', 'location_code',
    'geo_longitude', 'geo_latitude','changed_flag',  'planning_status', 'scheduled_share_status','scheduled_worker_code', 'requested_start_day',
    'scheduled_start_minutes', 'scheduled_start_day','scheduled_duration_minutes',
    'scheduled_travel_prev_code', 'scheduled_travel_minutes_before']].copy()

  return solution_df


def get_rl_planner(planner_code = None, env_config=None, replay=False, predict_unplanned=False):
  current_day_str = env_config['data_start_day']
  #workers, workers_id_dict = kplanner_db.load_transformed_workers (start_day = current_day_str) # ['result'] , nbr_days = 1
  #jobs = kplanner_db.load_transformed_jobs_current(start_day = current_day_str, nbr_days = env_config['nbr_of_days_planning_window'])
  env_config['kplanner_db'] = kplanner_db
  
  print("I am predicting for day:", current_day_str )
  # print(jobs)
  # ricnenv.KPRL5Minutes2WorkerTime
  # TODO: add to env config. , allow_overtime=True,  max_nbr_of_worker = len(workers) env.run_mode = 'predict'
  env = kp_models[planner_code]['planner_env_class']( env_config=env_config, from_db=True )
  
  model_agent = kp_models[planner_code]['planner_agent_class'](env=env,nbr_of_actions = 2)
  model_agent.load_model(filename = "{}/trained_model_{}_model.h5".format(working_dir, planner_code))

  # ================================================================================
  planner = {
    'planner_env':env,
    'planner_agent':model_agent
  }

  observation = env.reset()
  if replay:
    observation = env.replay_env()
    env.config['run_mode'] = 'predict'

  if predict_unplanned:
    print("Prediction Game: {}, started ...".format(planner_code))
    exec_rl_planner(planner)

   
  return planner

def exec_rl_planner(planner=None):
  env = planner['planner_env']
  observation=env._get_observation_numerical()
  # done = (env.current_job_i >= len(env.jobs))

  done = not (env._move_to_next_job())
  for step_index in range(len(env.jobs)):
    if done:
      break
    if env.jobs[env.current_job_i]['job_code'] == '0424-20-FS':
      print('pause for debug')
    action_list = planner['planner_agent'].predict_action_list( )
    

    observation, reward, done, info = env.step( action_list[0])  

    b_dict = planner['planner_env'].decode_action_into_dict( action_list[0])

  env._commit_changed_jobs()



def rl_run_all(batch_name = None, train_again = False, TRAINING_DAYS=1, PREDICTION_DAYS = 1, intial_games = 1, MAX_EPOCHS = 30):
  # ================================================================================ 
  GENERATOR_START_DATE = datetime.strptime(config.KANDBOX_TEST_START_DAY,config.KANDBOX_DATE_FORMAT) #date(2019, 11, 1)
  
  if train_again:
    training_data = training_data_permutation_preparation(batch_name, GENERATOR_START_DATE = GENERATOR_START_DATE
      , TRAINING_DAYS=TRAINING_DAYS, intial_games = intial_games)


    # print(accepted_scores)
    if save_training_data:
      try:
        pickle.dump(training_data,    open("{}/training_data_{}.pkl".format(working_dir, batch_name), "wb" ) )
        training_data =  pickle.load( open("{}/training_data_{}.pkl".format(working_dir, batch_name), "rb" ) )
      
      except:  
        '''
        for a in range(int(len(training_data)/MAX_PICKLE_DUMP_LENGHT) ):
            pickle.dump(training_data[a*MAX_PICKLE_DUMP_LENGHT:(a+1)*MAX_PICKLE_DUMP_LENGHT],    open( "/my/temp/t_data_{}.pkl".format(a), "wb" ) )
        pickle.dump(training_data[(a+1)*MAX_PICKLE_DUMP_LENGHT:],    open( "/my/temp/t_data_{}.pkl".format(a+1), "wb" ) )
        '''
        print("failed to save training data, but continue")
    model_agent = kp_models[batch_name]['planner_agent_class'](MAX_EPOCHS = MAX_EPOCHS)
    trained_model = model_agent.train_model(training_data, model_path = "{}/trained_model_{}_model.h5".format(working_dir, batch_name))
    # print('tf eager:', tf.executing_eagerly())
    # pickle.dump(trained_model, open( "{}/trained_model_{}_model.pkl".format(working_dir, batch_name) , "wb" ) )
    
  # trained_model =  pickle.load( open( "{}/trained_model_{}_model.pkl".format(working_dir, batch_name) , "rb" ) )



  for predict_day_i in range(PREDICTION_DAYS):

    current_day = GENERATOR_START_DATE + timedelta(days=TRAINING_DAYS+predict_day_i) 
    current_day_str = datetime.strftime(current_day, config.KANDBOX_DATE_FORMAT)
    workers, workers_id_dict = kplanner_db.load_transformed_workers (start_day = current_day_str) # ['result'] , nbr_days = 1
    jobs = kplanner_db.load_transformed_jobs_current(start_day = current_day_str, nbr_days = 1)

    print("I am predicting for day:", current_day )
    # print(jobs)
    if len(jobs) < 1:
      print("no jobs to predict: ", len(jobs))
      exit(0)
  
    # ricnenv.KPRL5Minutes2WorkerTime
    # TODO: add to env config. , allow_overtime=True,  max_nbr_of_worker = len(workers) env.run_mode = 'predict'
    env = kp_models[batch_name]['planner_env_class'](workers=workers, jobs=jobs, env_config={'data_start_day': datetime.strftime(current_day, config.KANDBOX_DATE_FORMAT)})
    
    model_agent = kp_models[batch_name]['planner_agent_class'](env=env,nbr_of_actions = 2)
    model_agent.load_model(filename = "{}/trained_model_{}_model.h5".format(working_dir, batch_name))
    # ================================================================================


    success_steps = [] 

    step_result_flag = []
    for game_index in range(1):
        failed_jobs = []
        choices = []
        # env.reset(shuffle_jobs=False)
        observation = env.replay_env()
        env.config['run_mode'] = 'predict'
        # print("Prediction Game: {}, started ...".format(game_index))
        for step_index in range(len(env.jobs)):
          #if step_index == 3:
          # print("debug step_index: {}".format(step_index))
          if env.current_job_i >= len(env.jobs):
            continue
          if '10019770|65|PESTS|19/08/19' in str(env.jobs[env.current_job_i]['job_code']):
            print('pause for debug')

          if 'job_status' in env.jobs[env.current_job_i].keys() and ( env.jobs[env.current_job_i]['job_status'] in ['P','I'] ):
            action = env.gen_action_from_scheduled_job(one_job = env.jobs[env.current_job_i] ) 
            print("job ({}) is recovered from {} status".format(env.jobs[env.current_job_i]['job_code'],  env.jobs[env.current_job_i]['job_status']))
          else:
            action = model_agent.predict_action(observation= observation ) # [0]
            # action = adjust_action_for_sunday (action)
  
          # action = gen_random_action()
          if  (action is None) or (len(action) <1):
            print("Failed to get prediction for job ({}) ".format(env.jobs[env.current_job_i]['job_code']))
            return
            break
          observation, reward, done, info = env.step(action)  
          # pprint(env.render_action(action))
          # 
          if done : # or info=='error':
            # adict = env.decode_action_into_dict(action)
            print("Final Error for action step {}, current_job _i : {}, action: {}. Done".format(step_index, env.current_job_i ,action ))  
            # failed_jobs.append([step_index, env.current_job_i]) # , env.jobs[env.current_job_i]
            # print(env.get_solution_json())
            # print_observation (observation)
            # print("action: ", action)
            # env.render()
            break
            info['action'] = adict
            env.jobs[env.current_job_i]['error_message'] = json.dumps(info)
            env.current_job_i +=1
            continue
          
          # print(info)
          step_result_flag.append(1 if info=='ok' else 0)


          if info=='error':
            failed_jobs.append([step_index, env.current_job_i]) # , env.jobs[env.current_job_i]
            env.current_job_i+=1
          elif info=='ok':
            success_steps.append(env.current_job_i)
        #print(success_steps)
        #print(choices)
        #if len(step_result_flag) > 0:
        #  continue
        print("Dispatch Done: Job_count: {}, info_ok: {}".format(len(step_result_flag), sum(step_result_flag))) 
        env.render()
        # print("Dispatch Done: Game: {}, info: {}, reward: {}, action: {}".format(game_index, info,reward, 1)) 
        result_json = env.get_solution_json()
        with open('{}/result_{}.json'.format(working_dir,datetime.strftime(current_day,config.KANDBOX_DATE_FORMAT)),  "w", encoding="utf8") as json_file:
          # json.dump(result_json, json_file)
          print("not saved. .... Generated dispatch result file : ", '{}/result_{}.json'.format(working_dir,datetime.strftime(current_day,config.KANDBOX_DATE_FORMAT)) )
        # kplanner_db.save_RL_dispatched_orders_one_day(result_json)
        if len(result_json) < 1:
          print("Empty result  [], no saving ")
          continue
        solution_df_all = pd.DataFrame(result_json)
        solution_df = solution_df_all[['job_code', 'job_type', 'location_code',
          'geo_longitude', 'geo_latitude',  'planning_status', 'scheduled_worker_code', 'requested_start_day', # 2020-04-16 15:18:19 ?
          'scheduled_start_minutes', 'scheduled_start_day','scheduled_duration_minutes',
          'scheduled_travel_prev_code', 'scheduled_travel_minutes_before','scheduled_share_status']].copy()

        curr_game_code = '{}-{}'.format(batch_name, datetime.strftime(current_day, config.KANDBOX_DATE_FORMAT)) 
        #solution_df['game_code'] = curr_game_code
        game_info = {
              'planner_code': batch_name,
              'game_code': curr_game_code,
          }

        jobs_df = kplanner_db._convert_df_day_minutes_to_datetime(jobs_df= solution_df, drop_original=False)
        kplanner_db.save_schedued_jobs(jobs_df, game_info, update_current=False)
        kplanner_db.save_game_info(game_code=curr_game_code
                  , planner_code=batch_name
                  , data_start_day = datetime.strftime(current_day, config.KANDBOX_DATE_FORMAT)
                  , data_end_day = datetime.strftime( current_day + timedelta(days=1) , config.KANDBOX_DATE_FORMAT))


if __name__ == '__main__':

    rl_run_all(batch_name = 'rl_heur', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 1, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    exit(0)




    rl_run_all(batch_name = '5minutes_dense_1', train_again = True, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 0, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    rl_run_all(batch_name = '5minutes_dense_1', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 3, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)

    rl_run_all(batch_name = '5minutescnn_dense_1', train_again = True, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 0, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    rl_run_all(batch_name = '5minutescnn_dense_1', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 3, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)

    rl_run_all(batch_name = 'dispatch_v2_1', train_again = True, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 0, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)
    rl_run_all(batch_name = 'dispatch_v2_1', train_again = False, TRAINING_DAYS=config.RL_TRAINING_DAYS, PREDICTION_DAYS = 3, intial_games = 120, MAX_EPOCHS = config.RL_MAX_EPOCHS)



  # list(kp_models.keys())[3]