



# from kandbox_planner.planner_engine.rl.env.kprl_reward_function import  kprl_rule_set
 
from kandbox_planner.planner_engine.rl.env.reward.reward_function import  RewardFunction
import kandbox_planner.util.planner_date_util  as date_util



class SufficientTravelTimeReward(RewardFunction):
  """
    Has the following members 
  """
  rule_code = "sufficient_travel_time_previous_n_next"
  rule_name = "Job is not blocked by other jobs"
  message_template = "Job ({}) to Job ({}) requires {} minutes, but only {} minutes in between"
  success_message_template = "Job ({}) to Job ({}) requires {} minutes, and there are  now {} minutes."

  result = {
    'score': 0,
    'message':'',
    'prev_job_index':None,
    'prev_travel_time':0,
  }
  def evalute_normal_single_worker_n_job(self,  env = None,  job = None): # worker = None,
    # return score, violated_rules (negative values)
    # return self.weight * 1 
    # Now check if this new job can fit into existing slots by checking travel time
    travel_time = 0
    prev_job = None
    next_job = None
    new_job_loc_i=0
    worker_code = job['scheduled_worker_code']
    job_start_time = job['assigned_start_minutes']


    for job_i in range(len(env.workers_dict[worker_code]['assigned_jobs'])):
      a_job = env.jobs[
          env.workers_dict[worker_code]['assigned_jobs'][job_i]['job_index']
        ]
      if a_job['assigned_start_minutes'] < job_start_time:
        prev_job = a_job
      if a_job['assigned_start_minutes'] > job_start_time: # can not be equal
        next_job = a_job
        break
      new_job_loc_i+=1
    
    
    overall_message = ""
    res = self.result.copy()
    res['new_job_loc_i'] = new_job_loc_i
    if prev_job : 
        # same job , one is virtual for checking.
    
      prev_travel_time = env._get_travel_time_2jobs( job['job_index'], prev_job['job_index'] )
      # print( job['job_index'] , prev_job['job_index']) 
      if (job['job_index'] == prev_job['job_index']):
         print( "same:", job['job_index'] , prev_job['job_index']) 
      else: #  (job['job_index'] != prev_job['job_index'])  :
        # no more room in this time slot 
        res['prev_job_index'] = prev_job['job_index']
        res['prev_travel_time'] = prev_travel_time
      if ( job_start_time - prev_travel_time <  prev_job['assigned_start_minutes'] + prev_job['scheduled_duration_minutes']):
        res['message'] = "Not enough travel time from prev_job: {}, rejected.".format(prev_job['job_code'])
        res['score'] = -1
        # print( res['message']) 
        return res
      else:
        overall_message += "(Prev_job={}, travel_time={}) ".format(prev_job['job_code'],int(prev_travel_time) )
    else:
      res['prev_job_index'] = None
      res['prev_travel_time'] = 0

    if next_job :
      next_travel_time = env._get_travel_time_2jobs(  job['job_index'] , next_job['job_index'])
      res['next_job_index'] = next_job['job_index']
      res['next_travel_time'] = next_travel_time
      if next_travel_time >  next_job['assigned_start_minutes'] - job_start_time - job['scheduled_duration_minutes']:
        # no more room in this time slot
        res['message'] = "Not enough travel time from next_job: {}, rejected.".format(next_job['job_code'])
        res['score'] = -1
        # print( res['message']) 
        return res
      else:
        overall_message += "(Next_job={}, travel_time={}) ".format(next_job['job_code'],int(next_travel_time) )

    res['message'] = "Got enough travel minutes.".format() + overall_message
    res['score'] = 1
    return res

  '''
  def evalute_action_normal(self, env=None, action = None, job_i=None):
    a_job = self.generate_virtural_job_from_action(env = env, action = action, job_i=job_i)

    worker = env.workers_dict[a_job['scheduled_worker_code']]
    return self.evalute_normal_single_worker_n_job(env, worker, a_job)

'''



