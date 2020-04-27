
from django.db import models
from datetime import datetime
import time
# from sqlalchemy.orm import relationship
 
from .customized_names import job_names, worker_names, absence_names
# print('''worker_names['model']['requested_worker_code'] ''' , worker_names['model']['requested_worker_code'])
class PlannerParameter(models.Model): 
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['planner_code', 'param_name'], name='unique_parameter')
        ]
        db_table = "kpdata_planner_parameter" 

    planner_code = models.CharField(max_length=250)
    param_name =  models.CharField(max_length=250 )

    # If ==0, means this is defined by model itself and it is static/constant
    # == 1, mutable
    mutable_flag = models.IntegerField(default=0)

    param_value = models.CharField(null=True, blank=True, max_length=4000)

    def __repr__(self):
        return '{}.{}'.format(self.planner_code, self.param_name)  


class WorkerSkill(models.Model):
    skill_code = models.CharField(primary_key=True, max_length=50 )
    name = models.CharField(null=True, blank=True, max_length=50  )
    desc = models.CharField(null=True, blank=True, max_length=1000  )

    def __repr__(self):
        return self.name

class WorkerLevel(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(null=True, blank=True, max_length=50  )
    worker_skill_levels = models.ManyToManyField(WorkerSkill)
    def __repr__(self):
        return self.name

class Game(models.Model):
    # id = models.IntegerField( primary_key=True)
    game_code = models.CharField(max_length=450, primary_key=True)
    game_based_on = models.CharField(max_length=1000, null=True, blank=True) # Json list of game_code
    game_start_date = models.DateTimeField(null=True, blank=True, default=datetime.now)
    game_finish_date = models.DateTimeField(null=True, blank=True)
    planner_code = models.CharField(null=True, blank=True, max_length=250)
    # game_status = models.CharField(null=True, blank=True, max_length=250)
    game_config = models.CharField(null=True, blank=True, max_length=4000)
    data_start_day = models.CharField(null=True, blank=True, max_length=250)
    data_end_day = models.CharField(null=True, blank=True, max_length=250)
    
    game_status  = models.CharField(null=True, blank=True, max_length=1000)
    error_message  = models.CharField(null=True, blank=True, max_length=4000)
    
    game_name = models.CharField(null=True, blank=True, max_length=1000)
    game_description = models.CharField(null=True, blank=True, max_length=1000)

    def __repr__(self):
        return self.game_code

class Worker(models.Model):
    class Meta:
        verbose_name = 'Current_Tech'
        verbose_name_plural = 'Techs'
 
    # id = models.IntegerField( primary_key=True)
    worker_code = models.CharField(max_length=250, primary_key=True, verbose_name = worker_names['model']['worker_code']  )
    name = models.CharField(null=True, blank=True, max_length=1000)
    geo_longitude = models.FloatField(null=True)
    geo_latitude = models.FloatField(null=True)

    active = models.IntegerField(null=True, blank=True, default=1) 
    level = models.IntegerField(default=1, null=True, blank=True) 
    skills = models.CharField(max_length=4000, null=True, blank=True) # [1,2,'termite']
    ''' 
    # skills_1 = models.CharField(null=True, blank=True, max_length=2000) # [1,2,'termite'] 
    # Instead, wrap multiple skills into dictionary
    # All skills are Wrapped into one dictionary 2020-04-15 15:55:59
    skills = {
                'cust_type': [x['CustomerType']],
                'product':[x['Product']],
            }
    '''


    max_conflict_level = models.IntegerField(default=1,null=True, blank=True) 


    # Assume only one working time slot per day.
    weekly_working_minutes = models.CharField(null=True, blank=True, max_length=950) # [[8*60, 18*60],[120, 200],....[0, 0] for 7 days ]
    weekly_max_working_minutes = models.FloatField(blank=True, null=True)
    lunch_break_minutes = models.FloatField(blank=True, null=True)
    served_location_gmm=models.CharField(max_length=2000, null=True, blank=True) # [1,2,'termite']
    last_update_by   = models.CharField(null=True, blank=True, max_length=250) 
    last_update_game_code   = models.CharField(null=True, blank=True, max_length=250) 
    effective_from_date = models.DateField(null=True, blank=True, default=datetime.now)


    def __repr__(self):
        return self.worker_code

class WorkerStatus(models.Model):
    class Meta:
        verbose_name = 'Batch_Tech'
        verbose_name_plural = 'Tech Batches'

    # id = models.IntegerField( primary_key=True)
    worker_code = models.CharField(max_length=250, verbose_name = 'Service Area' )
    game_code = models.CharField(max_length=450)
    planner_code = models.CharField(max_length=450)
    name = models.CharField(null=True, blank=True, max_length=150)
    active = models.IntegerField(null=True, blank=True) 
    level = models.IntegerField(default=1,null=True, blank=True) 
    skills = models.CharField(max_length=4000, null=True, blank=True) # [1,2,'termite']
   
    geo_longitude = models.FloatField(null=True)
    geo_latitude = models.FloatField(null=True)
    max_conflict_level = models.IntegerField(default=1,null=True, blank=True) 



    # Assume only one working time slot per day.
    weekly_working_minutes = models.CharField(null=True, blank=True, max_length=950) # [[8*60, 18*60],[120, 200],....[0, 0] for 7 days ]
    weekly_max_working_minutes = models.FloatField(blank=True, null=True)
    lunch_break_minutes = models.FloatField(blank=True, null=True)
    # level = relationship("WorkerLevel") 

    '''
    organization = models.CharField(blank=True, max_length=200, null=True)
    org_level_1 = models.CharField(blank=True, max_length=200, null=True)
    org_level_2 = models.CharField(blank=True, max_length=200, null=True)
    org_level_3 = models.CharField(blank=True, max_length=200, null=True)
    #team_code = models.CharField(null=True, blank=True, max_length=150)
    #region_code = models.CharField(null=True, blank=True, max_length=150)

    geo_address = models.CharField(null=True, blank=True, max_length=450)
    geo_postcode = models.CharField(null=True, blank=True, max_length=250)
    geo_country_code = models.CharField(null=True, blank=True, max_length=150)
    geo_admin_1 = models.CharField(null=True, blank=True, max_length=250)
    geo_admin_2 = models.CharField(null=True, blank=True, max_length=250)

    birthday = models.DateField(blank=True, null=True)
    email = models.CharField(null=True, blank=True, max_length=250 )
    description = models.CharField(null=True, blank=True, max_length=1000)
    notes = models.CharField(null=True, blank=True, max_length=1000)
    # more in future
    '''

    
    last_update_by   = models.CharField(null=True, blank=True, max_length=250)  
    effective_from_date = models.DateField(null=True, blank=True, default=datetime.now)



class WorkerAbsence(models.Model):
    class Meta:
        verbose_name = 'Current_Event'
        verbose_name_plural = 'Events'

    absence_code = models.CharField( max_length=250, primary_key=True) 
    absence_type = models.CharField(null=True, blank=True, max_length=250)
    worker_code = models.CharField(null=True, blank=True, max_length=250, verbose_name = worker_names['model']['worker_code'])

    start_datetime = models.DateTimeField(null=True, blank=True, default=datetime.now)
    end_datetime = models.DateTimeField(null=True, blank=True, default=datetime.now)

    geo_longitude = models.FloatField(null=True, blank=True) # x
    geo_latitude = models.FloatField(null=True, blank=True) # y

    last_update_by   = models.CharField(null=True, blank=True, max_length=250) 
    last_update_game_code   = models.CharField(null=True, blank=True, max_length=250) 
    effective_from_date = models.DateField(null=True, blank=True, default=datetime.now)




class WorkerAbsenceStatus(models.Model):
    class Meta:
        verbose_name = 'Batch_Event'
        verbose_name_plural = 'Event Histories'

    game_code = models.CharField(max_length=450)
    # id = models.IntegerField(primary_key=True) 
    absence_code = models.CharField( max_length=250) 
    absence_type = models.CharField(null=True, blank=True, max_length=250)
    worker_code = models.CharField(null=True, blank=True, max_length=250, verbose_name = 'Service Area')

    start_datetime = models.DateTimeField(null=True, blank=True, default=datetime.now)
    end_datetime = models.DateTimeField(null=True, blank=True, default=datetime.now)

    geo_longitude = models.FloatField(null=True, blank=True) # x
    geo_latitude = models.FloatField(null=True, blank=True) # y

    last_update_by   = models.CharField(null=True, blank=True, max_length=250) 
    last_update_game_code   = models.CharField(null=True, blank=True, max_length=250) 
    effective_from_date = models.DateField(null=True, blank=True, default=datetime.now)


class WorkerAbsenceChanged(models.Model):
    class Meta:
        verbose_name = 'Batch_Event'
        verbose_name_plural = 'Batch Events'

    # id = models.IntegerField(primary_key=True) 
    worker_code = models.CharField(max_length=250)
    game_code = models.CharField(max_length=450)
    worker_code = models.ForeignKey(Worker,null=True, blank=True,on_delete=models.DO_NOTHING
        , related_name="absence_worker"
        , db_column='worker_code')

    start_datetime = models.DateTimeField(null=True, blank=True, default=datetime.now)
    end_datetime = models.DateTimeField(null=True, blank=True, default=datetime.now)
 
    approval_status_code = models.CharField(null=True, blank=True, max_length=250)


    last_update_by   = models.CharField(null=True, blank=True, max_length=250) 
    last_update_game_code   = models.CharField(null=True, blank=True, max_length=250) 
    effective_from_date = models.DateField(null=True, blank=True, default=datetime.now)


class Job(models.Model):
    class Meta:
        verbose_name = 'Current_Visit'
        verbose_name_plural = 'Visits'
     # id = models.IntegerField( ), No surrogate keys
    job_code = models.CharField(max_length=250, primary_key=True)
    job_type =  models.CharField(null=True, blank=True, max_length=250)
    planning_status = models.CharField(null=True, blank=True, max_length=10, verbose_name='Status')

    active = models.IntegerField(null=True, blank=True, default=1) 
    scheduled_worker_code = models.ForeignKey(Worker,null=True, blank=True,on_delete=models.DO_NOTHING
        , related_name="scheduled_worker"
        , db_column='scheduled_worker_code', verbose_name=worker_names['model']['scheduled_worker_code'])
    scheduled_related_worker_code = models.CharField(null=True, blank=True, max_length=1000)
    scheduled_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Planned Start')
    #scheduled_start_day = models.CharField(null=True, blank=True, max_length=10)  #Column( Date) # String(16) )  # _yyyymmdd
    #scheduled_start_minutes = models.FloatField(null=True, blank=True) # _hhmm
    scheduled_duration_minutes = models.FloatField(null=True, blank=True, verbose_name='Duration')
    scheduled_share_status = models.CharField(null=True, blank=True, max_length=10) # N for no-shared, P=Primary, S=Secondary

    requested_worker_code = models.ForeignKey(Worker,null=True,on_delete=models.DO_NOTHING
        , related_name="requested_worker"
        , db_column='requested_worker_code', verbose_name = worker_names['model']['requested_worker_code'])
    requested_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Requested Start')
    # requested_start_day = models.CharField(null=True, blank=True, max_length=10)  #Column( Date )  # _yyyymmdd String(16)
    # requested_start_minutes = models.FloatField(null=True, blank=True)  # _yyyymmdd
    requested_duration_minutes = models.FloatField(null=True, blank=True) 

    # primary_worker_code = models.CharField(null=True, blank=True, max_length=250) # N for no-shared, P=Primary, S=Secondary
    location_code =  models.CharField(null=True, blank=True, max_length=250)
    geo_longitude = models.FloatField(null=True, blank=True) # x
    geo_latitude = models.FloatField(null=True, blank=True) # y

    requested_min_level = models.IntegerField(null=True, blank=True)
    requested_skills = models.CharField(null=True, blank=True, max_length=4000) # [1,2,'termite'] 
    # requested_skills_1 = models.CharField(null=True, blank=True, max_length=2000) # [1,2,'termite'] 
    mandatory_day_flag = models.IntegerField(null=True, blank=True) 
    preferred_day_flag = models.IntegerField(null=True, blank=True) 

    conflict_level = models.IntegerField(default=0,null=True, blank=True) 


    mandatory_day_minmax_flag = models.IntegerField(null=True, blank=True) 
    preferred_day_minmax_flag = models.IntegerField(null=True, blank=True)   # where there is prefered day, instead of mandatory request
    requested_start_min_day = models.IntegerField(null=True, blank=True)
    requested_start_max_day = models.IntegerField(null=True, blank=True)
    
    mandatory_minutes_minmax_flag = models.IntegerField(null=True, blank=True)  
    preferred_minutes_minmax_flag = models.IntegerField(null=True, blank=True)  # where there is prefered time, instead of mandatory request
    requested_start_min_minutes = models.IntegerField(null=True, blank=True) # in the same day
    requested_start_max_minutes = models.IntegerField(null=True, blank=True) #  

    requested_week_days_flag = models.IntegerField(null=True, blank=True) 
    requested_week_days = models.CharField(null=True, blank=True, max_length=100 ) # [1,2]


    actual_worker_code = models.ForeignKey(Worker,null=True, blank=True,on_delete=models.DO_NOTHING
        , related_name="actual_worker"
        , db_column='actual_worker_code')
    actual_start_datetime = models.DateTimeField(null=True, blank=True)
    #actual_start_day = models.CharField(null=True, blank=True, max_length=10)  #Column( Date) # Column( String(16) )  # _yyyymmdd
    #actual_start_minutes = models.FloatField(null=True, blank=True)# _hhmm
    actual_duration_minutes = models.FloatField(null=True, blank=True)


    scheduled_travel_minutes_before  = models.FloatField(null=True, blank=True)
    scheduled_travel_minutes_after  = models.FloatField(null=True, blank=True)
    scheduled_travel_prev_code = models.CharField(null=True, blank=True,max_length=250) #__HOME, or job_code
    scheduled_travel_next_code = models.CharField(null=True, blank=True,max_length=250) #__HOME, or __NONE

    last_update_by   = models.CharField(null=True, blank=True, max_length=250) 
    last_update_game_code   = models.CharField(null=True, blank=True, max_length=250) 
    effective_from_date = models.DateField(null=True, blank=True, default=datetime.now)
 

    '''
    # Not useful generical attributes.

    priority = models.IntegerField(null=True, blank=True) # only in fsm_order.py
    order_name = models.CharField(null=True, blank=True, max_length=250 )
    description = models.CharField(null=True, blank=True, max_length=950)

    customer_code =  models.CharField(null=True, blank=True, max_length=250)
    account_code =  models.CharField(null=True, blank=True, max_length=250)
    contract_code =  models.CharField(null=True, blank=True, max_length=250)
    # order_code = models.CharField(null=True, blank=True, max_length=250)
    order_sequence = models.IntegerField(null=True, blank=True)

    source_system_code = models.CharField(null=True, blank=True, max_length=150) # From which system this record is loaded.
    source_ref_code = models.CharField(null=True, blank=True, max_length=250) # From which system this record is loaded.

    #region_code = models.CharField(null=True, blank=True, max_length=150)
    #team_code = models.CharField(null=True, blank=True, max_length=150)
    organization = models.CharField(max_length=200, null=True, blank=True)
    org_level_1 = models.CharField(max_length=200, null=True, blank=True)
    org_level_2 = models.CharField(max_length=200, null=True, blank=True)
    org_level_3 = models.CharField(max_length=200, null=True, blank=True)


    geo_country_code = models.CharField(null=True, blank=True, max_length=150)
    geo_admin_1 = models.CharField(null=True, blank=True, max_length=250)
    geo_admin_2 = models.CharField(null=True, blank=True, max_length=250)
    geo_address = models.CharField(null=True, blank=True, max_length=450)
    geo_postcode = models.CharField(null=True, blank=True, max_length=250)
    '''




    def __repr__(self):
        return self.job_code # 'Job: {}'.format( self.job_code)  



class JobStatus(models.Model):
    '''
    Saves job result from each batch/game.

    '''
    class Meta:
        verbose_name = 'Batch_Visit'
        verbose_name_plural = 'Visit Batches'

    # id = models.AutoField(primary_key=True)

    planner_code =  models.CharField(max_length=250, default="orig" , verbose_name='Planner')
    game_code = models.CharField(max_length=450, verbose_name='Batch')
    job_code = models.CharField(max_length=250, verbose_name='Visit')
    job_type =  models.CharField(null=True, blank=True, max_length=250, verbose_name='Type Info')
    requested_skills = models.CharField(null=True, blank=True, max_length=4000) # [1,2,'termite'] 
    planning_status = models.CharField(null=True, blank=True, max_length=10, verbose_name='Status')

    scheduled_worker_code = models.CharField(null=True, blank=True, max_length=250, verbose_name=worker_names['model']['scheduled_worker_code'])
    scheduled_related_worker_code = models.CharField(null=True, blank=True, max_length=1000, verbose_name='Secondary Tech')
    scheduled_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Planned Start')
    #scheduled_start_day = models.CharField(null=True, blank=True, max_length=10)  #Column( Date) # String(16) )  # _yyyymmdd
    #scheduled_start_minutes = models.FloatField(null=True, blank=True) # _hhmm
    scheduled_duration_minutes = models.FloatField(null=True, verbose_name='Duration')

    scheduled_travel_minutes_before  = models.FloatField(null=True, blank=True)
    scheduled_travel_minutes_after  = models.FloatField(null=True, blank=True)
    scheduled_travel_prev_code = models.CharField(null=True, blank=True,max_length=250) #__HOME, or job_code
    scheduled_travel_next_code = models.CharField(null=True, blank=True,max_length=250) #__HOME, or __NONE
    conflict_level = models.IntegerField(default=1,null=True, blank=True) 
    scheduled_share_status = models.CharField(null=True, blank=True, max_length=10) # N for no-shared, P=Primary, S=Secondary

    requested_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Requested Start')
    # requested_start_day = models.CharField(null=True, blank=True, max_length=10)  #Column( Date )  # _yyyymmdd String(16)
    # requested_start_minutes = models.FloatField(null=True, blank=True)  # _yyyymmdd
    requested_duration_minutes = models.FloatField(null=True, blank=True) 
    requested_worker_code = models.CharField(null=True, blank=True, max_length=250, verbose_name = worker_names['model']['requested_worker_code'] )

    location_code = models.CharField(null=True, blank=True, max_length=250) # x
    geo_longitude = models.FloatField(null=True, blank=True) # x
    geo_latitude = models.FloatField(null=True, blank=True) # y


    changed_flag = models.IntegerField(null=True, blank=True, default=0) 


    # primary_worker_code = models.CharField(null=True, blank=True, max_length=250) # N for no-shared, P=Primary, S=Secondary


    error_message = models.CharField(null=True, blank=True, max_length=3950) # x
    effective_from_date = models.DateField(null=True, blank=True, default=datetime.now)
    effective_to_date = models.DateField(null=True, blank=True)


    ''' 
    # Now 
    #  Specific 2020-04-15 16:00:27
    
    ''' 

class JobChangeHistory(models.Model):
    '''
    Saves job change from human being, system generation, each batch/game, input and output
    only limitted attributed to keep tracking.


    '''    
    class Meta:
        db_table = "kpdata_job_change_history" 

        verbose_name = 'Visit Change'
        verbose_name_plural = 'Changed Visits'

    job_code = models.CharField(max_length=250, verbose_name='Visit')
    #Done 2020-03-28 16:42:45 : also need job type, from N->P,S
    job_type =  models.CharField(null=True, blank=True, max_length=250, verbose_name='Type Info')

    planning_status = models.CharField(null=True, blank=True, max_length=10, verbose_name='Status')

    planner_code =  models.CharField(max_length=250, default="orig" , verbose_name='Planner')
    game_code = models.CharField(max_length=450, verbose_name='Batch')
    # requested_skills = models.CharField(null=True, blank=True, max_length=2000) # [1,2,'termite'] 

    planning_note = models.CharField(null=True, blank=True, max_length=1000)

    geo_longitude = models.FloatField(null=True) # x
    geo_latitude = models.FloatField(null=True) # y


    scheduled_worker_code = models.CharField(null=True, blank=True, max_length=250, verbose_name='Planned Tech')
    scheduled_related_worker_code = models.CharField(null=True, blank=True, max_length=1000, verbose_name='Secondary Tech')
    scheduled_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name='Planned Start')
    scheduled_duration_minutes = models.FloatField(null=True, verbose_name='Duration')
    scheduled_share_status = models.CharField(null=True, blank=True, max_length=10) # N for no-shared, P=Primary, S=Secondary

    scheduled_travel_minutes_before  = models.FloatField(null=True, blank=True)
    scheduled_travel_prev_code = models.CharField(null=True, blank=True,max_length=250) #__HOME, or job_code

    #scheduled_travel_minutes_after  = models.FloatField(null=True, blank=True)
    #scheduled_travel_next_code = models.CharField(null=True, blank=True,max_length=250) #__HOME, or __NONE


    operation = models.CharField(null=True, blank=True, max_length=10, default="U" ) # D for Delete, U - Update
    effective_from_date = models.DateTimeField(null=True, blank=True, default=datetime.now)







