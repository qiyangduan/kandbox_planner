from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin


from .models import Worker, Job, JobStatus, JobChangeHistory, Game, WorkerAbsence
from .models import  RLPlannerParameter, WorkerLevel, WorkerSkill
from datetime import datetime, timedelta
from kandbox_planner import config

from .customized_names import job_names, worker_names, absence_names


#from django.conf import settings

#print('duan debug:', settings.AUTH_USER_MODEL)


# admin.site.register(Worker)
# admin.site.register(Job)

#admin.site.register(WorkerLevel)
#admin.site.register(WorkerSkill)
admin.site.register(RLPlannerParameter)


import kandbox_planner.util.planner_date_util  as date_util

from kandbox_planner.util.google_calendar  import GoogleCalendarChannelAdapter
google_calendar = GoogleCalendarChannelAdapter()


from kandbox_planner.planner_engine.opti1day.opti1day_planner  import Opti1DayPlanner
opti = Opti1DayPlanner( max_exec_time = 3) 

from kandbox_planner.planner_engine.feature_calc import KPlannerFeatureCalculator
 
kfc = KPlannerFeatureCalculator()
from django.db import transaction






class WorkerResource(resources.ModelResource):
    class Meta:
        model = Worker
        #instance_loader_class = MyCustomInstanceLoaderClass
        import_id_fields = ('worker_code',)

@admin.register(Worker)
class WorkerAdmin( ImportExportActionModelAdmin ): 
    resource_class = WorkerResource

    search_fields = ['worker_code',  'EmployeeCode'  ] # 'name', 'geo_address',
    list_filter =  worker_names['list_filter']
    save_as = True
    
    list_display = worker_names['list_display']
        
    list_per_page = 20


class GameChart(Game):
    class Meta:
        proxy = True
        verbose_name = 'Visit_Chart'
        verbose_name_plural = 'Visit Chart'


@admin.register(GameChart)
class GameChartAdmin(admin.ModelAdmin):
    search_fields = ['game_code', 'game_name', 'planner_code', 'data_start_day', 'data_end_day']
    list_filter = ('planner_code', )
    list_display = [ 'game_code',]    
    # A template for a very customized change view:
    change_form_template = 'pages/game_chart_change_form.html'
    # change_list_template = 'pages/game_chart_change_list.html'
    change_list_template = 'migrated/real_time_planner.html' 
    # actions_template = 'pages/game_chart_actions.html'


class VueGameChart(Game):
    class Meta:
        proxy = True
        verbose_name = 'Vue_Chart'
        verbose_name_plural = 'Vue Visit Chart'


@admin.register(VueGameChart)
class VueGameChartAdmin(admin.ModelAdmin):
    
    list_filter = ('planner_code', 'game_code', 'game_start_date')  

    # A template for a very customized change view:
    
    change_list_template = 'pages/vue_chart_change_list.html'
    
    search_form_template = 'pages/vue_chart_search_form.html'

    # actions_template = 'pages/vue_chart_actions.html'
    # https://books.agiliq.com/projects/django-admin-cookbook/en/latest/remove_add_delete.html
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    '''
    def get_actions(self, request):
        actions = super().get_actions(request)
        print(actions)
        if request.user.username[0].upper() != 'J':
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions
    '''

@admin.register(JobChangeHistory)
class NewJobChangeHistoryAdmin(admin.ModelAdmin):
    search_fields = ['job_code', "scheduled_worker_code", 'game_code']
    list_filter = ('game_code','scheduled_start_datetime', 'operation')
    save_as = True
    #  "planning_note",
    list_display = ["job_code", 'operation', "planning_status", 
        "scheduled_worker_code",  "scheduled_start_datetime",   "scheduled_duration_minutes" , 
        "planner_code", "game_code", "effective_from_date",
        ]

    readonly_fields = ["job_code", "planning_status", "planner_code", "game_code", 'operation', 
        "scheduled_worker_code",  "scheduled_start_datetime",   "scheduled_duration_minutes" , 'geo_longitude', 'geo_latitude', 
        ]



#class MyCustomInstanceLoaderClass(BaseInstanceLoader):
#    def get_instance(self, row):


class WorkerAbsenceResource(resources.ModelResource):
    class Meta:
        model = WorkerAbsence
        #instance_loader_class = MyCustomInstanceLoaderClass
        import_id_fields = ('absence_code',)

@admin.register(WorkerAbsence)
# class WorkerAbsenceAdmin(admin.ModelAdmin): ImportExportActionModelAdmin
class WorkerAbsenceAdmin(ImportExportActionModelAdmin): 
    resource_class = WorkerAbsenceResource

    list_display =  absence_names['list_display']  
         
      
    
    readonly_fields = ['last_update_by',  'last_update_game_code',  'effective_from_date']

    search_fields = ['worker_code', 'start_datetime']
    list_filter = ('worker_code', )
    save_as = True


