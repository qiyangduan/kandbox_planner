



# from kandbox_planner.planner_engine.rl.env.kprl_reward_function import  kprl_rule_set
 
from kandbox_planner.planner_engine.rl.env.reward.reward_function import  RewardFunction
import kandbox_planner.util.planner_date_util  as date_util

class SkillCheckReward(RewardFunction):
  """
    Has the following members 
  """
  rule_code = "check_job_skill"
  rule_name = "Worker can handle skills requested by job"
  error_message_template = "Job ({}) requires skill ({}) , which worker {} does not have."
  success_message_template = "Job ({}) requires skill ({}) , which worker {} has."
  '''
  result = {
    'score': 0,
    'message':'', 
  }
  '''
  def evalute_normal_single_worker_n_job(self,  env, job = None): # worker = None, 
    # return score, violated_rules (negative values)
    # return self.weight * 1 
    # Now check if this new job can fit into existing 
    worker_code = job['scheduled_worker_code']
    worker = env.workers_dict[worker_code]
    res={}
    overall_message = "Job ({}) requires skill ({}), checking workers {}".format(job['job_code'], job['requested_skills'], worker_code)
    score = 1
    for skill_key in job['requested_skills'].keys():

      # if(not all(skill in job['requested_skills'][skill_key] for skill in worker['skills'][skill_key])):
      for skill in job['requested_skills'][skill_key]:
        if not skill in worker['skills'][skill_key]:
          overall_message += "(skill_key={}, skill={}) is not found!".format(skill_key,skill )
          score = -1
          break
      overall_message += "(skill_key={}) found!".format(skill_key )
      
    res['message'] = overall_message
    res['score'] = score
    return res







