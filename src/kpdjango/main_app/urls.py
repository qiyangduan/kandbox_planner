"""simpleui_demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView


#from worker.views import  WorkerViewSet, hello_world
#from game import views as game_views
#from game.views import  LocalViewSet  as GameLocalViewSet

from rest_framework import routers
router = routers.DefaultRouter()
#router.register(r'workers', WorkerViewSet)
#router.register(r'games',  GameLocalViewSet)

admin.site.site_header = 'AI Planner World'                    # default: "Django Administration"
admin.site.index_title = 'AI Planner'                 # default: "Site administration"
admin.site.site_title = 'AI Planner by Qiyang Duan' # default: "Django site admin"



# from django.views.decorators.csrf import csrf_exempt

from django.views.generic import RedirectView
from django.conf.urls import url

urlpatterns = [ 
    url(r'doc/', include('django.contrib.admindocs.urls'), name='doc'),
    path('', admin.site.urls),

    # https://icons8.com/icons/set/timeline

    url(r'^favicon\.ico$',RedirectView.as_view(url='/static/timeline_icon.png')),
    path('api/', include(router.urls)),
    #path('api/hello', csrf_exempt (hello_world)),
    path("kpdata/", include("kpdata.urls")),
    url(r'^api-auth/', include('rest_framework.urls')),
]
 
