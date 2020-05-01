
import kandbox_planner.util.planner_date_util  as date_util

import numpy as np

from kandbox_planner.planner_engine.rl.env.reward.reward_function import  RewardFunction



from kandbox_planner.planner_engine.rl.env.reward.lunch_break import  LunchHourBreakReward
# class SufficientTravelTimeReward(RewardFunction):
from kandbox_planner.planner_engine.rl.env.reward.travel_time import  SufficientTravelTimeReward
from kandbox_planner.planner_engine.rl.env.reward.working_hour import  WithinWorkingHourReward

from kandbox_planner.planner_engine.rl.env.reward.skill import  SkillCheckReward

# no_conflict_ = NoConflictionReward(weight=0.5)

class KPlannerEnvWithHistoryReward:
  """
    Has the following members 
  """
  reward_function_rule_list = [ ] 

  action_rule_list = []

  within_working_hour = WithinWorkingHourReward(weight=0.5)
  lunch_break = LunchHourBreakReward(weight=0.5)

  sufficient_travel_reward = SufficientTravelTimeReward(weight=0.5)

  skill_check = SkillCheckReward(weight=1)

  result = {
    'score': 0,
    'messages':[], 
  }

  def __init__(self):     
    
    self.action_rule_list = [
        self.within_working_hour,
        self.lunch_break,
        # no_conflict,

        self.sufficient_travel_reward,
        self.skill_check,
      ]

    self.django_action_rule_list = [
        self.within_working_hour,
        self.sufficient_travel_reward
        # no_conflict,
      ]

    self.reward_function_rule_list = [
        #no_conflict,
        self.within_working_hour,
        self.lunch_break,
    ]
    pass

  def evalute(self, env=None, job_index_list = []):
    # return score, violated_rules (negative values)
    for rf in reward_function_rule_list:
      res =  rf.evalute(env, job_index_list)  
    sum_score = sum([])
    return 


kprl_rule_set = KPlannerEnvWithHistoryReward()

if __name__ == '__main__': 

    pass
    #kfc.purge_travel_time_statistics(planner_code = 'orig')
    