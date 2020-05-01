



from kandbox_planner.planner_engine.rl.env.reward import  RewardFunction
import kandbox_planner.util.planner_date_util  as date_util


class NoConflictionReward(RewardFunction):
  """
    Has the following members 
  """
  rule_code = "job_donot_conflict_other_jobs"
  rule_name = "Job is not blocked by other jobs"

  def evalute_normal_single_worker(self,  env, worker = None, job = None):
    # return score, violated_rules (negative values)
    # return self.weight * 1
    for working_time_i in range(len(worker['assigned_jobs'])):
      

      existing_job = env.jobs[worker['assigned_jobs'][working_time_i]['job_index']] 
      working_slot = [existing_job['assigned_start_minutes'], existing_job['assigned_start_minutes'] + existing_job['scheduled_duration_minutes']]
      cliped_slot = date_util.clip_time_period(
        p1=working_slot, 
        p2=[job['assigned_start_minutes'], job['assigned_start_minutes'] + job['scheduled_duration_minutes']]
        )
      if len(cliped_slot) > 1:
        return -1
      else:
        continue
    return 1
  '''
  def evalute_action_normal(self, env=None, action = None):
    a_job = self.generate_virtural_job_from_action(env, action)


    worker = env.workers_dict[a_job['scheduled_worker_code']]
    return self.evalute_normal_single_worker(env, worker, a_job)
  '''
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