import os

basedir = os.path.abspath(os.path.dirname(__file__))

OSS_LOCAL_STORAGE_PATH = os.getenv('KPLANNER',basedir)

# Get the value of 
# 'HOME' environment variable  
DATABASE_URI = os.environ['DATABASE_URL'] 
from datetime import datetime  


# Print the value of 
# 'HOME' environment variable 
# print("Database :", DATABASE_URI) 

KANDBOX_MAXINT = 2147483647
KANDBOX_DATE_FORMAT= "%Y%m%d"

# CURRENT_DATE = '01/09/19'
KANDBOX_DATE_FORMAT= "%Y%m%d"
SYSTEM_DATE_FORMAT = "%Y-%m-%d" 
# datetime.strptime('2019-07-01',"%Y-%m-%d")
ORIG_SYS_DATE_FORMAT = '%m/%d/%Y'

KANDBOX_DATETIME_FORMAT_WITH_MS="%Y-%m-%d %H:%M:%S.%f" # For postgres as well
KANDBOX_DATETIME_FORMAT_ISO="%Y-%m-%dT%H:%M:%S"

# FOR MODEL
NBR_DAYS_PER_TECH = 7 # 1, NUMBER of days for training the model, and observe
MAX_TIMESLOT_PER_DAY =  2
NBR_FEATURE_PER_TIMESLOT = 4
MAX_WORKING_TIME_DURATION = 60*12


KANDBOX_JOB_MINIMUM_START_DAY = '20200422'  # datetime.strftime(datetime.now(), KANDBOX_DATE_FORMAT) #'20200415' 

# For london
# KANDBOX_TEST_START_DAY = '20200303' 
#For The_Company
KANDBOX_TEST_START_DAY = '20200428'  # s KANDBOX_JOB_MINIMUM_START_DAY # '20200402' 


KANDBOX_TEST_END_DAY  =  '20200511'
KANDBOX_TEST_OPTI1DAY_START_DAY  =  KANDBOX_JOB_MINIMUM_START_DAY # '20200503'
KANDBOX_TEST_OPTI1DAY_END_DAY  =  '20200507'

KANDBOX_OPTI1DAY_EXEC_SECONDS  =  5
KANDBOX_TEST_WORKING_DIR = '/tmp'
RL_MAX_EPOCHS = 5
RL_TRAINING_DAYS = 8


OPTI1DAY_AUTOMATIC = False
RL_PLANNER_AUTOMATIC = False


SEND_GOOGLE_CALENDAR = False
google_calendar_token_path = '/tmp/The_Companys/a.token.pickle'


