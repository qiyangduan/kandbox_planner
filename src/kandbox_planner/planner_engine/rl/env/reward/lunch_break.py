



# from kandbox_planner.planner_engine.rl.env.kprl_reward_function import  kprl_rule_set
 
from kandbox_planner.planner_engine.rl.env.reward.reward_function import  RewardFunction
import kandbox_planner.util.planner_date_util  as date_util



class LunchHourBreakReward(RewardFunction):
  """
    Has the following members 
  """
  rule_code = "lunch_hour_break"
  rule_name = "30 minutes between 12:00-14:00"

  # def evalute_action_normal(self, env=None, action_dict = None):
  def evalute_normal_single_worker_n_job(self,  env = None,  job = None): # worker = None,
    # action_dict = env.decode_action_into_dict(action)
    # if (action_dict['scheduled_start_minutes'] > 14*60 ) | (action_dict['scheduled_start_minutes'] + action_dict['scheduled_duration_minutes']< 12*60  ):
    overlap_lunch = date_util.clip_time_period([ 12*60 ,  14*60 ], [job['scheduled_start_minutes'], job['scheduled_start_minutes'] + job['scheduled_duration_minutes']])
    if len(overlap_lunch) < 1:
      return {
        'score': 1,
        'message':['The Job is not at lunch time'],
        }


    worker_code = job['scheduled_worker_code']
    scheduled_start_minutes = job['scheduled_start_minutes']
    job_start_time =  job['assigned_start_minutes']
  
    prev_job = None
    next_job = None

    new_job_loc_i=0
    total_lunch_break = 2*60
    for job_i in range(len(env.workers_dict[worker_code]['assigned_jobs'])):
      a_job = env.jobs[
          env.workers_dict[worker_code]['assigned_jobs'][job_i]['job_index']
        ]
      a_job_period = [a_job['assigned_start_minutes'], a_job['assigned_start_minutes'] + a_job['scheduled_duration_minutes']  ]
      a_job_period_lunch = date_util.clip_time_period([ 12*60 ,  14*60 ], a_job_period)
      if len(a_job_period_lunch) > 1:
        total_lunch_break -= a_job_period_lunch[1] - a_job_period_lunch[0]

    if total_lunch_break < 30:
      return {
        'score': -1,
        'message':['total_lunch_break < 30'],
        }
    else:
      return {
        'score': 1,
        'message':['total_lunch_break >=30'],
        }