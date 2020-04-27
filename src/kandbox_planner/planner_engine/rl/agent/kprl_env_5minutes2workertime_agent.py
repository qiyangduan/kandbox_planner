


import gym
import random
import numpy as np
import tensorflow as tf

# kprl_env_5minutes2workertime
import kandbox_planner.planner_engine.rl.env.kprl_env_5minutes2workertime  as ricnenv 



from tensorflow.keras.models   import   Sequential
from tensorflow.keras.layers     import Dense
from tensorflow.keras.optimizers import Adam



class KPRLDenseAgent:
    env = None
    trained_model = None
    MAX_EPOCHS = 30
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

    
    def train_model(self, training_data = None, model_path = None):
        X = np.array([i[0] for i in training_data]).reshape(-1, len(training_data[0][0]))
        y = np.array([i[1] for i in training_data]).reshape(-1, len(training_data[0][1]))
        trained_model = self._build_model(input_size=len(X[0]), output_size=len(y[0]))

        trained_model.fit(X, y, epochs=self.MAX_EPOCHS)

        trained_model.save(model_path) 
        self.trained_model = trained_model
        return trained_model


    def predict_action( self, observation = None):
        action =  self.trained_model.predict(observation.reshape(-1, len(observation)))[0]
        return action

#from pprint import pprint
        # Verify by  pprint(observation[5*ricnenv.NBR_FEATURE_PER_TECH  + 100*4 :5*ricnenv.NBR_FEATURE_PER_TECH + 115*4 ].reshape(15,4))


import random
class KPRLRandomGuessAgent:
    env = None
    trained_model = None

    action_size = 2

    def __init__(self, env = None):     
        self.env = env

    def _build_model(self, input_size, output_size):
        model = Sequential()
        return model

    def load_model(self, filename):
        self.trained_model = None

    def train_model(self, training_data):
        return {'message':'void model for random guess'}


    def predict_action( self, observation = None):
        action =  [random.uniform(0, 1),  random.uniform(90/288, 200/288)]
        return action
