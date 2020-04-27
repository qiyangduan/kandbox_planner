
from kandbox_planner.planner_engine.rl.env.reward.reward_function import  RewardFunction
import kandbox_planner.util.planner_date_util  as date_util


class WithinWorkingHourReward(RewardFunction):
  """
    Has the following members 
  """
  rule_code = "within_working_hour"
  rule_name = "Job is between start and end time of the worker"
  message_template = "Job time ({}-{}) is out of working hour"

  def evalute_normal_single_worker_n_job(self, env=None, job = None): # worker = None, 
    worker = env.workers_dict[job['scheduled_worker_code']]
    result = {
      'score': 0,
      'message':[self.rule_name],
    }

    # return score, violated_rules (negative values)
    # return self.weight * 1
    for day_i, working_slot in enumerate(worker['working_minutes']):
      working_slot_with_day = [
        working_slot[0] + (24*60*day_i),
        working_slot[1] + (24*60*day_i),
      ]
      cliped_slot = date_util.clip_time_period(
        p1=working_slot_with_day, 
        p2=[job['assigned_start_minutes'], job['assigned_start_minutes'] + job['scheduled_duration_minutes']]
        )
      if len(cliped_slot) > 1:
        if ( cliped_slot[0] == job['assigned_start_minutes'] ) & ( cliped_slot[1] == job['assigned_start_minutes'] + job['scheduled_duration_minutes']):
          result['score'] = 1
          return result 
        # Partial fit, reject for now #TODO
        result['score'] = -1
        result['message'] = self.message_template.format(job['assigned_start_minutes'], job['assigned_start_minutes'] + job['scheduled_duration_minutes'])
        return result 
 
      else:
        continue
    # If the start time does not fall in working hour, reject it.
    result['score'] = -1
    result['message'] = self.message_template.format(job['assigned_start_minutes'], job['assigned_start_minutes'] + job['scheduled_duration_minutes'])
    return result 

  '''
  def evalute_action_normal(self, env=None, action = None):
    a_job = self.generate_virtural_job_from_action(env, action)

    worker = env.workers_dict[a_job['scheduled_worker_code']]
    return self.evalute_normal_single_worker(env, worker, a_job)

  def evalute_normal(self, env=None, job_index_list = []):
    # return score, violated_rules (negative values)
    # return self.weight * 1
    if len(job_index_list) < 1:
      return -1
      job_index_list = []#TODO
    
    for job_i  in job_index_list:
      cur_job =  env.jobs[job_i] 
      if len(cur_job['assigned_workers'] ) < 1:
        # Job not assigned
        return -1
      
      found_partial_slot = False
      no_slot_found = False

      for assignment in cur_job['assigned_workers']:
        if self.evalute_normal_single_worker(env, env.workers_dict[assignment['worker_code']], cur_job ) == -1:
          return -1
      return 1
          '''

