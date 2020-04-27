# 2020-04-22 18:07:41 renamed, but did not debug with inv env.

import gym
from gym import spaces
import numpy as np
import ray
from ray.rllib.agents.ppo import PPOTrainer, DEFAULT_CONFIG
import os
import math

class KInvRLAgentAgentRLLibPPO:
    env = None
    trainer = None
    # MAX_EPOCHS = 30
    def __init__(self, env_class = None, env = None, MAX_EPOCHS=3, nbr_of_actions = 1):     
        self.env = env
        self.env_class = env_class

        self.MAX_EPOCHS = MAX_EPOCHS
        # self.trained_model = trained_model

        ray.init(ignore_reinit_error=True, log_to_driver=False)

    def _build_model(self):

        trainer_config = DEFAULT_CONFIG.copy()
        trainer_config['num_workers'] = 0
        trainer_config["train_batch_size"] = 640
        trainer_config["sgd_minibatch_size"] = 64
        trainer_config["num_sgd_iter"] = 10
        trainer = PPOTrainer(trainer_config, self.env_class)

        return trainer


    def load_model(self, model_path = None):
        if (model_path is None ) | (not os.path.exists(model_path)):
            
            raise FileNotFoundError("can not find model at path: {}".format( model_path) )
        self.trainer = self._build_model()
        self.trainer.restore(model_path)
        return self.trainer

    def train_model(self, training_data=None, model_path = None):

        self.trainer = self._build_model()
        for i in range(self.MAX_EPOCHS):
            print("Training iteration {} ...".format(i))
            self.trainer.train()

        _path = self.trainer.save(checkpoint_dir = model_path)

        self.trainer.save(model_path) 

        return _path # self.trainer


    def predict_action( self, observation = None):

        # action = adjust_action_for_sunday (action)

        shop = self.env.shops[self.env.current_shop_i]
        if  (self.env.orders[int(self.env.current_day_i / 7)] < 1):
            print("Out of orders for shop: ", shop['shop_id'])
            return  0 
        if shop['shop_id'] == 's07':
            print('S07 pause')
        shop_need = (shop['daily_sales'] * 7 * 4 ) / self.env.orders[math.floor(self.env.current_day_i / 7)]
        available_average = 1/3

        if self.env._get_current_stock_count(shop) / shop['daily_sales'] < 20:
            
            if shop_need > (1/2):
                action = 1/2
            elif  shop_need < available_average:
                action = available_average
            else:
                action = shop_need
            # action = shop_need if shop_need > available_average else available_average 
        elif self.env._get_current_stock_count(shop) / shop['daily_sales'] >70:
            action = 0
        else:
            action =  self.trainer.compute_action(observation)
            if (  observation[-2] > 5 ) & (action > 0.5):
                # Prevent this shop from taking all, while others still need
                action = 0.5
            if action > shop_need *1.5:
                action = shop_need *1.5
        return action