@admin.register(JobStatus)
class JobStatusAdmin(admin.ModelAdmin):
    '''
    search_fields = ['job_code', 'error_message'] # ,   "scheduled_worker_code"


    list_filter = ('planner_code','game_code', 'Country', 'Branch', "scheduled_worker_code",'scheduled_start_datetime',  "requested_worker_code",'requested_start_datetime', 
        'planning_status','scheduled_share_status','VisitTypeCode','ServiceType','AppointmentRequiredInd','NoShareVisitInd','CustomerType','NationalKeyAccountInd','RetainTechInd',)

    list_display = ['Contract','Premise','Product',  "planning_status", "game_code",
        "scheduled_worker_code",  "scheduled_start_datetime",   "scheduled_duration_minutes" , "error_message"
        , 'scheduled_share_status' # , 'scheduled_related_worker_code'
        ,'ServiceCoverNumber','PlanVisitNumber'
        ,'Freq','VisitTypeCode','ServiceType','AppointmentRequiredInd','NoShareVisitInd','MinVisitGapDays','VisitTolerance'
        ,'LastVisitDateTime','CustAvailability','CustomerType','NationalKeyAccountInd','RetainTechInd'
        , 'geo_longitude', 'geo_latitude'
        , "job_code",   "game_code" ,'Country', 'Branch'
        ]

    readonly_fields = ["job_code", "planning_status", "planner_code", "game_code", 'Contract','Premise','Product', 
        "scheduled_worker_code",  "scheduled_start_datetime",   "scheduled_duration_minutes" , 'geo_longitude', 'geo_latitude', 
         "error_message"
         ]
    '''
    list_display = ["game_code"] + job_names['list_display'] # [ 'job_code', 'job_type' , 'planning_status' ,'scheduled_worker_code','scheduled_start_datetime',  'scheduled_duration_minutes', 'scheduled_share_status'  , 'geo_longitude', 'geo_latitude' ]
    search_fields = ["game_code"] +  ['job_code', 'job_code' ,'scheduled_worker_code']  
    list_filter = ['planner_code',"game_code"] + job_names['list_filter'] 
    readonly_fields =  job_names[ 'readonly_fields']

    list_per_page = 30




class JobResource(resources.ModelResource):
    class Meta:
        model = Job
        #instance_loader_class = MyCustomInstanceLoaderClass
        import_id_fields = ('job_code',)
    def before_import_row(self, row, **kwargs):
        print('before_import_row', row['job_code'], row)
        row['last_update_by'] = 'imported'
    def before_import(self, dataset,using_transactions,  dry_run, **kwargs):
        df = dataset.export('df')
        print(df)

@admin.register(Job)
class NewJobAdmin(ImportExportActionModelAdmin):
    # import_id_fields = ('job_code',)
    resource_class = JobResource
    
    list_per_page = 20
    list_display = job_names['list_display'] # [ 'job_code', 'job_type' , 'planning_status' ,'scheduled_worker_code','scheduled_start_datetime',  'scheduled_duration_minutes', 'scheduled_share_status'  , 'geo_longitude', 'geo_latitude' ]
    search_fields = ['job_code']  
    list_filter = job_names['list_filter'] 
    readonly_fields =  job_names[ 'readonly_fields']


    save_as = True

    def save_model(self, request, obj, form, change):
        user = request.user 
        instance = form.save(commit=True)
        obj.last_update_by='web_save'
        obj.save()

        if config.RL_PLANNER_AUTOMATIC:    # new object
            # instance.status = 
            if obj.planning_status == 'U':
                print('Running RL_PLANNER_AUTOMATIC on job: ', obj.job_code)
                transaction.on_commit(lambda: schedule_jobs_rl_heur(last_update_by_tag = 'web_save'))
            else:
                print('RL_PLANNER_AUTOMATIC triggered, but not in status U, skipped')

        if config.SEND_GOOGLE_CALENDAR:             # updated old object
            # instance.status = 
            print("I am sending calendar update.")
            print('changed', form.cleaned_data.get('scheduled_start_datetime'))
            # instance.save()
            # form.save_m2m()
            # obj.save(commit=True)
            #with transaction.atomic():
                # This code executes inside a transaction.

            # transaction.commit()
                # rr = super(NewJobAdmin, self).save_model(request, obj, form, change)
            scheduled_start_datetime = form.cleaned_data.get('scheduled_start_datetime')
            requested_start_day = datetime.strftime(scheduled_start_datetime, config.KANDBOX_DATE_FORMAT)
            # requested_start_minutes = form.cleaned_data.get('requested_start_minutes')
            
            start_d = scheduled_start_datetime # date_util.day_minutes_to_datetime(k_day=requested_start_day, minutes=requested_start_minutes)
            end_d = scheduled_start_datetime + timedelta(  minutes= int(form.cleaned_data.get('requested_duration_minutes')) )

            event = { 
                'summary': 'Pest: {}'.format(form.cleaned_data.get('job_code')),
                'location': 'The Arches, Villiers St, Charing Cross, London WC2N 6NG',
                'description': """Kill rats. \n <a href="http://localhost:8000/admin/kpdata/job/{}/change/" class="menu-link" target="_blank">Job Details</a>, to  \n Other details, """.format(form.cleaned_data.get('job_code')),
                'start': {
                    'dateTime': date_util.datetime_to_google_calendar_date_str(k_date=start_d),
                    'timeZone': 'Europe/London',
                },
                'end': {
                    'dateTime': date_util.datetime_to_google_calendar_date_str(k_date=end_d),
                    'timeZone': 'Europe/London',
                }, 
                'attendees': [
                    {'email': 'duan@example.com'},
                    {'email': 'qiyang@inc.com'},
                ], 
                'extendedProperties': {'private': 
                    {'planner': 'rhythm', 
                     'job_code': form.cleaned_data.get('job_code')
                    }},
            }
            
            transaction.on_commit(lambda: schedule_new_day(requested_start_day = requested_start_day, calendar_event = event))

