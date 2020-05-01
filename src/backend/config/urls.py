from django.urls import path
from django.contrib import admin
from django.contrib.auth import logout

from django.conf.urls import include

from config.api import api

from django.conf import settings

urlpatterns = [
    path(settings.ADMIN_URL , admin.site.urls, name='admin'), # 'admin/'
    path('logout/', logout, {'next_page': '/'}, name='logout'),
    
    path('api/', include(api.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path("kpdata/", include("kpdata.urls")),    
]