class PlannerStatisticalFeaturesPerDay(models.Model):
    class Meta:
        db_table = "kpdata_stats_features_per_day"
    scheduled_start_day = models.CharField(max_length=250)
    planner_code  = models.CharField(max_length=250)
    mean_on_site_service_time_ratio = models.FloatField(null=True) 
    sum_total_travel_minute = models.FloatField(null=True) 
    sum_total_service_minute = models.FloatField(null=True) 
    sum_total_on_duty_minute = models.FloatField(null=True) 
    total_job_count = models.IntegerField(null=True, blank=True)  
    total_unplanned_job_count = models.IntegerField(null=True, blank=True)  
    total_inplanning_job_count  = models.IntegerField(null=True, blank=True)  


class PlannerStatisticalFeaturesPerWorker(models.Model):
    class Meta:
        db_table = "kpdata_stats_features_per_worker"
    scheduled_worker_code = models.CharField(max_length=250)
    planner_code  = models.CharField(max_length=250)
    mean_on_site_service_time_ratio = models.FloatField(null=True) 
    sum_total_travel_minute = models.FloatField(null=True) 
    sum_total_service_minute = models.FloatField(null=True) 
    sum_total_on_duty_minute = models.FloatField(null=True) 
    total_job_count = models.IntegerField(null=True, blank=True)  
    total_unplanned_job_count = models.IntegerField(null=True, blank=True)  
    total_inplanning_job_count  = models.IntegerField(null=True, blank=True)  


