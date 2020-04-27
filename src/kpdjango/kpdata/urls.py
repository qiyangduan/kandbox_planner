from django.conf.urls import url, include 
from .models import Worker, Job, Game, WorkerAbsence
# from .models import planner_timeline_datatable_view

from .api_views import  worker_job_dataset_json, PlannerStatsPerDayJSONView   # EchartsTimelineJSONView,  JobsTimelineFilterJSONView ,


from rest_framework import routers, serializers, viewsets
from django.urls import path

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import authentication, permissions



class GameSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Game
        fields = ['game_code', 'game_name', 'data_start_day', 'data_end_day', 'planner_code']


#@api_view(['GET', 'POST'])
@authentication_classes([authentication.SessionAuthentication, authentication.TokenAuthentication]) # BasicAuthentication
@permission_classes([permissions.IsAuthenticated]) 
class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all().order_by('-game_code')
    serializer_class = GameSerializer

# Serializers define the API representation.
class WorkerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Worker
        fields = ['worker_code', 'level', 'skills','name', 'geo_longitude', 'geo_latitude','weekly_working_minutes' ]

# ViewSets define the view behavior.
@authentication_classes([authentication.SessionAuthentication, authentication.TokenAuthentication]) # BasicAuthentication
@permission_classes([permissions.IsAuthenticated]) 
class WorkerViewSet(viewsets.ModelViewSet):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer


class JobSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Job
        # 'requested_start_minutes',  'scheduled_start_minutes', 

        fields = ['job_code', 'job_type','requested_min_level', 'requested_skills', 
            'requested_duration_minutes','location_code',
            'requested_start_datetime', 'requested_worker_code',
            'scheduled_start_datetime', 'scheduled_worker_code',
            'geo_longitude', 'geo_latitude', 'planning_status' ]

# ViewSets define the view behavior.
@authentication_classes([authentication.SessionAuthentication, authentication.TokenAuthentication]) # BasicAuthentication
@permission_classes([permissions.IsAuthenticated]) 
class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer


class WorkerAbsenceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WorkerAbsence
        # 'requested_start_minutes',  'scheduled_start_minutes', 

        fields = ['absence_code',  'absence_type', 'worker_code', 'start_datetime', 'end_datetime' ,'geo_longitude', 'geo_latitude', ]

# ViewSets define the view behavior.
@authentication_classes([authentication.SessionAuthentication, authentication.TokenAuthentication]) # BasicAuthentication
@permission_classes([permissions.IsAuthenticated]) 
class WorkerAbsenceViewSet(viewsets.ModelViewSet):
    queryset = WorkerAbsence.objects.all()
    serializer_class = WorkerAbsenceSerializer


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'workers', WorkerViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'games', GameViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

from django.views.decorators.csrf import csrf_exempt
from .api_views import  SingleJobDropCheckJSONView   ,GetSlotsSingleJobJSONView , GymEnvStepJSONView, CommitRLChangesJSONView # EchartsTimelineJSONView, 



urlpatterns = [
    url(r'^', include(router.urls)),
    # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # path(r'worker_job_echarts.json', EchartsTimelineJSONView.as_view()),
    # path(r'worker_job_filtered.json', JobsTimelineFilterJSONView.as_view()),
    # path(r'worker_job_dataset.json', JobsTimelineDatasetView.as_view()),
    path('worker_job_dataset.json', (worker_job_dataset_json)), # csrf_exempt


    path(r'step.json', GymEnvStepJSONView.as_view()),
    path(r'commit_rl_changes.json', CommitRLChangesJSONView.as_view()),

    path(r'single_job_drop_check.json', SingleJobDropCheckJSONView.as_view()),
    path(r'get_slots_single_job.json', GetSlotsSingleJobJSONView.as_view()),
    path(r'planner_stats_per_day.json', PlannerStatsPerDayJSONView.as_view()),
    #path(r'planner_timeline_datatable', planner_timeline_datatable_view()),
]
