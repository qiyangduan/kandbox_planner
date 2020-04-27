


import gym
import random
import numpy as np
import tensorflow as tf

# kprl_env_5minutes2workertime
import kandbox_planner.planner_engine.rl.env.kprl_env_5minutes2workertime  as ricnenv 


from tensorflow.keras.models   import   Sequential
from tensorflow.keras.layers     import Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Input



from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.layers  import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import Activation
from tensorflow.keras.layers  import Dropout 
from tensorflow.keras.layers import Flatten 
from tensorflow.keras.models import Model
from tensorflow.keras.layers import concatenate


MAX_EPOCHS = 30




def create_mlp(dim, regress=False):
	# define our MLP network
	model = Sequential()
	model.add(Dense(64, input_dim=dim, activation="relu"))
	model.add(Dense(32, activation="relu"))
	model.add(Dense(32, activation="relu"))
 
	# check to see if the regression node should be added
	if regress:
		model.add(Dense(1, activation="linear"))
 
	# return our model
	return model

def create_cnn(height, width, depth, filters=(8, 16, 32), regress=False):
	# initialize the input shape and channel dimension, assuming
	# TensorFlow/channels-last ordering
	inputShape = (height, width, depth)
	chanDim = -1
	stride_list=(1,3,6)
	# define the model input
	inputs = Input(shape=inputShape)
 
	# loop over the number of filters
	for (i, f) in enumerate(filters):
		# if this is the first CONV layer then set the input
		# appropriately
		if i == 0:
			x = inputs
 
		# CONV => RELU => BN => POOL
		x = Conv2D(f, (1, 6), strides = stride_list[i], padding="valid")(x)
		x = Activation("relu")(x)
		x = BatchNormalization(axis=chanDim)(x)
		# x = MaxPooling2D(pool_size=(2, 2))(x)
	# flatten the volume, then FC => RELU => BN => DROPOUT
	x = Flatten()(x)
	x = Dense(24)(x)
	x = Activation("relu")(x)
	x = BatchNormalization(axis=chanDim)(x)
	x = Dropout(0.5)(x)
 
	# apply another FC layer, this one to match the number of nodes
	# coming out of the MLP
	x = Dense(12)(x)
	x = Activation("relu")(x)
 
	# check to see if the regression node should be added
	if regress:
		x = Dense(1, activation="linear")(x)
 
	# construct the CNN
	model = Model(inputs, x)
 
	# return the CNN
	return model



class KPRLCNNDenseAgent: 
    env = None
    trained_model = None
    MAX_EPOCHS = 30
    def __init__(self, env = None,trained_model=None, MAX_EPOCHS=30, nbr_of_actions = 1):     
        self.env = env
        self.MAX_EPOCHS = MAX_EPOCHS
        self.trained_model = trained_model

    def _build_model(self):


        # create the MLP and CNN models
        mlp = create_mlp(ricnenv.NBR_FEATURE_CUR_JOB_n_OVERALL, regress=False)
        # ricnenv.MAX_NBR_WORKERS,  ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2), ricnenv.NBR_FEATURE_PER_WORK_TIME_UNIT
        cnn = create_cnn(6, 290, 4, regress=False)
        combinedInput = concatenate([mlp.output, cnn.output])


        # our final FC layer head will have two dense layers, the final one
        # being our regression head
        x = Dense(64, activation="relu")(combinedInput)
        x = Dense(16, activation="linear")(x)
        x = Dense(8, activation="linear")(x)
        x = Dense(2, activation="linear")(x) 
        # our final model will accept categorical/numerical data on the MLP
        # input and images on the CNN input, outputting a single value (the
        # predicted price of the house)
        model = Model(inputs=[mlp.input, cnn.input], outputs=x)

        opt = Adam(lr=1e-3, decay=1e-3 / 200)
        model.compile(loss="mean_absolute_percentage_error", optimizer=opt)

        print(model.summary())
        return model

    def load_model(self, filename):
        self.trained_model = tf.keras.models.load_model(filename)
    def train_model(self, training_data=None, model_path = None):
        #X = np.array([i[0] for i in training_data]).reshape(-1, len(training_data[0][0]))
        #y = np.array([i[1] for i in training_data]).reshape(-1, len(training_data[0][1]))

        obs_graph = np.zeros([len(training_data), ricnenv.MAX_NBR_WORKERS * ricnenv.NBR_FEATURE_PER_WORK_TIME_UNIT * ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) ])
        for step_i in range(len(training_data)):
            for w_i in range(ricnenv.MAX_NBR_WORKERS):
                obs_graph[step_i, w_i*4* ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) : (w_i+1)*4* ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) ] = training_data[step_i][0][ w_i*ricnenv.NBR_FEATURE_PER_TECH: w_i*ricnenv.NBR_FEATURE_PER_TECH + (4* ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) )]

        obs_3d = obs_graph.reshape(len(training_data), ricnenv.MAX_NBR_WORKERS,  ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2), ricnenv.NBR_FEATURE_PER_WORK_TIME_UNIT  )


        obs_CUR_JOB_n_OVERALL = np.zeros( [len(training_data), ricnenv.NBR_FEATURE_CUR_JOB_n_OVERALL])  
        job_feature_start_index = 6 *ricnenv. NBR_FEATURE_PER_TECH + ricnenv.NBR_FEATURE_WORKERS
        for step_i in range(len(training_data)):
            obs_CUR_JOB_n_OVERALL[step_i, :] = training_data[step_i][0][ job_feature_start_index:job_feature_start_index + ricnenv.NBR_FEATURE_CUR_JOB_n_OVERALL]


        all_actions = np.zeros([  len(training_data), training_data[0][1].shape[0]    ])
        for step_i in range(len(training_data)):
            all_actions[step_i, :] = training_data[step_i][1]



        new_model = self._build_model()
        print("[INFO] training CNN + Dense model...")
        new_model.fit( [obs_CUR_JOB_n_OVERALL, obs_3d ], all_actions, 
            epochs=self.MAX_EPOCHS )


        self.trained_model = new_model
        self.trained_model.save(model_path) 
        return new_model


    def predict_action( self, observation = None):
        # action =  self.trained_model.predict(observation.reshape(-1, len(observation)))[0]


        obs_graph = np.zeros([1, ricnenv.MAX_NBR_WORKERS * ricnenv.NBR_FEATURE_PER_WORK_TIME_UNIT * ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) ])

        for w_i in range(ricnenv.MAX_NBR_WORKERS):
            obs_graph[0, w_i*4* ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) : (w_i+1)*4* ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) ] = observation[ w_i*ricnenv.NBR_FEATURE_PER_TECH: w_i*ricnenv.NBR_FEATURE_PER_TECH + (4* ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2) )]

        obs_3d = obs_graph.reshape(1, ricnenv.MAX_NBR_WORKERS,  ( ricnenv.NBR_WORK_TIME_UNIT_PER_TECH + 2), ricnenv.NBR_FEATURE_PER_WORK_TIME_UNIT  )


        obs_CUR_JOB_n_OVERALL = np.zeros( [1, ricnenv.NBR_FEATURE_CUR_JOB_n_OVERALL])  
        job_feature_start_index = 6 *ricnenv. NBR_FEATURE_PER_TECH + ricnenv.NBR_FEATURE_WORKERS
        obs_CUR_JOB_n_OVERALL[0,:] = observation[ job_feature_start_index:job_feature_start_index + ricnenv.NBR_FEATURE_CUR_JOB_n_OVERALL]



        action =  self.trained_model.predict( [obs_CUR_JOB_n_OVERALL, obs_3d ] )[0]
        return action

 