class LocationJobHistoryFeatures(models.Model):
    # Location code is the only primary Key
    class Meta:
        db_table = "kpdata_location_job_history_features"

    location_code = models.CharField(max_length=250) # primary_key=True, 
    job_historical_worker_service_dict  = models.CharField(null=True, blank=True, max_length=60000)

    job_count = models.IntegerField(null=True, blank=True)  
    list_requested_worker_code  = models.CharField(null=True, blank=True, max_length=4000)
    avg_actual_start_minutes = models.FloatField(null=True) 
    avg_actual_duration_minutes = models.FloatField(null=True) 
    avg_days_delay = models.FloatField(null=True) 
    stddev_days_delay = models.IntegerField(null=True, blank=True)  



class LocationWorkerAffinityFeatures(models.Model):
    # Location code + worker_code are the primary Key
    class Meta:
        db_table = "kpdata_location_worker_affinity_features"

    location_code = models.CharField(max_length=250) # primary_key=True, 
    worker_code = models.CharField(max_length=250)

    job_count = models.IntegerField(null=True, blank=True)  
    total_duration_minutes = models.IntegerField(null=True, blank=True) 

    location_2_home_distance = models.FloatField(null=True, blank=True)  
    location_2_working_gmm_distance = models.FloatField(null=True, blank=True)  


    affinity_score = models.FloatField(null=True, blank=True)  


# https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