def schedule_new_day(requested_start_day = None, calendar_event = None):
    
    end_date = date_util.add_days_2_day_string(k_day=requested_start_day, days = 1)
    res = opti.dispatch_jobs( start_date = requested_start_day, end_date =  end_date )
    kfc.add_travel_time_to_orig_job_status(planner_code = 'orig',start_day=requested_start_day, end_day=end_date)
    print(calendar_event)
    google_calendar.send(event=calendar_event)
    #return None



from kandbox_planner.planner_engine.rl.all_rl_planners import  get_rl_planner, exec_rl_planner

current_day_str = datetime.strftime(datetime.now(), config.KANDBOX_DATE_FORMAT)
rl_heur_env_config = {
    'run_mode' : 'replay',
    'data_start_day':current_day_str,
    # 'data_end_day':'20200319',
    'nbr_of_observed_workers':6,
    'nbr_of_days_planning_window':2, 

}
current_rl_heur_planner=None
if config.RL_PLANNER_AUTOMATIC:
  current_rl_heur_planner = get_rl_planner(planner_code = 'rl_heur', env_config=rl_heur_env_config, replay=True, predict_unplanned=False)
# ================================================================================
import pandas as pd

def schedule_jobs_rl_heur(last_update_by_tag = None):
    if last_update_by_tag is None:
        last_update_by_tag = 'imported'
    imported_jobs = Job.objects.filter(last_update_by=last_update_by_tag).values()
    # if imported_jobs_df.count().max() < 1:
    if len(imported_jobs) < 1:
        print('rl_heur no data:')
        return
    imported_jobs_df = pd.DataFrame(imported_jobs)
    print(imported_jobs_df.columns)
    

    kplanner_db = current_rl_heur_planner['planner_env'].config['kplanner_db']

    imported_jobs_df['requested_worker_code'] = imported_jobs_df['requested_worker_code_id']
    imported_jobs_df['scheduled_worker_code'] = imported_jobs_df['requested_worker_code_id']
    imported_jobs_df['actual_worker_code'] = imported_jobs_df['requested_worker_code_id']


    imported_jobs_df['actual_start_datetime'] = imported_jobs_df['requested_start_datetime']
    imported_jobs_df['scheduled_start_datetime'] = imported_jobs_df['requested_start_datetime']
    imported_jobs_df = kplanner_db.convert_df_datetime_to_day_minutes(imported_jobs_df)
    new_jobs = kplanner_db._transform_jobs(jobs = imported_jobs_df, start_date = datetime.now())
    
    #
    for new_job in new_jobs:
        # if new_job['job_code'] not in self.jobs_dict.keys():
        current_rl_heur_planner['planner_env'].add_job(new_job)

    exec_rl_planner(current_rl_heur_planner)

    print('rl_heur dispatched.')

# for testing without importing every time.
# schedule_jobs_rl_heur()

def schedule_jobs_opti1day():

    new_job_days = Job.objects.filter(~Q(last_update_by='opti1day' ) ).values('requested_start_datetime').distinct()
    new_job_days_set = set()
    for job_day in new_job_days:
        new_job_days_set.add(datetime.strftime(job_day['requested_start_datetime'],config.KANDBOX_DATE_FORMAT))
        print(job_day)
    print('all days to dispatch:',new_job_days_set)
    for requested_start_day in new_job_days_set:
        end_date = date_util.add_days_2_day_string(k_day=requested_start_day, days = 1)
        res = opti.dispatch_jobs( start_date = requested_start_day, end_date =  end_date )
        # kfc.add_travel_time_to_orig_job_status(planner_code = 'orig',start_day=requested_start_day, end_day=end_date)
        print('dispatched:',requested_start_day)



from django.dispatch import receiver
from import_export.signals import post_import, post_export
from django.db.models import Q
# https://django-import-export.readthedocs.io/en/latest/getting_started.html
@receiver(post_import, dispatch_uid=None)
def _post_import(model, **kwargs):
    # model is the actual model instance which after import
    # print(model.__name__)
    if model.__name__ == 'Job':
        
        if config.OPTI1DAY_AUTOMATIC:
            schedule_jobs_opti1day()
        if config.RL_PLANNER_AUTOMATIC:
            schedule_jobs_rl_heur()


    pass